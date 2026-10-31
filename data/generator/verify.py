"""Independent check of the generated files against the specification.

It reads only the output files, so it fails if a generator drifts from the spec. Nothing here
imports generator logic, apart from shared paths and CSV reading.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from data.generator.common import GENERATED, build_manifest, read_table

Row = dict[str, str]


class Checks:
    def __init__(self) -> None:
        self.failed = 0

    def check(self, label: str, passed: bool, detail: object = "") -> None:
        self.failed += not passed
        print(f"  {'PASS' if passed else 'FAIL'}  {label}{f'  [{detail}]' if detail != '' else ''}")


def _pounds(minor: int) -> str:
    return f"£{minor / 100:,.2f}"


def verify(root: Path = GENERATED) -> bool:
    c = Checks()
    src = {p.stem: read_table(p) for p in (root / "cr_source").glob("*.csv")}
    tgt = {p.stem: read_table(p) for p in (root / "erpx_sim").glob("*.csv")}
    studio = {p.stem: read_table(p) for p in (root / "studio").glob("*.csv")}
    key = {r["item_id"]: r for r in read_table(root / "answer_key" / "expected_decision.csv")}
    planted = read_table(root / "answer_key" / "planted_issue.csv")
    items = {r["item_id"]: r for r in studio["estate_item"]}
    definition = {i: json.loads(r["definition"]) for i, r in items.items()}
    types = Counter(r["item_type"] for r in items.values())
    events: dict[str, list[Row]] = defaultdict(list)
    for event in studio["usage_event"]:
        events[event["item_id"]].append(event)

    print("Estate counts")
    c.check("64 custom code items", types["CC"] == 64, types["CC"])
    c.check("2 direct database writers", sum(r["direct_db_write"] == "True" for r in items.values()) == 2)
    c.check("148 custom reports", types["RP"] == 148, types["RP"])
    c.check("9 workflow variants", types["WF"] == 9, types["WF"])
    c.check("14 integrations", types["INT"] == 14, types["INT"])
    c.check("About 2,300 accounts", 2250 <= len(src["account"]) <= 2350, len(src["account"]))
    c.check("About 3,100 receivables", 3050 <= len(src["ar_open_item"]) <= 3150, len(src["ar_open_item"]))
    c.check("About 1,450 payables", 1400 <= len(src["ap_open_item"]) <= 1500, len(src["ap_open_item"]))
    open_projects = sum(r["status"] == "open" for r in src["project"])
    c.check("About 860 active projects", open_projects == 860, open_projects)
    c.check("Mock-up IDs exist", {"CC-014", "RP-077", "RP-112", "RP-031", "WF-006", "CF-203"} <= set(items))

    print("Report plan (61 retire, 38 into 9, 31 standard, 18 rebuild)")
    reports = [r for i, r in key.items() if i.startswith("RP-")]
    merged = [r for r in reports if r["merge_group"]]
    c.check("61 retire", sum(r["expected_outcome"] == "retire" for r in reports) == 61)
    c.check("38 merged", len(merged) == 38, len(merged))
    c.check("Into 9 groups", len({r["merge_group"] for r in merged}) == 9)
    c.check("31 standard", sum(r["expected_outcome"] == "replace_standard" for r in reports) == 31)
    c.check("18 rebuild", sum(r["expected_action"] == "rebuild" for r in reports) == 18)
    retire_usage = [
        int(items[r["item_id"]]["usage_12m"]) for r in reports if r["expected_outcome"] == "retire"
    ]
    c.check("Every retire is unused or in the low-use band", max(retire_usage) <= 2, max(retire_usage))
    protected = re.compile(r"year-end|audit|statutory|tax", re.I)
    decoys = [
        r["item_id"]
        for r in reports
        if r["expected_outcome"] == "retire" and protected.search(items[r["item_id"]]["name"])
    ]
    c.check("Exactly one decoy keyword among retirements", decoys == ["RP-058"], decoys)

    print("Workflows")
    workflow_use = {i: int(r["usage_12m"]) for i, r in items.items() if r["item_type"] == "WF"}
    top_two = sum(sorted(workflow_use.values())[-2:]) / sum(workflow_use.values())
    c.check("Two variants cover most cases", top_two > 0.9, f"{top_two:.0%}")
    survivors = {
        i for i in workflow_use if key[i]["expected_outcome"] != "retire" and not key[i]["expected_action"]
    }
    c.check("Proposal moves 9 to 3", len(survivors) == 3, sorted(survivors))

    print("Planted issues")
    c.check("Ten issues registered", [p["issue_id"] for p in planted] == [f"M{i}" for i in range(1, 11)])

    code = items["CC-014"]["source_text"]
    policy = (root / "documents" / "billing_policy.md").read_text(encoding="utf-8")
    c.check("M1 code says 10%, policy says 15%", "Limit = 0.10m" in code and "more than 15%" in policy)

    table = "zz_rate_override"
    writers = [
        i for i, r in items.items() if r["item_type"] == "INT" and table in definition[i]["tables_written"]
    ]
    c.check(
        "M2 CC-014 reads a table an integration writes",
        table in code and table in definition["CC-014"]["tables_read"] and writers == ["INT-09"],
        writers,
    )

    rp112 = items["RP-112"]
    c.check(
        "M3 audit pack ran once and is held",
        int(rp112["usage_12m"]) == 1 and key["RP-112"]["expected_state"] == "held",
    )

    stale = set(definition["RP-077"]["hard_coded_partners"])
    current = {r["partner_code"] for r in src["resource_reference"] if r["active"] == "True"}
    project_partner = {r["project_id"]: r["partner_code"] for r in src["project"]}
    project_status = {r["project_id"]: r["status"] for r in src["project"]}
    omitted_wip = sum(
        int(r["billable_minor"])
        for r in src["wip_item"]
        if project_status[r["project_id"]] == "open" and project_partner[r["project_id"]] not in stale
    )
    c.check(
        "M4 list omits current partners who hold WIP",
        len(current - stale) == 6 and omitted_wip > 0,
        f"{len(current - stale)} partners, {_pounds(omitted_wip)}",
    )
    c.check("M4 list still names departed partners", len(stale - current) == 4)

    entity_status = {r["entity_code"]: r["status"] for r in studio["legal_entity"]}
    wf6 = {e["entity_code"] for e in events["WF-006"]}
    c.check(
        "M5 WF-006 is used only by a dormant entity",
        len(wf6) == 1 and entity_status[wf6.pop()] == "dormant" and int(items["WF-006"]["usage_12m"]) == 2,
    )

    account_map = {r["account_code"]: r["erpx_account"] for r in src["account_map"]}
    by_target: dict[str, list[Row]] = defaultdict(list)
    for account in src["account"]:
        by_target[account_map[account["account_code"]]].append(account)
    merges = [g for g in by_target.values() if len(g) > 1]
    conflicts = [g for g in merges if len({a["vat_code"] for a in g}) > 1]
    c.check(
        "M6 exactly one many-to-one merge has conflicting VAT",
        len(conflicts) == 1 and len(conflicts[0]) == 2 and len(merges) > 20,
        f"{len(merges)} merges, conflict {[a['account_code'] for a in conflicts[0]] if conflicts else None}",
    )
    used = {r["account_code"] for r in src["gl_balance"]}
    c.check(
        "M6 both accounts carry balances", conflicts and all(a["account_code"] in used for a in conflicts[0])
    )

    src_ar = {r["item_id"]: r for r in src["ar_open_item"]}
    tgt_ar = {r["item_id"]: r for r in tgt["ar_open_item"]}
    differences = {i: int(tgt_ar[i]["base_minor"]) - int(r["base_minor"]) for i, r in src_ar.items()}
    difference = sum(differences.values())
    foreign_only = all(src_ar[i]["currency"] != "GBP" for i, d in differences.items() if d)
    bound = len(src_ar) // 2
    c.check("M7 receivables differ by exactly £1,240.50", difference == 124050, _pounds(difference))
    c.check("M7 only foreign-currency items differ", foreign_only)
    c.check("M7 too large to be line rounding", difference > bound, f"line rounding limit {_pounds(bound)}")
    c.check("M7 same item count on both sides", len(src_ar) == len(tgt_ar))
    source_rates = {r["currency"]: r["rate_text"] for r in src["fx_rate"]}
    target_rates = {r["currency"]: r["rate_text"] for r in tgt["fx_rate"]}
    c.check(
        "M7 cause visible in the rate tables",
        source_rates != target_rates,
        f"{source_rates} -> {target_rates}",
    )

    held = {r["project_id"] for r in src["wip_item"] if project_status[r["project_id"]] == "closed"}
    held_value = sum(int(r["billable_minor"]) for r in src["wip_item"] if r["project_id"] in held)
    tgt_wip = {r["project_id"] for r in tgt["wip_item"]}
    c.check("M8 14 closed projects hold WIP", len(held) == 14, _pounds(held_value))
    c.check("M8 their WIP does not reach the target", not held & tgt_wip)
    src_wip_open = [r for r in src["wip_item"] if project_status[r["project_id"]] == "open"]
    c.check("M8 all other WIP arrives", len(src_wip_open) == len(tgt["wip_item"]))

    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in src["dimension_value"]:
        groups[(row["dimension"], row["value"].strip().upper())].append(row["value"])
    duplicates = [v for v in groups.values() if len(v) > 1]
    gl_values = {r["service_line"] for r in src["gl_balance"]}
    c.check("M9 one value differs only by trailing spaces", len(duplicates) == 1, duplicates)
    c.check(
        "M9 both spellings carry balances", bool(duplicates) and all(v in gl_values for v in duplicates[0])
    )

    unowned = sorted(
        i
        for i, r in items.items()
        if r["item_type"] == "CC" and not r["owner"] and r["documented"] == "False"
    )
    c.check(
        "M10 CC-037 has no owner or documentation",
        "CC-037" in unowned and key["CC-037"]["expected_state"] == "held",
    )
    c.check("M10 only CC-014 and CC-037 are unowned", unowned == ["CC-014", "CC-037"], unowned)

    print("Checks that should pass")

    def totals(rows: list[Row], *columns: str) -> dict[tuple[str, ...], int]:
        result: dict[tuple[str, ...], int] = defaultdict(int)
        for row in rows:
            result[tuple(row[x] for x in columns)] += int(row["amount_minor"])
        return dict(result)

    dimension_map = {(r["dimension"], r["value"]): r["erpx_value"] for r in src["dimension_map"]}
    mapped = [
        {
            "account": account_map[r["account_code"]],
            "period": r["period"],
            "cost_centre": dimension_map[("COSTC", r["cost_centre"])],
            "service_line": dimension_map[("SERVLINE", r["service_line"])],
            "amount_minor": r["amount_minor"],
        }
        for r in src["gl_balance"]
    ]
    target_gl = [{**r, "account": r["erpx_account"]} for r in tgt["gl_balance"]]
    dims = ("account", "period", "cost_centre", "service_line")
    source_tb = totals(mapped, *dims)
    target_tb = totals(target_gl, *dims)
    c.check("R1 trial balance matches", source_tb == target_tb, f"{len(target_tb)} balances")
    period_nets = totals(src["gl_balance"], "period")
    c.check("Every period nets to zero", not any(period_nets.values()))
    closing = totals(src["gl_balance"], "account_code")
    c.check(
        "Control accounts agree to sub-ledgers",
        closing["120000",] == sum(int(r["base_minor"]) for r in src["ar_open_item"])
        and closing["210000",] == -sum(int(r["base_minor"]) for r in src["ap_open_item"])
        and closing["130000",] == sum(int(r["billable_minor"]) for r in src["wip_item"]),
    )
    c.check(
        "R3 payables match",
        {(r["item_id"], r["base_minor"]) for r in src["ap_open_item"]}
        == {(r["item_id"], r["base_minor"]) for r in tgt["ap_open_item"]},
    )
    c.check(
        "R5 master counts match", all(len(src[t]) == len(tgt[t]) for t in ("customer", "supplier", "project"))
    )
    unmapped = [r["account_code"] for r in src["account"] if r["account_code"] not in account_map]
    c.check("R6 no account is unmapped", not unmapped)

    print("Privacy")
    columns = set()
    for rows in src.values():
        columns |= set(rows[0])
    banned = {"salary", "nino", "date_of_birth", "address", "bank_account", "pay_grade"}
    c.check("No HR or payroll attributes", not columns & banned)

    print("Reproducibility")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    c.check(
        "Manifest matches files", manifest["files"] == build_manifest(root), f"{len(manifest['files'])} files"
    )

    print(f"\n{'All checks passed' if not c.failed else f'{c.failed} checks FAILED'}")
    return c.failed == 0


if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
