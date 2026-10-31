"""Scores the system's own output against the answer key.

This is the only module that reads the answer_key schema. Each detector looks at what the system
actually produced, so an issue only counts when it reached a person with its evidence.
"""

from collections import Counter
from typing import Any

from sqlalchemy import Connection, text

MAX_FALSE_ITEMS = 3
ISSUE_FOR_EXCEPTION = {
    "fx_rate_precision": "M7",
    "closed_project_wip": "M8",
    "vat_mapping_conflict": "M6",
    "duplicate_dimension_value": "M9",
}
RAISING_FLAGS = {
    "conflict",
    "hidden_dependency",
    "stale_logic",
    "dormant_use",
    "needs_interview",
    "refused_retire",
}


def _proposals(db: Connection) -> dict[str, dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT p.item_id, p.outcome, p.action, p.state, p.flags, p.evidence, s.conflict
            FROM studio.proposal p JOIN studio.agent_signal s USING (item_id)
        """)
    ).mappings()
    return {row["item_id"]: dict(row) for row in rows}


def _latest_run(db: Connection) -> int | None:
    return db.execute(text("SELECT max(run_id) FROM studio.check_run")).scalar()


def _detect(proposals: dict[str, dict[str, Any]], exceptions: dict[str, dict[str, Any]]) -> dict[str, bool]:
    def has(item_id: str, flag: str) -> bool:
        return flag in proposals[item_id]["flags"]

    conflict = proposals["CC-014"]["conflict"] or {}
    r2 = exceptions.get("fx_rate_precision")
    return {
        "M1": has("CC-014", "conflict")
        and {conflict.get("left_value"), conflict.get("right_value")} == {"10%", "15%"},
        "M2": any(
            e["kind"] == "dependency" and e.get("item") == "INT-09" for e in proposals["CC-014"]["evidence"]
        ),
        "M3": proposals["RP-112"]["state"] == "held" and has("RP-112", "refused_retire"),
        "M4": has("RP-077", "stale_logic"),
        "M5": proposals["WF-006"]["outcome"] == "retire" and has("WF-006", "dormant_use"),
        "M6": "vat_mapping_conflict" in exceptions,
        "M7": r2 is not None and abs(r2["amount_minor"]) == 124050,
        "M8": "closed_project_wip" in exceptions
        and len(exceptions["closed_project_wip"]["detail"]["projects"]) == 14,
        "M9": "duplicate_dimension_value" in exceptions,
        "M10": proposals["CC-037"]["state"] == "held" and has("CC-037", "needs_interview"),
    }


def _false_items(
    db: Connection, proposals: dict[str, dict[str, Any]], exceptions: dict[str, dict[str, Any]]
) -> list[str]:
    """Everything raised to a person that no planted issue accounts for."""
    planted_items = set(
        db.execute(text("SELECT item_ref FROM answer_key.planted_issue WHERE item_ref IS NOT NULL")).scalars()
    )
    false_items = [
        item_id
        for item_id, proposal in proposals.items()
        if item_id not in planted_items
        and (proposal["state"] == "held" or RAISING_FLAGS & set(proposal["flags"]))
    ]
    false_items += [code for code in exceptions if code not in ISSUE_FOR_EXCEPTION]
    return sorted(false_items)


def _decision_quality(db: Connection, proposals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keyed = db.execute(
        text("SELECT item_id, expected_outcome, expected_state FROM answer_key.expected_decision")
    ).mappings()
    wrong = []
    totals: Counter[str] = Counter()
    for row in keyed:
        proposal = proposals[row["item_id"]]
        totals[row["item_id"][:2]] += 1
        # A held item is correct when it is held: its outcome is the customer's to give.
        same_state = proposal["state"] == row["expected_state"]
        if not same_state or (
            row["expected_state"] != "held" and proposal["outcome"] != row["expected_outcome"]
        ):
            wrong.append(row["item_id"])
    total = sum(totals.values())
    return {"matched": total - len(wrong), "total": total, "wrong": sorted(wrong), "by_type": dict(totals)}


def score(db: Connection) -> dict[str, Any]:
    proposals = _proposals(db)
    run_id = _latest_run(db)
    exceptions = {}
    if run_id is not None:
        rows = db.execute(
            text("SELECT code, amount_minor, detail FROM studio.exception WHERE run_id = :run_id"),
            {"run_id": run_id},
        ).mappings()
        exceptions = {row["code"]: dict(row) for row in rows}

    detected = _detect(proposals, exceptions)
    false_items = _false_items(db, proposals, exceptions)
    found = sum(detected.values())
    return {
        "reconciliation_run": run_id,
        "issues": {"found": found, "planted": len(detected), "detail": detected},
        "false_items": {"count": len(false_items), "limit": MAX_FALSE_ITEMS, "items": false_items},
        "decision_quality": _decision_quality(db, proposals),
        "passed": found == len(detected) and len(false_items) <= MAX_FALSE_ITEMS,
    }
