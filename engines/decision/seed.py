"""Builds the demo's start state: proposals, plus the few decisions already in flight.

Also used by the presenter's reset, so it must stay fast and repeatable.
"""

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Connection, text

from engines.agents.analysis import analyse_reports, analyse_workflows, find_stale_partner_lists
from engines.agents.pipeline import store_artefacts
from engines.decision import audit
from engines.decision.policy import CONSULTANT, CUSTOMER, PERSONAS, required_roles, status_for
from engines.decision.rules import ENGINE_VERSION, RETIRE, ItemFacts, Proposal, propose

START_TIME = datetime(2026, 10, 30, 16, 0, tzinfo=UTC)
ENGINE_ACTOR = "Decision engine"

# The mock-up's starting statuses: one retirement already agreed, two questions already sent.
AGREED_AT_START = "RP-031"
RETIRE_CHOICES = ["Keep it", "Retire it"]
ROUTINE_MIN_CONFIDENCE = 85


def _dependencies(db: Connection) -> dict[str, list[dict[str, str]]]:
    rows = (
        db.execute(
            text("""
            SELECT item_id, name, item_type,
                   definition -> 'tables_read' AS reads, definition -> 'tables_written' AS writes
            FROM studio.estate_item WHERE item_type IN ('CC', 'INT')
        """)
        )
        .mappings()
        .all()
    )
    writers = [
        (row["item_id"], row["name"], table)
        for row in rows
        if row["item_type"] == "INT"
        for table in row["writes"]
    ]
    found: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["item_type"] != "CC":
            continue
        for writer_id, writer_name, table in writers:
            # Core tables are shared by design. Only a custom table is a hidden dependency.
            if table in row["reads"] and table.startswith("zz_"):
                found[row["item_id"]].append(
                    {"depends_on": writer_id, "name": writer_name, "table_name": table}
                )
    return found


def load_facts(db: Connection) -> list[ItemFacts]:
    dependencies = _dependencies(db)
    dormant = {
        row["entity_code"]: row["dormant_since"].strftime("%B %Y")
        for row in db.execute(
            text("SELECT entity_code, dormant_since FROM studio.legal_entity WHERE status = 'dormant'")
        ).mappings()
    }
    entities: dict[str, list[str]] = defaultdict(list)
    for row in db.execute(text("SELECT DISTINCT item_id, entity_code FROM studio.usage_event")).mappings():
        entities[row["item_id"]].append(row["entity_code"])
    precedents = {
        row["pattern"]: row["count"]
        for row in db.execute(
            text("""
                SELECT pattern, count(*) AS count FROM studio.mapping_precedent
                WHERE review_status = 'approved' GROUP BY pattern
            """)
        ).mappings()
    }
    j2x = {
        row["item_id"]: row["summary"]
        for row in db.execute(text("SELECT item_id, summary FROM studio.j2x_explanation")).mappings()
    }
    rows = db.execute(
        text("""
            SELECT e.*, to_jsonb(s) AS signal
            FROM studio.estate_item e
            JOIN studio.agent_signal s USING (item_id)
            ORDER BY e.item_id
        """)
    ).mappings()
    facts = [
        ItemFacts(
            item_id=row["item_id"],
            item_type=row["item_type"],
            name=row["name"],
            owner=row["owner"],
            documented=row["documented"],
            usage_12m=row["usage_12m"],
            last_used=row["last_used"],
            definition=row["definition"],
            source_text=row["source_text"],
            signal=row["signal"],
            usage_entities=entities[row["item_id"]],
            dormant_entities=dormant,
            dependencies=dependencies[row["item_id"]],
            precedents=precedents.get(row["name"], 0),
            j2x_summary=j2x.get(row["item_id"]),
        )
        for row in rows
    ]
    catalogue = db.execute(
        text("SELECT content FROM studio.reference_document WHERE document_key = 'erpx_standard_catalogue'")
    ).scalar_one()
    active_partners = set(
        db.execute(text("SELECT partner_code FROM cr_source.resource_reference WHERE active")).scalars()
    )
    analyse_reports(facts, catalogue["reports"])
    analyse_workflows(facts)
    find_stale_partner_lists(facts, active_partners)
    return facts


INSERT_PROPOSAL = text("""
    INSERT INTO studio.proposal (item_id, outcome, candidate_outcome, action, state, reason, confidence,
                                 rule, flags, evidence, engine_version)
    VALUES (:item_id, :outcome, :candidate_outcome, :action, :state, :reason, :confidence, :rule,
            CAST(:flags AS jsonb), CAST(:evidence AS jsonb), :engine_version)
""")
INSERT_DECISION = text("""
    INSERT INTO studio.decision (item_id, outcome, action, status, conflict_open, updated_at)
    VALUES (:item_id, :outcome, :action, :status, :conflict_open, :updated_at)
""")
INSERT_QUESTION = text("""
    INSERT INTO studio.customer_question (item_id, question, options, status, asked_by, asked_at)
    VALUES (:item_id, :question, CAST(:options AS jsonb), 'open', :asked_by, :asked_at)
""")
INSERT_APPROVAL = text("INSERT INTO studio.approval VALUES (:item_id, :role, :person, :decided_at)")


def _proposal_row(item_id: str, proposal: Proposal) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "outcome": proposal.outcome,
        "candidate_outcome": proposal.candidate_outcome,
        "action": proposal.action,
        "state": proposal.state,
        "reason": proposal.reason,
        "confidence": proposal.confidence,
        "rule": proposal.rule,
        "flags": json.dumps(proposal.flags),
        "evidence": json.dumps(proposal.evidence),
        "engine_version": ENGINE_VERSION,
    }


def _is_routine(item_type: str, proposal: Proposal, required: list[str], has_question: bool) -> bool:
    """Decisions a consultant would already have cleared before the demo starts.

    Seeded, and labelled so on the audit trail and in the sign-off pack. Anything flagged, unsure,
    needing a second role, or in configuration stays open, because reconciliation can reopen those.
    """
    return (
        required == [CONSULTANT]
        and item_type != "CF"
        and (proposal.confidence or 0) >= ROUTINE_MIN_CONFIDENCE
        and not proposal.flags
        and not has_question
    )


def seed_decisions(db: Connection) -> None:
    db.execute(
        text("""
        TRUNCATE studio.audit_event, studio.customer_question, studio.approval, studio.decision,
                 studio.check_run, studio.mapping_memory, studio.artefact, studio.signoff_pack,
                 studio.timing_event, studio.exception_resolution,
                 studio.proposal, studio.dependency RESTART IDENTITY CASCADE
    """)
    )
    for item_id, rows in sorted(_dependencies(db).items()):
        for row in rows:
            db.execute(
                text("INSERT INTO studio.dependency VALUES (:item_id, :depends_on, :table_name)"),
                {"item_id": item_id, "depends_on": row["depends_on"], "table_name": row["table_name"]},
            )

    store_artefacts(db)
    writer = audit.Writer(db)
    proposals, decisions, questions, approvals = [], [], [], []
    for facts in load_facts(db):
        proposal = propose(facts)
        proposals.append(_proposal_row(facts.item_id, proposal))
        conflict = facts.signal.get("conflict") or {}
        conflict_open = bool(conflict.get("blocks_acceptance"))
        question = facts.signal.get("question")
        if proposal.state == "held" and not question:
            question = f"{facts.name} looks unused, but it may have a legal, audit or tax purpose. Can it go?"
        required = required_roles(facts.item_type, proposal.outcome)
        routine = _is_routine(facts.item_type, proposal, required, bool(question))
        approved = [CONSULTANT] if routine else []
        if facts.item_id == AGREED_AT_START:
            approved = [CONSULTANT, CUSTOMER]
        status = status_for(required, approved, bool(question), conflict_open)
        decisions.append(
            {
                "item_id": facts.item_id,
                "outcome": proposal.outcome,
                "action": proposal.action,
                "status": status,
                "conflict_open": conflict_open,
                "updated_at": START_TIME,
            }
        )
        writer.record(
            START_TIME,
            ENGINE_ACTOR,
            "engine",
            "proposed",
            facts.item_id,
            {"outcome": proposal.outcome, "state": proposal.state, "rule": proposal.rule},
        )
        if question:
            asked_at = START_TIME + timedelta(minutes=10)
            questions.append(
                {
                    "item_id": facts.item_id,
                    "question": question,
                    # An item that may go gets two clear choices. An interview needs a written answer.
                    "options": json.dumps(
                        RETIRE_CHOICES if RETIRE in (proposal.outcome, proposal.candidate_outcome) else []
                    ),
                    "asked_by": PERSONAS[CONSULTANT],
                    "asked_at": asked_at,
                }
            )
            writer.record(
                asked_at,
                PERSONAS[CONSULTANT],
                CONSULTANT,
                "asked_customer",
                facts.item_id,
                {"question": question},
            )
        for offset, role in enumerate(approved, start=1):
            approved_at = START_TIME + timedelta(minutes=30 if routine else 60 * offset)
            approvals.append(
                {"item_id": facts.item_id, "role": role, "person": PERSONAS[role], "decided_at": approved_at}
            )
            writer.record(
                approved_at,
                PERSONAS[role],
                role,
                "accepted_seeded" if routine else "accepted",
                facts.item_id,
                {"outcome": proposal.outcome},
            )
    db.execute(INSERT_PROPOSAL, proposals)
    db.execute(INSERT_DECISION, decisions)
    db.execute(INSERT_QUESTION, questions)
    db.execute(INSERT_APPROVAL, approvals)
    writer.flush()
