"""Turns differences into exceptions, each with a cause that has been proven from the data."""

from collections import defaultdict
from typing import Any

from sqlalchemy import Connection, text

from data.generator.common import multiply_rate


def _pounds(minor: int) -> str:
    return f"£{abs(minor) / 100:,.2f}"


def _receivables(db: Connection, differences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not differences:
        return []
    source_rates = dict(db.execute(text("SELECT currency, rate_text FROM cr_source.fx_rate")).all())
    target_rates = dict(db.execute(text("SELECT currency, rate_text FROM erpx_sim.fx_rate")).all())
    rows = db.execute(
        text("""
            SELECT s.item_id, s.currency, s.amount_cur_minor, s.base_minor AS source_base,
                   t.base_minor AS target_base
            FROM cr_source.ar_open_item s JOIN erpx_sim.ar_open_item t USING (item_id)
            WHERE s.base_minor <> t.base_minor
        """)
    ).all()

    by_currency: dict[str, dict[str, int]] = defaultdict(lambda: {"items": 0, "difference": 0})
    explained = True
    for row in rows:
        rate = target_rates.get(row.currency)
        explained = (
            explained and rate is not None and multiply_rate(row.amount_cur_minor, rate) == row.target_base
        )
        by_currency[row.currency]["items"] += 1
        by_currency[row.currency]["difference"] += row.target_base - row.source_base

    total = sum(entry["difference"] for entry in by_currency.values())
    decimals = sorted({len(rate.split(".")[1]) for rate in target_rates.values()})
    source_decimals = sorted({len(rate.split(".")[1]) for rate in source_rates.values()})
    rounding_limit = sum(entry["items"] for entry in by_currency.values()) // 2
    if not explained or abs(total) <= rounding_limit:
        return [
            {
                "code": "receivables_difference",
                "title": f"Receivables differ by {_pounds(total)}",
                "cause": "Not yet explained.",
                "proposed_action": "Investigate the differing items.",
                "approver_role": "consultant",
                "amount_minor": total,
                "detail": {"by_currency": by_currency},
            }
        ]

    changes = [f"{c} {source_rates[c]} to {target_rates[c]}" for c in sorted(by_currency)]
    return [
        {
            "code": "fx_rate_precision",
            "title": f"Receivables differ by {_pounds(total)}",
            "cause": f"The trial load holds revaluation rates at {decimals[0]} decimal places, and CR holds "
            f"{source_decimals[0]} ({'; '.join(changes)}). Recalculating every differing item at the "
            "loaded rate reproduces the difference exactly.",
            "proposed_action": f"Load revaluation rates at {source_decimals[0]} decimal places and rerun.",
            "approver_role": "consultant",
            "amount_minor": total,
            "detail": {
                "by_currency": {key: dict(value) for key, value in sorted(by_currency.items())},
                "source_rates": source_rates,
                "target_rates": target_rates,
                "items_recalculated": len(rows),
                "line_rounding_limit_minor": rounding_limit,
            },
        }
    ]


def _project_wip(differences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closed = [row for row in differences if row["detail"].get("project_status") == "closed"]
    other = [row for row in differences if row not in closed]
    exceptions = []
    if closed:
        amount = sum(row["difference"] or 0 for row in closed)
        exceptions.append(
            {
                "code": "closed_project_wip",
                "title": f"{len(closed)} closed projects still hold WIP",
                "cause": "Billing policy section 5 says a closed project may not hold WIP. These projects "
                f"hold {_pounds(amount)}, which the load correctly leaves behind.",
                "proposed_action": "Bill or write off the balance in CR before migration.",
                "approver_role": "customer",
                "amount_minor": amount,
                "detail": {"projects": [row["row_key"] for row in closed]},
            }
        )
    if other:
        exceptions.append(
            {
                "code": "wip_difference",
                "title": f"{len(other)} projects differ in WIP",
                "cause": "Not yet explained.",
                "proposed_action": "Investigate the differing projects.",
                "approver_role": "consultant",
                "amount_minor": sum(row["difference"] or 0 for row in other),
                "detail": {"projects": [row["row_key"] for row in other]},
            }
        )
    return exceptions


def _mapping(differences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exceptions = []
    for row in differences:
        detail = row["detail"]
        sub_rule = detail["sub_rule"]
        if sub_rule == "many_to_one_conflict":
            accounts = detail["accounts"]
            listed = ", ".join(f"{a['account']} ({a['vat_code']})" for a in accounts)
            exceptions.append(
                {
                    "code": "vat_mapping_conflict",
                    "title": f"Two accounts merge with different VAT codes: {listed}",
                    "cause": f"They map to ERPx account {detail['erpx_account']}, which holds one VAT code.",
                    "proposed_action": "Keep separate ERPx accounts, or set VAT by transaction.",
                    "approver_role": "customer",
                    "amount_minor": None,
                    "detail": detail,
                }
            )
        elif sub_rule == "duplicate_value":
            shown = " and ".join(f'"{value}"' for value in detail["values"])
            exceptions.append(
                {
                    "code": "duplicate_dimension_value",
                    "title": f"{detail['dimension']} value stored twice: {shown}",
                    "cause": "The two values differ only by trailing spaces.",
                    "proposed_action": "Merge into one value.",
                    "approver_role": "consultant",
                    "amount_minor": None,
                    "detail": detail,
                }
            )
        else:
            exceptions.append(
                {
                    "code": "unmapped_value",
                    "title": f"Unmapped value: {row['row_key']}",
                    "cause": "No ERPx value is mapped.",
                    "proposed_action": "Add a mapping.",
                    "approver_role": "consultant",
                    "amount_minor": None,
                    "detail": detail,
                }
            )
    return exceptions


def explain(db: Connection, check_id: str, differences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if check_id == "R2":
        return _receivables(db, differences)
    if check_id == "R4":
        return _project_wip(differences)
    if check_id == "R6":
        return _mapping(differences)
    if differences:
        return [
            {
                "code": f"{check_id.lower()}_difference",
                "title": f"{check_id} found {len(differences)} differences",
                "cause": "Not yet explained.",
                "proposed_action": "Investigate the differing rows.",
                "approver_role": "consultant",
                "amount_minor": None,
                "detail": {},
            }
        ]
    return []
