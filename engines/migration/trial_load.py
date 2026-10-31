"""Trial migration of one entity from CR extracts into an ErpxTarget.

The planted differences are not written here. They come from the mapping and load settings:
the revaluation rate precision (M7), the closed-project WIP exclusion (M8) and the many-to-one
account merges (M6).
"""

from collections import defaultdict
from typing import Any

from data.generator.common import multiply_rate, round_rate
from engines.migration.target import ErpxTarget

Rows = list[dict[str, str]]


def run_trial_load(source: dict[str, Rows], settings: dict[str, Any], target: ErpxTarget) -> None:
    account_map = {row["account_code"]: row["erpx_account"] for row in source["account_map"]}
    dimension_map = {(row["dimension"], row["value"]): row["erpx_value"] for row in source["dimension_map"]}

    accounts: dict[str, tuple] = {}
    for row in source["account"]:
        erpx = account_map[row["account_code"]]
        accounts.setdefault(erpx, (erpx, row["name"].split(" - ")[0], row["account_type"], row["vat_code"]))
    target.load("account", ["erpx_account", "name", "account_type", "vat_code"], sorted(accounts.values()))

    values = sorted({(dimension, value) for (dimension, _), value in dimension_map.items()})
    target.load("dimension_value", ["dimension", "erpx_value"], values)

    for master, id_column in (("customer", "customer_id"), ("supplier", "supplier_id")):
        rows = [(row[id_column], row["name"], row["country"], row["active"]) for row in source[master]]
        target.load(master, [id_column, "name", "country", "active"], rows)

    project_columns = [
        "project_id",
        "name",
        "customer_id",
        "partner_code",
        "service_line",
        "status",
        "start_date",
        "closed_date",
    ]
    target.load(
        "project",
        project_columns,
        [
            tuple(
                dimension_map[("SERVLINE", row[c])] if c == "service_line" else row[c]
                for c in project_columns
            )
            for row in source["project"]
        ],
    )

    decimals = settings["fx_rate_decimals"]
    rates = {row["currency"]: round_rate(row["rate_text"], decimals) for row in source["fx_rate"]}
    target.load(
        "fx_rate",
        ["currency", "rate_date", "rate_text"],
        [(row["currency"], row["rate_date"], rates[row["currency"]]) for row in source["fx_rate"]],
    )

    item_columns = [
        "item_id",
        "customer_id",
        "invoice_date",
        "due_date",
        "currency",
        "amount_cur_minor",
        "base_minor",
    ]
    receivables = []
    for row in source["ar_open_item"]:
        amount = int(row["amount_cur_minor"])
        base = amount if row["currency"] == "GBP" else multiply_rate(amount, rates[row["currency"]])
        receivables.append((*[row[c] for c in item_columns[:-1]], base))
    target.load("ar_open_item", item_columns, receivables)

    # Payables are carried at their booked base value and are not revalued on load.
    payable_columns = ["supplier_id" if c == "customer_id" else c for c in item_columns]
    target.load(
        "ap_open_item",
        payable_columns,
        [tuple(row[c] for c in payable_columns) for row in source["ap_open_item"]],
    )

    excluded = set(settings["wip_excluded_project_status"])
    loadable = {row["project_id"] for row in source["project"] if row["status"] not in excluded}
    wip_columns = ["wip_id", "project_id", "txn_date", "hours_x100", "cost_minor", "billable_minor"]
    target.load(
        "wip_item",
        wip_columns,
        [tuple(row[c] for c in wip_columns) for row in source["wip_item"] if row["project_id"] in loadable],
    )

    utilisation_columns = ["period", "grade", "available_hours", "billable_hours"]
    target.load(
        "utilisation_summary",
        utilisation_columns,
        [tuple(row[c] for c in utilisation_columns) for row in source["utilisation_summary"]],
    )

    balances: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for row in source["gl_balance"]:
        key = (
            account_map[row["account_code"]],
            row["period"],
            dimension_map[("COSTC", row["cost_centre"])],
            dimension_map[("SERVLINE", row["service_line"])],
        )
        balances[key] += int(row["amount_minor"])
    target.load(
        "gl_balance",
        ["erpx_account", "period", "cost_centre", "service_line", "amount_minor"],
        [(*key, value) for key, value in sorted(balances.items())],
    )
