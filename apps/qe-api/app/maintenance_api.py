"""Flaky tests and selector repairs: the evidence, the proposed changes, their proof and their review."""

import json
from collections import Counter
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.db import Db, Tx
from qe.engines import audit, flaky, maintenance
from qe.engines.estate import Estate

router = APIRouter(prefix="/api")

QE_ROOT = maintenance.QE_ROOT
ESTATE = Estate(QE_ROOT / "estate")
BASELINE = QE_ROOT / "lab" / "results" / "baseline-20.jsonl"
REVIEWERS = {"engineer", "qe_lead"}


def _runs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _failures(runs: list[dict[str, Any]]) -> Counter[str]:
    return Counter(t["title"] for run in runs for t in run["tests"] if t["status"] != "passed")


def _reviews(db: Connection) -> dict[str, dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT r.change_id, r.status, p.name AS reviewed_by, r.reviewed_at, r.note
            FROM qe.change_review r JOIN qe.person p ON p.person_key = r.reviewed_by
        """)
    ).mappings()
    return {row["change_id"]: dict(row) for row in rows}


@lru_cache(maxsize=1)
def _triage(modified: float) -> list[dict[str, Any]]:
    """Read once per version of the runs file; the file only changes when the lab runs again."""
    return flaky.triage(ESTATE, BASELINE)


@router.get("/flaky")
def flaky_tests(db: Db) -> dict[str, Any]:
    before = _runs(BASELINE)
    after = _runs(maintenance.RESULTS / "flaky-fix-runs.jsonl")
    record = maintenance.load("flaky") or {"diagnoses": []}
    failed_after = _failures(after)
    reviews = _reviews(db)
    return {
        "runs_before": len(before),
        "runs_after": len(after),
        "suite_after": len(after[0]["tests"]) if after else 0,
        "failures_after": sum(failed_after.values()),
        "tests": [
            {
                **entry,
                "after": {"failed": failed_after[entry["test"]["title"]], "runs": len(after)}
                if after
                else None,
                "change_id": f"FLAKY-{entry['test']['rule']}",
                "review": reviews.get(f"FLAKY-{entry['test']['rule']}"),
            }
            for entry in record["diagnoses"]
        ],
        "triage": _triage(BASELINE.stat().st_mtime) if before else [],
    }


@router.get("/maintenance")
def maintenance_measure(db: Db) -> dict[str, Any]:
    record = maintenance.load("release-4.9-repair")
    if record is None:
        return {"repair": None}
    before = _runs(maintenance.RESULTS / "release-4.9-before.jsonl")
    after = _runs(maintenance.RESULTS / "release-4.9-after.jsonl")
    detect = sum(run.get("seconds", 0) for run in before)
    verify = sum(run.get("seconds", 0) for run in after)
    agent = (record["agent"]["duration_ms"] or 0) / 1000
    return {
        "release": record["release"],
        "failures": [{"title": f["title"], "error": f["error"]} for f in record["failures"]],
        "repair": record["repair"],
        "agent": record["agent"],
        "after": {
            "tests": len(after[0]["tests"]) if after else 0,
            "failed": sum(_failures(after).values()),
        },
        "timing": {
            "detect_seconds": round(detect, 1),
            "repair_seconds": round(agent, 1),
            "verify_seconds": round(verify, 1),
            "machine_seconds": round(detect + agent + verify, 1),
        },
        "change_id": "REPAIR-release-4.9",
        "review": _reviews(db).get("REPAIR-release-4.9"),
    }


class ChangeReview(BaseModel):
    person_key: str
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=500)


@router.post("/changes/{change_id}/review")
def review_change(change_id: str, body: ChangeReview, db: Tx) -> dict[str, Any]:

    if not change_id.startswith(("FLAKY-", "REPAIR-")):
        raise HTTPException(404, "No such change.")
    person = db.execute(
        text("SELECT name, role FROM qe.person WHERE person_key = :key"), {"key": body.person_key}
    ).one_or_none()
    if person is None or person.role not in REVIEWERS:
        raise HTTPException(
            403, "Only an engineer or the quality engineering lead can approve a change to tests."
        )
    if body.decision == "rejected" and not body.note.strip():
        raise HTTPException(422, "Say why the change is rejected.")
    now = datetime.now(UTC)
    inserted = db.execute(
        text("""
            INSERT INTO qe.change_review (change_id, kind, status, reviewed_by, reviewed_at, note)
            VALUES (:id, :kind, :status, :person, :at, :note)
            ON CONFLICT (change_id) DO NOTHING
            RETURNING change_id
        """),
        {
            "id": change_id,
            "kind": "flaky_fix" if change_id.startswith("FLAKY-") else "selector_repair",
            "status": body.decision,
            "person": body.person_key,
            "at": now,
            "note": body.note.strip() or None,
        },
    ).one_or_none()
    if inserted is None:
        raise HTTPException(409, "This change has already been reviewed.")
    audit.record(db, now, person.name, person.role, f"change_{body.decision}", change_id, {"note": body.note})
    return {"change_id": change_id, "status": body.decision}


def warm() -> None:
    if BASELINE.exists():
        _triage(BASELINE.stat().st_mtime)
