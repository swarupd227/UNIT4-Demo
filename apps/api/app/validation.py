import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Connection, text

from app.config import get_settings
from app.decisions import PersonaRole, Tx
from engines.agents.gateway import ClaudeGateway, LiveAgentError, LLMGateway
from engines.agents.pipeline import request_for, run_live
from engines.decision import audit
from engines.decision.policy import CONSULTANT, PERSONAS
from engines.ontology.ontology import concepts
from engines.ontology.ontology import version as ontology_version
from engines.scoring.score import score
from engines.validation.runner import run_checks

router = APIRouter(prefix="/api")


def _latest_run_id(db: Connection) -> int | None:
    return db.execute(text("SELECT max(run_id) FROM studio.check_run")).scalar()


def _run_report(db: Connection, run_id: int) -> dict[str, Any]:
    params = {"run_id": run_id}
    run = db.execute(text("SELECT * FROM studio.check_run WHERE run_id = :run_id"), params).mappings().one()
    checks = db.execute(
        text("SELECT * FROM studio.check_result WHERE run_id = :run_id ORDER BY check_id"), params
    ).mappings()
    exceptions = db.execute(
        text("""
            SELECT e.*, r.approved_by, r.approved_at
            FROM studio.exception e LEFT JOIN studio.exception_resolution r USING (code, title)
            WHERE e.run_id = :run_id ORDER BY e.exception_id
        """),
        params,
    ).mappings()
    return {**run, "checks": [dict(c) for c in checks], "exceptions": [dict(e) for e in exceptions]}


@router.post("/reconciliation/run")
def run_reconciliation(db: Tx) -> dict[str, Any]:
    return _run_report(db, run_checks(db))


@router.get("/reconciliation/latest")
def latest_reconciliation(db: Tx) -> dict[str, Any] | None:
    run_id = _latest_run_id(db)
    return _run_report(db, run_id) if run_id is not None else None


@router.post("/reconciliation/exceptions/{exception_id}/approve")
def approve_exception(exception_id: str, db: Tx, role: PersonaRole) -> dict[str, Any]:
    """Approves the proposed action. The fix lands in the next trial load, so the check still fails."""
    run_id = _latest_run_id(db)
    if run_id is None:
        raise HTTPException(status_code=404, detail="Reconciliation has not run yet.")
    row = db.execute(
        text("""
            SELECT e.code, e.title, e.proposed_action, e.approver_role, r.approved_at
            FROM studio.exception e LEFT JOIN studio.exception_resolution r USING (code, title)
            WHERE e.run_id = :run_id AND e.exception_id = :exception_id
        """),
        {"run_id": run_id, "exception_id": exception_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="This exception is not in the latest run.")
    if role != row.approver_role:
        raise HTTPException(status_code=403, detail=f"{PERSONAS[row.approver_role]} approves this exception.")
    if row.approved_at:
        raise HTTPException(status_code=409, detail="This exception is already approved.")
    now = datetime.now(UTC)
    db.execute(
        text("""
            INSERT INTO studio.exception_resolution (code, title, approved_by, approved_role, approved_at)
            VALUES (:code, :title, :by, :role, :at)
        """),
        {"code": row.code, "title": row.title, "by": PERSONAS[role], "role": role, "at": now},
    )
    audit.record(
        db,
        now,
        PERSONAS[role],
        role,
        "approved_exception",
        exception_id,
        {"title": row.title, "proposed_action": row.proposed_action},
    )
    return _run_report(db, run_id)


@router.get("/reconciliation/{check_id}/differences")
def check_differences(check_id: str, db: Tx, limit: int = Query(200, le=1000)) -> list[dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT row_number, row_key, source_value, target_value, difference, detail
            FROM studio.check_difference
            WHERE run_id = (SELECT max(run_id) FROM studio.check_run) AND check_id = :check_id
            ORDER BY row_number LIMIT :limit
        """),
        {"check_id": check_id, "limit": limit},
    ).mappings()
    return [dict(row) for row in rows]


@router.get("/artefacts/{item_id}")
def artefacts(item_id: str, db: Tx) -> list[dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT kind, content, source, model, duration_ms, prompt_version, input_tokens, output_tokens
            FROM studio.artefact WHERE item_id = :item_id ORDER BY kind
        """),
        {"item_id": item_id},
    ).mappings()
    return [dict(row) for row in rows]


def _live_gateway() -> LLMGateway:
    return ClaudeGateway(get_settings().llm_model)


def _live_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


@router.get("/ontology")
def ontology() -> dict[str, Any]:
    return {
        "version": ontology_version(),
        "concepts": {
            concept_id: {"label": concept["label"], "meaning": concept["meaning"]}
            for concept_id, concept in concepts().items()
        },
    }


@router.get("/agents/status")
def agent_status() -> dict[str, Any]:
    return {"live": _live_available(), "model": get_settings().llm_model}


@router.post("/agents/{agent}/{subject}/run")
def run_agent(agent: str, subject: str, db: Tx, role: PersonaRole) -> dict[str, Any]:
    """Runs one agent live. A person still reviews the result, and a reset restores the cached one."""
    if role != CONSULTANT:
        raise HTTPException(status_code=403, detail="The consultant runs the agents.")
    if not _live_available():
        raise HTTPException(status_code=409, detail="Live agents are not set up on this environment.")
    found = request_for(db, agent, subject)
    if found is None:
        raise HTTPException(status_code=404, detail="This agent does not cover this item.")
    spec, request = found
    try:
        result = run_live(db, spec, request, _live_gateway())
    except LiveAgentError as error:
        raise HTTPException(
            status_code=502, detail=f"{error} The previous result is still in place."
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="The result failed its checks, so it was rejected. The previous result is still in place.",
        ) from error
    audit.record(
        db,
        datetime.now(UTC),
        PERSONAS[role],
        role,
        "ran_agent",
        subject,
        {"agent": agent, "model": result.model, "input_hash": request.input_hash},
    )
    return {
        "source": result.source,
        "model": result.model,
        "duration_ms": result.duration_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


@router.get("/score")
def get_score(db: Tx) -> dict[str, Any]:
    return score(db)
