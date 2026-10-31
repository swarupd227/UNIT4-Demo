"""The two checks that are not a plain source-to-target comparison."""

import re
from typing import Any

from sqlalchemy import Connection, text

REPORTING_DATE = "2026-10-31"
RULE_ITEM = "CC-014"

AGE_BAND = """
    CASE WHEN CAST(:reporting_date AS date) - w.txn_date <= 30 THEN '0-30'
         WHEN CAST(:reporting_date AS date) - w.txn_date <= 60 THEN '31-60'
         WHEN CAST(:reporting_date AS date) - w.txn_date <= 90 THEN '61-90'
         ELSE 'over 90' END
"""


def _wip_by_partner(db: Connection, schema: str, partners: list[str] | None) -> dict[tuple[str, str], int]:
    """WIP ageing by partner. `partners` limits it as the report's typed-in list does."""
    sql = f"""
        SELECT p.partner_code, {AGE_BAND} AS band, sum(w.billable_minor) AS value
        FROM {schema}.wip_item w
        JOIN {schema}.project p USING (project_id)
        WHERE p.status = 'open' AND (:all_partners OR p.partner_code = ANY(:partners))
        GROUP BY 1, 2
    """
    rows = db.execute(
        text(sql),
        {"reporting_date": REPORTING_DATE, "all_partners": partners is None, "partners": partners or []},
    )
    return {(row.partner_code, row.band): int(row.value) for row in rows}


def _utilisation(db: Connection, schema: str) -> dict[tuple[str, str], tuple[int, int]]:
    rows = db.execute(
        text(f"SELECT period, grade, available_hours, billable_hours FROM {schema}.utilisation_summary")
    )
    return {(row.period, row.grade): (row.available_hours, row.billable_hours) for row in rows}


def report_parity(db: Connection) -> dict[str, Any]:
    """Two steps for RP-077, because a fixed report cannot match a report with a stale list.

    Step 1 rebuilds it faithfully, which proves the logic. Step 2 fixes the list, and the difference
    must equal the omitted partners' WIP exactly.
    """
    definition = db.execute(
        text("SELECT definition FROM studio.estate_item WHERE item_id = 'RP-077'")
    ).scalar_one()
    listed = definition["hard_coded_partners"]

    legacy = _wip_by_partner(db, "cr_source", listed)
    faithful = _wip_by_partner(db, "erpx_sim", listed)
    fixed = _wip_by_partner(db, "erpx_sim", None)
    omitted_source = _wip_by_partner(db, "cr_source", None)

    differences = []
    for key in sorted(legacy.keys() | faithful.keys()):
        if legacy.get(key) != faithful.get(key):
            differences.append(
                {
                    "row_key": f"RP-077 faithful / {key[0]} / {key[1]}",
                    "source_value": legacy.get(key),
                    "target_value": faithful.get(key),
                    "difference": faithful.get(key, 0) - legacy.get(key, 0),
                    "detail": {},
                }
            )

    legacy_total = sum(legacy.values())
    fixed_total = sum(fixed.values())
    omitted = {key: value for key, value in omitted_source.items() if key[0] not in listed}
    omitted_total = sum(omitted.values())
    if fixed_total - legacy_total != omitted_total:
        differences.append(
            {
                "row_key": "RP-077 fixed / unexplained",
                "source_value": legacy_total + omitted_total,
                "target_value": fixed_total,
                "difference": fixed_total - legacy_total - omitted_total,
                "detail": {},
            }
        )

    source_use = _utilisation(db, "cr_source")
    target_use = _utilisation(db, "erpx_sim")
    for key in sorted(source_use.keys() | target_use.keys()):
        if source_use.get(key) != target_use.get(key):
            differences.append(
                {
                    "row_key": f"RP-084 / {key[0]} / {key[1]}",
                    "source_value": None,
                    "target_value": None,
                    "difference": None,
                    "detail": {"source": source_use.get(key), "target": target_use.get(key)},
                }
            )

    return {
        "status": "fail" if differences else "pass",
        "source_value": legacy_total,
        "target_value": fixed_total,
        "source_count": 2,
        "target_count": 2,
        "differences": differences,
        "summary": {
            "reports": [
                {
                    "report": "RP-077",
                    "name": "WIP ageing by partner",
                    "cr_total": legacy_total,
                    "faithful_rebuild_total": sum(faithful.values()),
                    "fixed_rebuild_total": fixed_total,
                    "reconciling_item": {
                        "label": "WIP of partners missing from the typed-in list",
                        "partners": sorted({key[0] for key in omitted}),
                        "amount": omitted_total,
                    },
                },
                {
                    "report": "RP-084",
                    "name": "Utilisation by grade",
                    "cr_total": sum(billable for _, billable in source_use.values()),
                    "rebuilt_total": sum(billable for _, billable in target_use.values()),
                },
            ]
        },
    }


def rule_decision(case: dict[str, Any], threshold_pct: int) -> str:
    """The rebuilt approval rule. A write-down above the threshold holds unless already approved."""
    billable, adjust = case["billable_minor"], case["adjust_minor"]
    above = billable != 0 and adjust * 100 > threshold_pct * billable
    if case["adjust_type"] == "write_down" and above and not case["prior_approval"]:
        return "hold"
    return "apply"


def chosen_threshold(db: Connection) -> int | None:
    answer = db.execute(
        text("""
            SELECT answer FROM studio.customer_question
            WHERE item_id = :item_id AND status = 'answered'
            ORDER BY answered_at DESC LIMIT 1
        """),
        {"item_id": RULE_ITEM},
    ).scalar()
    match = re.search(r"(\d+)\s*%", answer or "")
    return int(match.group(1)) if match else None


def billing_rule_tests(db: Connection) -> dict[str, Any]:
    tests = db.execute(
        text("SELECT content FROM studio.artefact WHERE item_id = :item_id AND kind = 'test_cases'"),
        {"item_id": RULE_ITEM},
    ).scalar_one()
    threshold = chosen_threshold(db)
    total = len(tests["cases"])
    if threshold is None:
        return {
            "status": "waiting",
            "source_value": total,
            "target_value": None,
            "source_count": total,
            "target_count": 0,
            "differences": [],
            "summary": {"waiting_for": "The customer to choose the write-down threshold", "threshold": None},
        }

    expected_key = f"expected_at_{threshold}"
    differences = []
    results = []
    for case in tests["cases"]:
        actual = rule_decision(case, threshold)
        expected = case.get(expected_key)
        passed = actual == expected
        results.append({"id": case["id"], "description": case["description"], "passed": passed})
        if not passed:
            differences.append(
                {
                    "row_key": case["id"],
                    "source_value": None,
                    "target_value": None,
                    "difference": None,
                    "detail": {"expected": expected, "actual": actual, "description": case["description"]},
                }
            )
    return {
        "status": "fail" if differences else "pass",
        "source_value": total,
        "target_value": total - len(differences),
        "source_count": total,
        "target_count": total - len(differences),
        "differences": differences,
        "summary": {"threshold": threshold, "results": results},
    }
