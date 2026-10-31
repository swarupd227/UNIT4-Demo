import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.db import get_engine
from engines.decision import audit
from engines.decision.policy import (
    CUSTOMER,
    OUTCOMES,
    PERSONAS,
    allowed_actions,
    required_roles,
    status_for,
)
from engines.decision.seed import seed_decisions

router = APIRouter(prefix="/api")

Role = Literal["consultant", "customer", "unit4_technical", "unit4_product"]


def get_role(x_studio_persona: Annotated[Role, Header()] = "consultant") -> str:
    return x_studio_persona


def get_transaction():
    with get_engine().begin() as connection:
        yield connection


Tx = Annotated[Connection, Depends(get_transaction)]
PersonaRole = Annotated[str, Depends(get_role)]

ROW_SQL = """
    SELECT e.item_id, e.item_type, e.name, e.subtype, e.module, e.frequency, e.usage_12m, e.last_used,
           e.owner, e.j2x_explained,
           d.outcome, d.action, d.status, d.conflict_open, d.edit_reason,
           p.outcome AS proposed_outcome, p.candidate_outcome, p.state, p.reason, p.confidence, p.flags,
           COALESCE(a.roles, '{}') AS approved_roles
    FROM studio.decision d
    JOIN studio.estate_item e USING (item_id)
    JOIN studio.proposal p USING (item_id)
    LEFT JOIN (SELECT item_id, array_agg(role ORDER BY decided_at) AS roles
               FROM studio.approval GROUP BY item_id) a USING (item_id)
"""


def _with_roles(row: Any) -> dict[str, Any]:
    result = dict(row)
    result["required_roles"] = required_roles(row["item_type"], row["outcome"])
    return result


@router.get("/decisions")
def list_decisions(db: Tx) -> list[dict[str, Any]]:
    rows = db.execute(text(f"{ROW_SQL} ORDER BY e.item_id")).mappings()
    return [_with_roles(row) for row in rows]


def _load(db: Connection, item_id: str, lock: bool = False) -> dict[str, Any]:
    sql = f"{ROW_SQL} WHERE d.item_id = :item_id"
    if lock:
        sql += " FOR UPDATE OF d"
    row = db.execute(text(sql), {"item_id": item_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return _with_roles(row)


def _open_question(db: Connection, item_id: str) -> dict[str, Any] | None:
    row = (
        db.execute(
            text("SELECT * FROM studio.customer_question WHERE item_id = :item_id AND status = 'open'"),
            {"item_id": item_id},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def _allowed(row: dict[str, Any], role: str):
    return allowed_actions(role, row["outcome"], row["required_roles"], row["approved_roles"], row["status"])


def _refresh_status(db: Connection, item_id: str, now: datetime) -> None:
    row = _load(db, item_id)
    status = status_for(
        row["required_roles"],
        row["approved_roles"],
        _open_question(db, item_id) is not None,
        row["conflict_open"],
    )
    db.execute(
        text("UPDATE studio.decision SET status = :status, updated_at = :now WHERE item_id = :item_id"),
        {"status": status, "now": now, "item_id": item_id},
    )


@router.get("/decisions/{item_id}")
def get_decision(item_id: str, db: Tx, role: PersonaRole) -> dict[str, Any]:
    row = _load(db, item_id)
    params = {"item_id": item_id}
    extra = (
        db.execute(
            text("""
            SELECT e.source_text, e.documented, e.definition, s.summary, s.conflict, s.action_note,
                   p.evidence, p.rule, p.engine_version, j.summary AS j2x_summary,
                   j.complexity AS j2x_complexity
            FROM studio.estate_item e
            JOIN studio.agent_signal s USING (item_id)
            JOIN studio.proposal p USING (item_id)
            LEFT JOIN studio.j2x_explanation j USING (item_id)
            WHERE e.item_id = :item_id
        """),
            params,
        )
        .mappings()
        .one()
    )
    usage = db.execute(
        text("""
            SELECT to_char(event_date, 'YYYY-MM') AS month, sum(event_count) AS count
            FROM studio.usage_event WHERE item_id = :item_id GROUP BY 1 ORDER BY 1
        """),
        params,
    ).mappings()
    approvals = db.execute(
        text(
            "SELECT role, person, decided_at FROM studio.approval "
            "WHERE item_id = :item_id ORDER BY decided_at"
        ),
        params,
    ).mappings()
    questions = db.execute(
        text("SELECT * FROM studio.customer_question WHERE item_id = :item_id ORDER BY asked_at"), params
    ).mappings()
    trail = db.execute(
        text("""
            SELECT seq, at, actor, role, action, detail, hash
            FROM studio.audit_event WHERE item_id = :item_id ORDER BY seq DESC
        """),
        params,
    ).mappings()
    allowed = _allowed(row, role)
    return {
        **row,
        **extra,
        "usage_by_month": [{"month": u["month"], "count": int(u["count"])} for u in usage],
        "approvals": [dict(a) for a in approvals],
        "questions": [dict(q) for q in questions],
        "audit": [dict(t) for t in trail],
        "allowed": {
            "accept": allowed.accept,
            "edit": allowed.edit,
            "ask": allowed.ask,
            "answer": allowed.answer,
            "reason": allowed.reason,
        },
    }


def _remember(
    db: Connection,
    row: dict[str, Any],
    outcome: str,
    review_status: str,
    person: str,
    at: datetime,
    reason: str | None,
) -> None:
    """Each decision becomes a precedent, so the next customer gets a better first proposal."""
    db.execute(
        text("""
            INSERT INTO studio.mapping_memory
                (item_id, pattern, outcome, review_status, decided_by, decided_at, reason)
            VALUES (:item_id, :pattern, :outcome, :review_status, :person, :at, :reason)
        """),
        {
            "item_id": row["item_id"],
            "pattern": row["name"],
            "outcome": outcome,
            "review_status": review_status,
            "person": person,
            "at": at,
            "reason": reason,
        },
    )


def _accept(db: Connection, item_id: str, role: str, now: datetime) -> None:
    row = _load(db, item_id, lock=True)
    if not _allowed(row, role).accept:
        raise HTTPException(status_code=403, detail=_allowed(row, role).reason or "Not allowed")
    db.execute(
        text("INSERT INTO studio.approval VALUES (:item_id, :role, :person, :at)"),
        {"item_id": item_id, "role": role, "person": PERSONAS[role], "at": now},
    )
    audit.record(db, now, PERSONAS[role], role, "accepted", item_id, {"outcome": row["outcome"]})
    _refresh_status(db, item_id, now)
    if _load(db, item_id)["status"] == "agreed":
        _remember(db, row, row["outcome"], "approved", PERSONAS[role], now, None)


@router.post("/decisions/{item_id}/accept")
def accept(item_id: str, db: Tx, role: PersonaRole) -> dict[str, str]:
    _accept(db, item_id, role, datetime.now(UTC))
    return {"status": "ok"}


class BulkAccept(BaseModel):
    item_ids: list[str] = Field(min_length=1, max_length=300)


@router.post("/decisions/bulk-accept")
def bulk_accept(body: BulkAccept, db: Tx, role: PersonaRole) -> dict[str, int]:
    """Skips what this role may not accept, rather than failing the whole batch."""
    now = datetime.now(UTC)
    accepted = 0
    for item_id in body.item_ids:
        if _allowed(_load(db, item_id, lock=True), role).accept:
            _accept(db, item_id, role, now)
            accepted += 1
    return {"accepted": accepted, "skipped": len(body.item_ids) - accepted}


class EditDecision(BaseModel):
    outcome: str
    reason: str = Field(min_length=3, max_length=1000)


@router.post("/decisions/{item_id}/edit")
def edit(item_id: str, body: EditDecision, db: Tx, role: PersonaRole) -> dict[str, str]:
    if body.outcome not in OUTCOMES:
        raise HTTPException(status_code=422, detail="Unknown outcome")
    row = _load(db, item_id, lock=True)
    if not _allowed(row, role).edit:
        raise HTTPException(
            status_code=403, detail="Only the consultant can edit a decision that is still open."
        )
    now = datetime.now(UTC)
    if row["proposed_outcome"]:
        _remember(db, row, row["proposed_outcome"], "rejected", PERSONAS[role], now, body.reason)
    # A changed outcome needs fresh approvals, and resolves a conflict by a person's choice.
    db.execute(text("DELETE FROM studio.approval WHERE item_id = :item_id"), {"item_id": item_id})
    db.execute(
        text("""
            UPDATE studio.decision
            SET outcome = :outcome, action = NULL, edit_reason = :reason, conflict_open = false
            WHERE item_id = :item_id
        """),
        {"outcome": body.outcome, "reason": body.reason, "item_id": item_id},
    )
    audit.record(
        db,
        now,
        PERSONAS[role],
        role,
        "edited",
        item_id,
        {"from": row["outcome"], "to": body.outcome, "reason": body.reason},
    )
    _refresh_status(db, item_id, now)
    return {"status": "ok"}


class AskCustomer(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    options: list[str] = Field(default_factory=list, max_length=4)


@router.post("/decisions/{item_id}/ask")
def ask(item_id: str, body: AskCustomer, db: Tx, role: PersonaRole) -> dict[str, str]:
    row = _load(db, item_id, lock=True)
    if not _allowed(row, role).ask:
        raise HTTPException(status_code=403, detail="This question cannot be raised now.")
    now = datetime.now(UTC)
    db.execute(
        text("""
            INSERT INTO studio.customer_question (item_id, question, options, status, asked_by, asked_at)
            VALUES (:item_id, :question, CAST(:options AS jsonb), 'open', :asked_by, :at)
        """),
        {
            "item_id": item_id,
            "question": body.question,
            "options": json.dumps(body.options),
            "asked_by": PERSONAS[role],
            "at": now,
        },
    )
    audit.record(db, now, PERSONAS[role], role, "asked_customer", item_id, {"question": body.question})
    _refresh_status(db, item_id, now)
    return {"status": "ok"}


class AnswerQuestion(BaseModel):
    answer: str = Field(min_length=1, max_length=1000)


@router.post("/decisions/{item_id}/answer")
def answer(item_id: str, body: AnswerQuestion, db: Tx, role: PersonaRole) -> dict[str, str]:
    _load(db, item_id, lock=True)
    question = _open_question(db, item_id)
    if role != CUSTOMER or question is None:
        raise HTTPException(status_code=403, detail="Only the customer can answer an open question.")
    now = datetime.now(UTC)
    db.execute(
        text("""
            UPDATE studio.customer_question
            SET status = 'answered', answer = :answer, answered_by = :person, answered_at = :at
            WHERE question_id = :question_id
        """),
        {
            "answer": body.answer,
            "person": PERSONAS[CUSTOMER],
            "at": now,
            "question_id": question["question_id"],
        },
    )
    db.execute(
        text("UPDATE studio.decision SET conflict_open = false WHERE item_id = :item_id"),
        {"item_id": item_id},
    )
    audit.record(db, now, PERSONAS[CUSTOMER], CUSTOMER, "answered", item_id, {"answer": body.answer})
    _refresh_status(db, item_id, now)
    return {"status": "ok"}


@router.get("/mapping-memory")
def mapping_memory(db: Tx) -> list[dict[str, Any]]:
    rows = db.execute(text("SELECT * FROM studio.mapping_memory ORDER BY memory_id DESC")).mappings()
    return [dict(row) for row in rows]


@router.post("/demo/reset")
def reset(db: Tx) -> dict[str, str]:
    seed_decisions(db)
    return {"status": "ok"}


@router.get("/audit/verify")
def verify_audit(db: Tx) -> dict[str, bool]:
    return {"intact": audit.verify_chain(db)}
