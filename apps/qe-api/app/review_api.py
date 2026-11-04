"""The pull request screen: every test and fix with its evidence, the engineer's decisions and the merge."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.config import get_settings
from app.db import Db, Tx
from qe.engines import audit, review

router = APIRouter(prefix="/api")

# Engineers accept tests. The quality engineering lead chose the batch, so does not approve it too.
APPROVER = "engineer"


def _repo() -> Path:
    return Path(get_settings().history_repo)


def _decisions(db: Connection) -> dict[str, dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT r.item_id, r.decision, p.name AS reviewed_by, r.reviewed_at, r.note
            FROM qe.pr_review r JOIN qe.person p ON p.person_key = r.reviewed_by
        """)
    ).mappings()
    return {row["item_id"]: dict(row) for row in rows}


def _merge(db: Connection) -> dict[str, Any] | None:
    row = (
        db.execute(
            text("""
                SELECT m.pr_id, p.name AS merged_by, m.merged_at, m.branch, m.branch_commit,
                       m.merge_commit, m.items
                FROM qe.pr_merge m JOIN qe.person p ON p.person_key = m.merged_by WHERE m.pr_id = :pr
            """),
            {"pr": review.PR_ID},
        )
        .mappings()
        .one_or_none()
    )
    return dict(row) if row else None


@router.get("/review")
def pull_request(db: Db) -> dict[str, Any]:
    decisions = _decisions(db)
    merged = _merge(db)
    files = review.changed_files(_repo()) if merged is None else []
    entries = review.items()
    return {
        "id": review.PR_ID,
        "branch": review.BRANCH,
        "title": "Add proven billing tests and fix two flaky tests",
        "author": review.AGENT_AUTHOR[0],
        "files": files,
        "release_controls_unchanged": review.release_controls_unchanged(files) if files else True,
        "pipeline_file": review.PIPELINE,
        "items": [{**item, "decision": decisions.get(item["item_id"])} for item in entries],
        "merged": merged,
    }


class Decision(BaseModel):
    person_key: str
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=500)


def _person(db: Connection, key: str) -> Any:
    person = db.execute(
        text("SELECT name, role FROM qe.person WHERE person_key = :key"), {"key": key}
    ).one_or_none()
    if person is None or person.role != APPROVER:
        raise HTTPException(403, "Only an engineer can accept tests into the suite.")
    return person


@router.post("/review/items/{item_id}")
def decide(item_id: str, body: Decision, db: Tx) -> dict[str, Any]:
    person = _person(db, body.person_key)
    if _merge(db) is not None:
        raise HTTPException(409, "The pull request has been merged.")
    if item_id not in {item["item_id"] for item in review.items()}:
        raise HTTPException(404, "No such item in the pull request.")
    if body.decision == "rejected" and not body.note.strip():
        raise HTTPException(422, "Say why the item is rejected.")
    now = datetime.now(UTC)
    db.execute(
        text("""
            INSERT INTO qe.pr_review (item_id, decision, reviewed_by, reviewed_at, note)
            VALUES (:id, :decision, :person, :at, :note)
            ON CONFLICT (item_id) DO UPDATE
            SET decision = excluded.decision, reviewed_by = excluded.reviewed_by,
                reviewed_at = excluded.reviewed_at, note = excluded.note
        """),
        {
            "id": item_id,
            "decision": body.decision,
            "person": body.person_key,
            "at": now,
            "note": body.note or None,
        },
    )
    audit.record(db, now, person.name, person.role, f"pr_item_{body.decision}", item_id, {"note": body.note})
    return {"item_id": item_id, "decision": body.decision}


class MergeRequest(BaseModel):
    person_key: str


@router.post("/review/merge")
def merge(body: MergeRequest, db: Tx) -> dict[str, Any]:
    person = _person(db, body.person_key)
    if _merge(db) is not None:
        raise HTTPException(409, "The pull request has already been merged.")
    decisions = _decisions(db)
    entries = review.items()
    undecided = [item["item_id"] for item in entries if item["item_id"] not in decisions]
    if undecided:
        raise HTTPException(422, f"Decide on every item first: {', '.join(undecided)}.")
    approved = [i for i, d in decisions.items() if d["decision"] == "approved"]
    if not approved:
        raise HTTPException(422, "Nothing is approved, so there is nothing to merge.")
    if not review.release_controls_unchanged(review.changed_files(_repo())):
        raise HTTPException(409, "The pull request changes more than the test suite.")
    reviewer = (person.name, review.REVIEWER_EMAIL.format(key=body.person_key))
    result = review.merge(_repo(), approved, reviewer)
    now = datetime.now(UTC)
    db.execute(
        text("""
            INSERT INTO qe.pr_merge (pr_id, merged_by, merged_at, branch, branch_commit, merge_commit, items)
            VALUES (:pr, :person, :at, :branch, :branch_commit, :merge_commit, CAST(:items AS jsonb))
        """),
        {"pr": review.PR_ID, "person": body.person_key, "at": now, **result, "items": json.dumps(approved)},
    )
    audit.record(db, now, person.name, person.role, "pr_merged", review.PR_ID, {**result, "items": approved})
    return {**result, "items": approved}


def warm() -> None:
    """Reads the attempts, the lab results and the repository once, so the first screen is quick."""
    review.items()
    review.changed_files(_repo())
