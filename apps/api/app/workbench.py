"""Read models for the journey screens, plus sign-off and the scorecard."""

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.decisions import AnswerQuestion, AskCustomer, PersonaRole, Tx, answer, ask
from app.storage import get_storage
from engines.decision import audit
from engines.decision.policy import CONSULTANT, CUSTOMER, PERSONAS
from engines.decision.seed import seed_decisions
from engines.scoring.score import score
from engines.signoff.pack import SCOPE, build_pack, gate
from engines.validation import checks
from engines.validation.runner import run_checks

router = APIRouter(prefix="/api")


def _rows(db: Connection, sql: str, **params: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in db.execute(text(sql), params).mappings()]


@router.get("/estate")
def estate(db: Tx) -> dict[str, Any]:
    volumes = (
        db.execute(
            text("""
                SELECT (SELECT count(*) FROM cr_source.account) AS accounts,
                       (SELECT count(*) FROM cr_source.dimension_value) AS dimension_values,
                       (SELECT count(*) FROM cr_source.ar_open_item) AS receivables,
                       (SELECT count(*) FROM cr_source.ap_open_item) AS payables,
                       (SELECT count(*) FROM cr_source.project WHERE status = 'open') AS active_projects,
                       (SELECT count(*) FROM studio.usage_event) AS usage_events
            """)
        )
        .mappings()
        .one()
    )
    j2x: dict[str, Any] = db.execute(
        text("SELECT content FROM studio.reference_document WHERE document_key = 'j2x_assessment'")
    ).scalar_one()
    return {
        "types": _rows(
            db,
            """
            SELECT item_type, count(*) AS count, count(*) FILTER (WHERE j2x_explained) AS j2x_explained,
                   count(*) FILTER (WHERE direct_db_write) AS direct_db_writes
            FROM studio.estate_item GROUP BY 1 ORDER BY 1
            """,
        ),
        "integrations": _rows(
            db,
            """
            SELECT item_id, name, subtype AS direction, definition ->> 'external_system' AS system
            FROM studio.estate_item WHERE item_type = 'INT' ORDER BY item_id
            """,
        ),
        "volumes": dict(volumes),
        "j2x": j2x,
    }


@router.get("/reports/overview")
def reports_overview(db: Tx) -> dict[str, Any]:
    rows = _rows(
        db,
        """
        SELECT e.item_id, e.name, e.usage_12m, e.frequency, d.outcome, d.action, d.status, p.state, p.flags
        FROM studio.estate_item e
        JOIN studio.decision d USING (item_id)
        JOIN studio.proposal p USING (item_id)
        WHERE e.item_type = 'RP'
        ORDER BY e.item_id
        """,
    )
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["action"] == "merge_survivor":
            groups.setdefault(row["item_id"], {"members": []}).update(lead=row)
    for row in rows:
        action = row["action"] or ""
        if action.startswith("merge_into:"):
            groups.setdefault(action.split(":")[1], {"members": []})["members"].append(row)

    def count(condition: Any) -> int:
        return sum(1 for row in rows if condition(row))

    merged = sum(len(group["members"]) + 1 for group in groups.values())
    # Held reports stay out of every count until the customer answers, so the five groups add to 148.
    rebuild = [r for r in rows if r["action"] == "rebuild"]
    return {
        "total": len(rows),
        "retire": count(lambda r: r["outcome"] == "retire"),
        "merged": merged,
        "merged_into": len(groups),
        "standard": count(lambda r: r["outcome"] == "replace_standard"),
        "rebuild": len(rebuild),
        "held": [r for r in rows if r["state"] == "held"],
        "groups": sorted(groups.values(), key=lambda g: -(len(g["members"]))),
        "rebuild_items": rebuild,
    }


@router.post("/reports/{report_id}/parity")
def report_parity(report_id: str, db: Tx) -> dict[str, Any]:
    result = checks.report_parity(db)
    report = next((r for r in result["summary"]["reports"] if r["report"] == report_id), None)
    if report is None:
        raise HTTPException(status_code=404, detail="No rebuild exists for this report.")
    return {**report, "status": result["status"]}


@router.get("/workflows")
def workflows(db: Tx) -> dict[str, Any]:
    pack = db.execute(
        text("SELECT content, source FROM studio.artefact WHERE kind = 'workflow_pack' LIMIT 1")
    ).first()
    return {
        "variants": _rows(
            db,
            """
            SELECT e.item_id, e.name, e.subtype, e.usage_12m, e.definition, d.outcome, d.action, d.status,
                   p.reason, p.flags,
                   (SELECT array_agg(DISTINCT u.entity_code) FROM studio.usage_event u
                    WHERE u.item_id = e.item_id) AS entities
            FROM studio.estate_item e
            JOIN studio.decision d USING (item_id)
            JOIN studio.proposal p USING (item_id)
            WHERE e.item_type = 'WF'
            ORDER BY e.usage_12m DESC
            """,
        ),
        "pack": pack.content if pack else None,
        "pack_source": pack.source if pack else None,
    }


def _latest_pack(db: Connection) -> dict[str, Any] | None:
    row = (
        db.execute(text("SELECT * FROM studio.signoff_pack ORDER BY pack_id DESC LIMIT 1")).mappings().first()
    )
    return dict(row) if row else None


def _audit_head(db: Connection) -> str:
    return db.execute(text("SELECT hash FROM studio.audit_event ORDER BY seq DESC LIMIT 1")).scalar_one()


def _signoff_state(db: Connection) -> dict[str, Any]:
    pack = _latest_pack(db)
    conditions = gate(db)
    current = pack is not None and pack["audit_head"] == _audit_head(db)
    return {
        "scope": SCOPE,
        "conditions": conditions,
        "ready_to_generate": all(c["passed"] for c in conditions),
        "pack": pack,
        "pack_current": current or bool(pack and pack["signed_at"]),
        "open_questions": _rows(
            db,
            """
            SELECT q.question_id, q.item_id, e.name, q.question, q.options
            FROM studio.customer_question q JOIN studio.estate_item e USING (item_id)
            WHERE q.status = 'open' ORDER BY q.asked_at, q.question_id
            """,
        ),
    }


@router.get("/signoff")
def signoff(db: Tx) -> dict[str, Any]:
    return _signoff_state(db)


@router.post("/signoff/generate")
def generate_pack(db: Tx, role: PersonaRole) -> dict[str, Any]:
    if role != "consultant":
        raise HTTPException(status_code=403, detail="The consultant generates the pack.")
    state = _signoff_state(db)
    if not state["ready_to_generate"]:
        raise HTTPException(status_code=409, detail="The sign-off conditions are not all met.")
    run_id: int = db.execute(text("SELECT max(run_id) FROM studio.check_run")).scalar_one()
    now = datetime.now(UTC)
    audit.record(db, now, PERSONAS[role], role, "generated_pack", "PACK", {"run_id": run_id})
    built = build_pack(db, run_id)
    pack_id: int = db.execute(
        text("""
            INSERT INTO studio.signoff_pack
                (generated_at, generated_by, run_id, audit_head, manifest_hash, summary)
            VALUES (:at, :by, :run_id, :audit_head, :manifest_hash, CAST(:summary AS jsonb))
            RETURNING pack_id
        """),
        {
            "at": now,
            "by": PERSONAS[role],
            "run_id": run_id,
            "audit_head": built["audit_head"],
            "manifest_hash": built["manifest_hash"],
            "summary": json.dumps(built["summary"]),
        },
    ).scalar_one()
    storage = get_storage()
    storage.put(f"packs/{pack_id}/signoff_pack.pdf", built["pdf"])
    storage.put(f"packs/{pack_id}/signoff_pack.zip", built["zip"])
    return _signoff_state(db)


@router.post("/signoff/sign")
def sign_pack(db: Tx, role: PersonaRole) -> dict[str, Any]:
    if role != CUSTOMER:
        raise HTTPException(status_code=403, detail="Only the customer can sign.")
    state = _signoff_state(db)
    pack = state["pack"]
    if pack is None or not state["pack_current"]:
        raise HTTPException(status_code=409, detail="Generate a current pack first.")
    if pack["signed_at"]:
        raise HTTPException(status_code=409, detail="This pack is already signed.")
    now = datetime.now(UTC)
    db.execute(
        text("UPDATE studio.signoff_pack SET signed_by = :by, signed_at = :at WHERE pack_id = :pack_id"),
        {"by": PERSONAS[role], "at": now, "pack_id": pack["pack_id"]},
    )
    audit.record(
        db, now, PERSONAS[role], role, "signed_pack", "PACK", {"manifest_hash": pack["manifest_hash"]}
    )
    return _signoff_state(db)


@router.get("/signoff/{pack_id}/{file_name}")
def download_pack(pack_id: int, file_name: str) -> Response:
    media = {"signoff_pack.pdf": "application/pdf", "signoff_pack.zip": "application/zip"}.get(file_name)
    if media is None:
        raise HTTPException(status_code=404, detail="Unknown file")
    try:
        content = get_storage().get(f"packs/{pack_id}/{file_name}")
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Pack not found") from error
    disposition = "inline" if file_name.endswith(".pdf") else "attachment"
    return Response(
        content, media_type=media, headers={"Content-Disposition": f"{disposition}; filename={file_name}"}
    )


class Timing(BaseModel):
    stage: str = Field(max_length=30)
    seconds: int = Field(ge=1, le=600)


@router.post("/timing")
def record_timing(body: Timing, db: Tx, role: PersonaRole) -> dict[str, str]:
    db.execute(
        text("""
            INSERT INTO studio.timing_event (stage, role, seconds, recorded_at)
            VALUES (:stage, :role, :seconds, :at)
        """),
        {"stage": body.stage, "role": role, "seconds": body.seconds, "at": datetime.now(UTC)},
    )
    return {"status": "ok"}


SCENE_ANSWERS = {
    "CC-014": "15% (as the policy says)",
    "RP-058": "Retire it",
    "RP-112": "Keep it",
    "WF-006": "Retire it",
    "CC-037": "The finance systems lead can explain it",
}


@router.post("/workspace/prepare/{scene}")
def prepare_scene(scene: int, db: Tx) -> dict[str, str]:
    """Rebuilds the state a scene expects, so the presenter can resume anywhere."""
    if not 0 <= scene <= 8:
        raise HTTPException(status_code=404, detail="Scenes run from 0 to 8.")
    seed_decisions(db)
    if scene >= 7:
        conflict: dict[str, Any] = db.execute(
            text("SELECT conflict FROM studio.agent_signal WHERE item_id = 'CC-014'")
        ).scalar_one()
        ask("CC-014", AskCustomer(question=conflict["question"], options=conflict["options"]), db, CONSULTANT)
        for item_id, text_answer in SCENE_ANSWERS.items():
            answer(item_id, AnswerQuestion(answer=text_answer), db, CUSTOMER)
        run_checks(db)
    if scene == 8:
        generate_pack(db, CONSULTANT)
        sign_pack(db, CUSTOMER)
    return {"status": "ok"}


STAGE_GROUPS = {
    "Decision": ["decisions"],
    "Technical execution": ["code", "reports", "workflows"],
    "Validation": ["reconcile"],
    "Customer acceptance": ["signoff"],
}


@router.get("/scorecard")
def scorecard(db: Tx) -> dict[str, Any]:
    result = score(db)
    planted = _rows(db, "SELECT issue_id, issue_type, planted, scene FROM answer_key.planted_issue")
    planted.sort(key=lambda row: int(row["issue_id"][1:]))
    timing = {
        row["stage"]: row
        for row in _rows(
            db,
            """
            SELECT stage, sum(seconds) AS seconds,
                   sum(seconds) FILTER (WHERE role = 'consultant') AS consultant_seconds
            FROM studio.timing_event GROUP BY 1
            """,
        )
    }
    stages = [
        {
            "stage": label,
            "seconds": sum(int(timing.get(key, {}).get("seconds") or 0) for key in keys),
            "consultant_seconds": sum(
                int(timing.get(key, {}).get("consultant_seconds") or 0) for key in keys
            ),
        }
        for label, keys in STAGE_GROUPS.items()
    ]
    run = (
        db.execute(
            text("""
                SELECT run_id, extract(epoch FROM finished_at - started_at) AS seconds, result_hash
                FROM studio.check_run ORDER BY run_id DESC LIMIT 1
            """)
        )
        .mappings()
        .first()
    )
    results = (
        _rows(db, "SELECT check_id, status FROM studio.check_result WHERE run_id = :r", r=run["run_id"])
        if run
        else []
    )
    # A rebuilt item that fails its own tests on the first run is a defect.
    first_run = (
        _rows(
            db,
            """
            SELECT check_id, status FROM studio.check_result
            WHERE check_id IN ('R7', 'R8') AND status <> 'waiting'
              AND run_id = (SELECT min(run_id) FROM studio.check_result c
                            WHERE c.check_id = check_result.check_id AND c.status <> 'waiting')
            """,
        )
        if run
        else []
    )
    artefacts = _rows(
        db, "SELECT source, count(*) AS count, sum(duration_ms) AS ms FROM studio.artefact GROUP BY 1"
    )
    pack = _latest_pack(db)
    conditions = gate(db)
    return {
        "issues": [{**row, "found": result["issues"]["detail"][row["issue_id"]]} for row in planted],
        "found": result["issues"]["found"],
        "planted": result["issues"]["planted"],
        "false_items": result["false_items"],
        "decision_quality": result["decision_quality"],
        "passed": result["passed"],
        "stages": stages,
        "reconciliation": {
            "run": bool(run),
            "seconds": float(run["seconds"]) if run else None,
            "passed": sum(r["status"] == "pass" for r in results),
            "total": len(results),
        },
        "defects": {"tested": len(first_run), "failed": sum(r["status"] == "fail" for r in first_run)},
        "artefacts": artefacts,
        "signoff": {
            "generated": pack is not None,
            "signed": bool(pack and pack["signed_at"]),
            "conditions": conditions,
        },
    }
