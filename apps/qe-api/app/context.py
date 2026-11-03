"""The context analysis as the workbench serves it, and the entries engineers review and export."""

import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.config import get_settings
from app.db import Db, Tx, get_engine
from qe.engines import audit
from qe.engines.agents.gateway import ReplayGateway
from qe.engines.analysis import RECORDINGS, Sources, analyse

router = APIRouter(prefix="/api")

REVIEWERS = {"engineer", "qe_lead"}
EXPORT_FORMAT = "test-assurance-context/1"


@lru_cache(maxsize=1)
def analysis() -> dict[str, Any]:
    """Recorded agent results replayed over today's files. Nothing here changes while the API runs."""
    settings = get_settings()
    src = Sources.at(Path(settings.estate_root).parent, Path(settings.history_repo), settings.gate_percent)
    return analyse(src, ReplayGateway(RECORDINGS))


def _agent_fields(part: dict[str, Any]) -> dict[str, Any]:
    return {"source": part["source"], "model": part["model"], "input_hash": part["input_hash"]}


def proposed_entries(result: dict[str, Any]) -> list[dict[str, Any]]:
    entries = []
    facts = {entry["rule"]: entry for entry in result["risk_ranking"]}
    for rule, part in result["risk_cards"].items():
        if part["status"] == "ok":
            entries.append(
                {
                    "entry_id": f"RISK-{rule}",
                    "kind": "risk_card",
                    "rule": rule,
                    "title": part["content"]["headline"],
                    "content": {"card": part["content"], "facts": facts[rule]},
                    "provenance": "ai_analysis",
                    **_agent_fields(part),
                }
            )
    hidden = result["hidden_rules"]
    if hidden["status"] == "ok":
        for number, rule in enumerate(hidden["content"]["rules"], start=1):
            entries.append(
                {
                    "entry_id": f"HIDDEN-{number:02d}",
                    "kind": "hidden_rule",
                    "rule": rule["related_rule"],
                    "title": rule["title"],
                    "content": rule,
                    "provenance": "ai_analysis",
                    **_agent_fields(hidden),
                }
            )
    for item in result["dead_code"]:
        entries.append(
            {
                "entry_id": f"DEAD-{item['name']}",
                "kind": "dead_code",
                "rule": None,
                "title": f"{item['name']} cannot be reached",
                "content": item,
                "provenance": "verified_by_code",
                "source": "reachability",
                "model": None,
                "input_hash": None,
            }
        )
    return entries


def sync_entries(db: Connection, result: dict[str, Any]) -> None:
    """Adds new entries and refreshes ones nobody has reviewed. A reviewed entry never changes."""
    for entry in proposed_entries(result):
        db.execute(
            text("""
                INSERT INTO qe.context_entry
                    (entry_id, kind, rule, title, content, provenance, source, model, input_hash)
                VALUES (:entry_id, :kind, :rule, :title, CAST(:content AS jsonb), :provenance, :source,
                        :model, :input_hash)
                ON CONFLICT (entry_id) DO UPDATE
                SET kind = excluded.kind, rule = excluded.rule, title = excluded.title,
                    content = excluded.content, provenance = excluded.provenance,
                    source = excluded.source, model = excluded.model, input_hash = excluded.input_hash
                WHERE qe.context_entry.status = 'proposed'
            """),
            {**entry, "content": json.dumps(entry["content"])},
        )


def warm() -> None:
    result = analysis()
    with get_engine().begin() as db:
        sync_entries(db, result)


def _entries(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT e.entry_id, e.kind, e.rule, e.title, e.content, e.provenance, e.source, e.model,
                   e.status, p.name AS reviewed_by, e.reviewed_at, e.review_note
            FROM qe.context_entry e LEFT JOIN qe.person p ON p.person_key = e.reviewed_by
            ORDER BY CASE e.kind WHEN 'risk_card' THEN 0 WHEN 'hidden_rule' THEN 1 ELSE 2 END, e.entry_id
        """)
    ).mappings()
    return [dict(row) for row in rows]


def _agent_summary(part: dict[str, Any]) -> dict[str, Any]:
    return {key: part.get(key) for key in ("status", "source", "model", "duration_ms")}


@router.get("/coverage")
def coverage() -> dict[str, Any]:
    result = analysis()
    return {
        "rules": result["coverage"],
        "summary": result["summary"],
        "gate_percent": result["gate_percent"],
        "case_mapping": _agent_summary(result["case_mapping"]),
        "defect_mapping": _agent_summary(result["defect_mapping"]),
    }


@router.get("/context")
def context(db: Db) -> dict[str, Any]:
    result = analysis()
    return {
        "risk_ranking": result["risk_ranking"],
        "clusters": result["clusters"],
        "entries": _entries(db),
        "agents": {
            "defect_clusterer": _agent_summary(result["defect_mapping"]),
            "hidden_rule_finder": _agent_summary(result["hidden_rules"]),
            "risk_analyst": {rule: _agent_summary(part) for rule, part in result["risk_cards"].items()},
        },
    }


class Review(BaseModel):
    person_key: str
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=500)


@router.post("/context/{entry_id}/review")
def review(entry_id: str, body: Review, db: Tx) -> dict[str, Any]:
    person = db.execute(
        text("SELECT name, role FROM qe.person WHERE person_key = :key"), {"key": body.person_key}
    ).one_or_none()
    if person is None or person.role not in REVIEWERS:
        raise HTTPException(403, "Only an engineer or the quality engineering lead can review context.")
    if body.decision == "rejected" and not body.note.strip():
        raise HTTPException(422, "Say why the entry is rejected.")
    now = datetime.now(UTC)
    updated = db.execute(
        text("""
            UPDATE qe.context_entry
            SET status = :status, reviewed_by = :person, reviewed_at = :at, review_note = :note
            WHERE entry_id = :entry_id AND status = 'proposed'
            RETURNING entry_id
        """),
        {
            "status": body.decision,
            "person": body.person_key,
            "at": now,
            "note": body.note.strip() or None,
            "entry_id": entry_id,
        },
    ).one_or_none()
    if updated is None:
        raise HTTPException(409, "This entry has already been reviewed, or does not exist.")
    audit.record(
        db, now, person.name, person.role, f"context_{body.decision}", entry_id, {"note": body.note.strip()}
    )
    return {"entry_id": entry_id, "status": body.decision}


@router.get("/context/export")
def export(db: Db) -> dict[str, Any]:
    approved = [entry for entry in _entries(db) if entry["status"] == "approved"]
    return {
        "format": EXPORT_FORMAT,
        "area": "Project billing",
        "exported_at": datetime.now(UTC).isoformat(),
        "entries": [
            {
                "id": entry["entry_id"],
                "kind": entry["kind"],
                "rule": entry["rule"],
                "title": entry["title"],
                "content": entry["content"],
                "provenance": entry["provenance"],
                "approved_by": entry["reviewed_by"],
                "approved_at": entry["reviewed_at"].isoformat(),
                "note": entry["review_note"],
            }
            for entry in approved
        ],
    }
