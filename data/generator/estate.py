"""The CR estate: custom code, reports, workflows, integrations, configuration and J2X output.

Each item also records its expected decision. Those values go only to the answer key and
never into the estate tables that agents and the UI read.
"""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from data.generator.common import (
    CASE_ID,
    DORMANT_NL,
    FIXTURES,
    NL,
    UK,
    US,
    WINDOW_END,
    WINDOW_START,
    Table,
    compact_json,
    random_date,
    rng,
)

RETIRE = "retire"
STANDARD = "replace_standard"
EXTENSION = "rebuild_extension"
KEEP = "keep_repoint"
GAP = "product_gap"


@dataclass
class Item:
    item_id: str
    item_type: str
    name: str
    subtype: str
    module: str | None
    owner: str | None
    documented: bool
    frequency: str | None
    direct_db_write: bool = False
    definition: dict[str, Any] = field(default_factory=dict)
    source_text: str | None = None
    events: list[tuple[date, int, str]] = field(default_factory=list)
    default_last_used: date | None = None
    expected_outcome: str | None = None
    expected_action: str | None = None
    expected_state: str = "proposed"
    requires_customer: bool = False
    merge_group: str | None = None
    planted_issue: str | None = None
    note: str | None = None


OWNERS = ["Finance systems", "Billing team", "Group reporting", "Project controls", "Procurement office",
          "Credit control", "Finance operations"]

# Title, kind, module, expected outcome, frequency, tables read, tables written
CODE_ITEMS = [
    ("Invoice number prefix by office", "scripted_rule", "billing", STANDARD, "on_event", ["office"], []),
    ("Project code format check", "scripted_rule", "projects", STANDARD, "on_event", ["project"], []),
    ("Purchase order number sequence", "scripted_rule", "procurement", STANDARD, "on_event", ["po_header"], []),
    ("Expense mileage rate lookup", "scripted_rule", "time_expenses", STANDARD, "on_event", ["zz_mileage_rate"], []),
    ("Timesheet minimum hours warning", "scripted_rule", "time_expenses", STANDARD, "on_event", ["timesheet_line"], []),
    ("Client credit limit warning", "scripted_rule", "financials", STANDARD, "on_event", ["customer"], []),
    ("Supplier duplicate name warning", "scripted_rule", "procurement", STANDARD, "on_event", ["supplier"], []),
    ("Cost centre required on journals", "scripted_rule", "financials", STANDARD, "on_event", ["journal_line"], []),
    ("Project end date reminder", "server_process", "projects", STANDARD, "weekly", ["project"], []),
    ("Unsubmitted timesheet reminder", "server_process", "time_expenses", STANDARD, "weekly", ["timesheet_line"], []),
    ("Payment run file naming", "scripted_rule", "financials", STANDARD, "monthly", ["payment_run"], []),
    ("Invoice email subject builder", "scripted_rule", "billing", STANDARD, "on_event", ["invoice"], []),
    ("Expense receipt required flag", "custom_field", "time_expenses", STANDARD, "on_event", ["expense_line"], []),
    ("Client sector field", "custom_field", "financials", STANDARD, "on_event", ["customer"], []),
    ("Project sponsor field", "custom_field", "projects", STANDARD, "on_event", ["project"], []),
    ("Supplier category field", "custom_field", "procurement", STANDARD, "on_event", ["supplier"], []),
    ("Purchase requisition default buyer", "scripted_rule", "procurement", STANDARD, "on_event", ["po_header"], []),
    ("Credit note reason list", "custom_table", "billing", STANDARD, "on_event", ["zz_credit_reason"], []),
    ("Office address block on invoices", "custom_table", "billing", STANDARD, "monthly", ["zz_office_block"], []),

    ("Legacy Scala import mapping", "custom_table", "financials", RETIRE, "none", ["zz_scala_map"], []),
    ("2015 office move recharge", "server_process", "financials", RETIRE, "none", ["zz_move_recharge"], []),
    ("Old expense card loader", "server_process", "time_expenses", RETIRE, "none", ["zz_card_stage"], []),
    ("Euro conversion helper", "scripted_rule", "financials", RETIRE, "none", ["zz_euro_conv"], []),
    ("Timesheet paper form export", "server_process", "time_expenses", RETIRE, "none", ["timesheet_line"], []),
    ("Pre-CR menu shortcut table", "custom_table", "financials", RETIRE, "none", ["zz_menu_short"], []),
    ("Former partner fee split", "custom_table", "billing", RETIRE, "none", ["zz_fee_split_old"], []),
    ("Fax remittance sender", "server_process", "financials", RETIRE, "none", ["payment_run"], []),
    ("Project closure checklist v1", "scripted_rule", "projects", RETIRE, "none", ["project"], []),
    ("Test client flag", "custom_field", "financials", RETIRE, "none", ["customer"], []),
    ("Archived office codes", "custom_table", "financials", RETIRE, "none", ["zz_office_old"], []),
    ("Supplier fax number field", "custom_field", "procurement", RETIRE, "none", ["supplier"], []),
    ("Budget upload 2018 format", "server_process", "financials", RETIRE, "none", ["zz_budget_18"], []),
    ("Merged entity recode list", "custom_table", "financials", RETIRE, "none", ["zz_recode"], []),
    ("Old intranet time feed", "server_process", "time_expenses", RETIRE, "none", ["zz_intranet_time"], []),
    ("Staff lunch allowance rule", "scripted_rule", "time_expenses", RETIRE, "none", ["expense_line"], []),
    ("Client gift register field", "custom_field", "financials", RETIRE, "none", ["customer"], []),

    ("Milestone billing trigger", "server_process", "billing", EXTENSION, "nightly", ["project", "milestone"], ["billing_line"]),
    ("Disbursement mark-up by client", "scripted_rule", "billing", EXTENSION, "on_event", ["zz_markup"], ["billing_line"]),
    ("Fixed fee revenue spreading", "server_process", "billing", EXTENSION, "monthly", ["project"], ["journal_line"]),
    ("Intercompany time recharge", "server_process", "financials", EXTENSION, "monthly", ["timesheet_line"], ["journal_line"]),
    ("Partner share of fees allocation", "server_process", "billing", EXTENSION, "monthly", ["zz_fee_split"], ["journal_line"]),
    ("Subcontractor self-billing", "server_process", "procurement", EXTENSION, "weekly", ["timesheet_line"], ["ap_invoice"]),
    ("Purchase order budget block", "scripted_rule", "procurement", EXTENSION, "on_event", ["budget"], ["po_header"]),
    ("Project margin alert hold", "scripted_rule", "projects", EXTENSION, "on_event", ["project"], ["project"]),
    ("Client rate card expiry hold", "server_process", "billing", EXTENSION, "nightly", ["zz_rate_expiry"], ["project"]),
    ("Retainer drawdown ledger", "custom_table", "billing", EXTENSION, "on_event", ["zz_retainer"], ["zz_retainer"]),
    ("Expense policy limit enforcement", "scripted_rule", "time_expenses", EXTENSION, "on_event", ["zz_exp_limit"], ["expense_line"]),

    ("Lockup days calculation view", "custom_table", "financials", KEEP, "on_event", ["invoice", "wip_item"], []),
    ("Partner dashboard query", "custom_table", "projects", KEEP, "on_event", ["project", "wip_item"], []),
    ("Pipeline to forecast view", "custom_table", "projects", KEEP, "on_event", ["zz_forecast_view"], []),
    ("Resource demand view", "custom_table", "projects", KEEP, "on_event", ["project"], []),
    ("Client profitability view", "custom_table", "billing", KEEP, "on_event", ["invoice", "project"], []),
    ("Budget holder lookup view", "custom_table", "procurement", KEEP, "on_event", ["budget"], []),
    ("Open purchase commitments view", "custom_table", "procurement", KEEP, "on_event", ["po_header"], []),
    ("Debtor contact history view", "custom_table", "financials", KEEP, "on_event", ["customer"], []),
    ("Service line revenue view", "custom_table", "financials", KEEP, "on_event", ["invoice"], []),
    ("Timesheet approval queue view", "custom_table", "time_expenses", KEEP, "on_event", ["timesheet_line"], []),

    ("Retention billing on fixed fee work", "server_process", "billing", GAP, "monthly", ["project"], ["billing_line"]),
    ("Multi-currency rate card by client", "custom_table", "billing", GAP, "on_event", ["zz_rate_multi"], ["billing_line"]),
    ("Partner approval on billing write-offs", "scripted_rule", "billing", GAP, "on_event", ["billing_line"], ["billing_line"]),
    ("Time capture against framework call-offs", "custom_table", "time_expenses", GAP, "on_event", ["zz_calloff"], ["timesheet_line"]),
]

REPORT_SUBJECTS = [
    "Debtors by region", "Creditors by cost centre", "Project margin", "Fee income by office",
    "Timesheet exceptions", "Expense claims by client", "Purchase order ageing", "Supplier spend",
    "Recharge summary", "Budget vs actual", "Disbursements listing", "Client credit notes", "Lockup days",
    "Invoice run check", "Partner fee share", "Cost centre summary", "Unbilled time",
    "Intercompany recharge", "Accruals listing", "Prepayments listing",
]
RETIRE_FORMS = ["{} (old)", "{} v1", "{} - 2016 layout", "Copy of {}", "{} - test"]
MERGE_GROUPS = [
    ("Aged debtors", 6), ("Fee income", 5), ("Project profitability", 5), ("Supplier spend analysis", 4),
    ("Lockup", 4), ("Unbilled WIP", 4), ("Expense claims analysis", 4), ("Timesheet compliance", 3),
    ("Budget variance", 3),
]
MERGE_QUALIFIERS = ["by client", "by office", "by partner", "UK only", "monthly", "v2"]
STANDARD_REPORTS = [
    "Aged receivables", "Aged payables", "Trial balance", "General ledger detail", "Customer statement",
    "Supplier statement", "Project status", "Project transactions", "Invoice register", "Payment proposal",
    "Purchase order status", "Goods received not invoiced", "Expense report status", "Timesheet status",
    "Cash flow summary", "VAT return summary", "Budget overview", "Fixed asset register",
    "Journal listing", "Bank reconciliation", "Customer master list", "Supplier master list",
    "Cost centre overview", "Currency revaluation",
]
REBUILD_REPORTS = [
    "Partner monthly pack", "Client contribution by sector", "Board KPI pack", "Fixed fee overrun watchlist",
    "Bid cost recovery", "Service line margin bridge", "Rate realisation by grade", "Forecast to complete",
    "Secondment recharge analysis", "Client concentration", "Associate cost tracker",
    "Engagement letter expiry", "Milestone billing forecast", "Sustainability spend disclosure",
    "Revenue by sector and office",
]
REPORT_TYPES = ["enquiry", "spreadsheet_addin", "report_layout"]
REPORT_MODULES = ["financials", "billing", "projects", "time_expenses", "procurement"]
COLUMN_POOL = ["client", "office", "partner", "project", "service_line", "period", "currency", "value",
               "budget", "variance", "hours", "cost", "margin", "days", "supplier", "status"]
TABLE_POOL = ["invoice", "project", "wip_item", "gl_balance", "ap_invoice", "po_header", "timesheet_line",
              "expense_line", "budget"]

WORKFLOWS = [
    ("WF-001", "PO approval, standard", "purchase", 6840, "manager_then_budget_holder", UK,
     ["Line manager", "Budget holder"], STANDARD, None),
    ("WF-002", "Expense approval, standard", "expense", 14220, "manager_only", UK,
     ["Line manager"], STANDARD, None),
    ("WF-003", "PO approval, high value", "purchase", 412, "budget_holder_then_finance", UK,
     ["Budget holder", "Finance director"], STANDARD, None),
    ("WF-004", "PO approval, IT purchases", "purchase", 96, "manager_then_budget_holder", UK,
     ["Line manager", "IT budget holder"], STANDARD, "merge_into:WF-001"),
    ("WF-005", "Expense approval, partners", "expense", 380, "manager_only", UK,
     ["Managing partner"], STANDARD, "merge_into:WF-002"),
    ("WF-006", "PO approval, NL", "purchase", 2, "manager_then_budget_holder", DORMANT_NL,
     ["Line manager", "Director NL"], RETIRE, None),
    ("WF-007", "Expense approval, rechargeable", "expense", 210, "manager_only", US,
     ["Project manager"], STANDARD, "merge_into:WF-002"),
    ("WF-008", "PO approval, subcontractors", "purchase", 148, "budget_holder_then_finance", NL,
     ["Budget holder", "Finance controller"], STANDARD, "merge_into:WF-003"),
    ("WF-009", "Expense approval, overseas travel", "expense", 74, "manager_only", UK,
     ["Line manager"], STANDARD, "merge_into:WF-002"),
]

INTEGRATIONS = [
    ("INT-01", "Banking payments file", "outbound", "Bank portal", ["payment_run"], []),
    ("INT-02", "Bank statement import", "inbound", "Bank portal", [], ["bank_statement"]),
    ("INT-03", "Corporate card feed", "inbound", "Card provider", [], ["expense_line"]),
    ("INT-04", "CRM client master", "inbound", "CRM", [], ["customer"]),
    ("INT-05", "CRM opportunity feed", "inbound", "CRM", [], ["zz_pipeline"]),
    ("INT-06", "Data warehouse extract", "outbound", "Data warehouse", ["gl_balance", "invoice"], []),
    ("INT-07", "HR leaver notification", "inbound", "HR system", [], ["zz_leaver_flag"]),
    ("INT-08", "Travel booking feed", "inbound", "Travel provider", [], ["expense_line"]),
    ("INT-09", "Client rate card feed", "inbound", "Contract system", [], ["zz_rate_override"]),
    ("INT-10", "E-invoicing gateway", "outbound", "E-invoicing network", ["invoice"], []),
    ("INT-11", "Purchase catalogue punch-out", "inbound", "Supplier catalogue", [], ["po_header"]),
    ("INT-12", "Consolidation system", "outbound", "Consolidation system", ["gl_balance"], []),
    ("INT-13", "Document archive", "outbound", "Document store", ["invoice"], []),
    ("INT-14", "Resource planning sync", "inbound", "Resource planner", [], ["project"]),
]

CONFIG_ITEMS = [
    ("CF-201", "Chart of accounts mapping"), ("CF-202", "Cost centre mapping"), ("CF-203", "VAT code mapping"),
    ("CF-204", "Service line values"), ("CF-205", "Payment terms"), ("CF-206", "Currency codes"),
    ("CF-207", "Revaluation settings"), ("CF-208", "Invoice layouts"), ("CF-209", "Project types"),
    ("CF-210", "Expense types"), ("CF-211", "Number series"), ("CF-212", "Period calendar"),
]


def _usage(r, frequency: str, entity: str = UK) -> list[tuple[date, int, str]]:
    """Events inside the 12-month window, oldest first."""
    days = (WINDOW_END - WINDOW_START).days + 1
    if frequency == "nightly":
        return [(WINDOW_START + timedelta(days=i), 1, entity) for i in range(days)]
    if frequency == "daily":
        return [(WINDOW_START + timedelta(days=i), 1, entity) for i in range(days)
                if (WINDOW_START + timedelta(days=i)).weekday() < 5]
    if frequency == "weekly":
        return [(WINDOW_START + timedelta(days=4 + 7 * i), 1, entity) for i in range(52)]
    if frequency == "monthly":
        return [(_month_start(i), 1, entity) for i in range(12)]
    if frequency == "on_event":
        return [(_month_start(i), r.randint(40, 900), entity) for i in range(12)]
    return []


def _month_start(offset: int) -> date:
    month = WINDOW_START.month + offset
    return date(WINDOW_START.year + (month - 1) // 12, (month - 1) % 12 + 1, 1)


def _code_stub(item_id: str, title: str, kind: str, reads: list[str], writes: list[str]) -> str:
    if kind == "custom_table":
        columns = ",\n    ".join(["id bigint", "code varchar(25)", "value varchar(100)"])
        return f"-- {item_id}: {title}\nCREATE TABLE {reads[0] if reads[0].startswith('zz_') else 'zz_view_src'} (\n    {columns}\n);\n"
    if kind == "custom_field":
        return f"-- {item_id}: {title}\nALTER TABLE {reads[0]} ADD zz_{item_id[3:]}_value varchar(50);\n"
    class_name = "".join(word.capitalize() for word in item_id.split("-"))
    lines = [f"// {item_id}: {title}", f"public class {class_name} : IServerJob", "{",
             "    public void Run(DateTime runDate)", "    {"]
    lines += [f'        var {table.removeprefix("zz_")} = Api.Read("{table}", runDate);' for table in reads]
    lines += [f'        Api.Update("{table}", Rules.Apply(runDate));' for table in writes]
    return "\n".join([*lines, "    }", "}", ""])


def generate_code_items() -> list[Item]:
    r = rng("code")
    numbers = iter(n for n in range(1, 65) if n not in (14, 37, 41))
    items = []
    for title, kind, module, outcome, frequency, reads, writes in CODE_ITEMS:
        item_id = f"CC-{next(numbers):03d}"
        items.append(Item(
            item_id=item_id, item_type="CC", name=title, subtype=kind, module=module, owner=r.choice(OWNERS),
            documented=True, frequency=frequency,
            definition={"tables_read": reads, "tables_written": writes},
            source_text=_code_stub(item_id, title, kind, reads, writes),
            events=_usage(r, frequency),
            default_last_used=random_date(r, date(2019, 1, 1), date(2025, 6, 30)) if frequency == "none" else None,
            expected_outcome=outcome, requires_customer=outcome == RETIRE,
        ))

    code = FIXTURES / "code"
    items.append(Item(
        item_id="CC-014", item_type="CC", name="Billing adjust writer", subtype="server_process", module="billing",
        owner=None, documented=False, frequency="nightly", direct_db_write=True,
        definition={"job_name": "BILLADJ_NIGHTLY",
                    "tables_read": ["zz_billing_adjust_queue", "billing_line", "project", "zz_rate_override",
                                    "zz_writedown_approval"],
                    "tables_written": ["billing_line", "zz_billing_adjust_queue", "zz_writedown_approval"]},
        source_text=(code / "CC-014.cs").read_text(encoding="utf-8"),
        events=_usage(r, "nightly"), expected_outcome=EXTENSION, expected_action="standard_plus_one_extension",
        planted_issue="M1,M2",
        note="Undocumented and unowned, but readable and in daily use, so it gets a decision. M10 does not apply.",
    ))
    items.append(Item(
        item_id="CC-037", item_type="CC", name="Proc7", subtype="server_process", module=None,
        owner=None, documented=False, frequency="monthly",
        definition={"job_name": "PROC7", "tables_read": ["zz_tmp_x1"], "tables_written": []},
        source_text=(code / "CC-037.cs").read_text(encoding="utf-8"),
        events=_usage(r, "monthly"), expected_state="held", requires_customer=True, planted_issue="M10",
        note="Purpose cannot be established from the code. Needs a customer interview.",
    ))
    items.append(Item(
        item_id="CC-041", item_type="CC", name="Timesheet period lock stamp", subtype="server_process",
        module="time_expenses", owner="Finance systems", documented=True, frequency="weekly",
        direct_db_write=True,
        definition={"job_name": "TSLOCK_WEEKLY", "tables_read": ["time_period"], "tables_written": ["timesheet_line"]},
        source_text=(code / "CC-041.cs").read_text(encoding="utf-8"),
        events=_usage(r, "weekly"), expected_outcome=EXTENSION,
    ))
    return sorted(items, key=lambda item: item.item_id)


def _report_definition(r, report_type: str, columns: list[str] | None = None) -> dict[str, Any]:
    return {
        "columns": columns or r.sample(COLUMN_POOL, r.randint(4, 8)),
        "filters": [r.choice(["period = :period", "entity = :entity", "office = :office"])],
        "layout_last_changed": random_date(r, date(2012, 1, 1), date(2025, 12, 31)).isoformat(),
        "report_type": report_type,
        "tables": r.sample(TABLE_POOL, r.randint(1, 3)),
    }


def generate_reports() -> list[Item]:
    r = rng("reports")
    pool = [n for n in range(1, 149) if n not in (31, 58, 77, 84, 112)]
    r.shuffle(pool)
    numbers = iter(pool)

    def build(name: str, frequency: str, **expected: Any) -> Item:
        report_type = r.choice(REPORT_TYPES)
        columns = expected.pop("columns", None)
        last_used = expected.pop("default_last_used", None)
        events = expected.pop("events", None)
        item_id = expected.pop("item_id", None) or f"RP-{next(numbers):03d}"
        return Item(
            item_id=item_id, item_type="RP", name=name, subtype=report_type, module=r.choice(REPORT_MODULES),
            owner=r.choice(OWNERS), documented=True, frequency=frequency,
            definition=_report_definition(r, report_type, columns),
            events=events if events is not None else _usage(r, frequency), default_last_used=last_used, **expected,
        )

    items: list[Item] = []

    # 61 retire: 49 unused in the window, 12 in the low-use band, including one decoy keyword match.
    names = [form.format(subject) for subject in REPORT_SUBJECTS for form in RETIRE_FORMS]
    r.shuffle(names)
    names = names[:59]
    items.append(build("Old utilisation v2", "none", item_id="RP-031", expected_outcome=RETIRE,
                       requires_customer=True, default_last_used=date(2023, 2, 14)))
    items.append(build("Old tax code listing v1", "none", item_id="RP-058", expected_outcome=RETIRE,
                       requires_customer=True, default_last_used=date(2021, 7, 2),
                       note="Decoy: the keyword match on 'tax' is reasonable, but it is safe to retire."))
    for i, name in enumerate(names):
        low_use = i < 12
        events = [(random_date(r, WINDOW_START, WINDOW_END), 1, UK) for _ in range(r.randint(1, 2))] if low_use else []
        items.append(build(
            name, "low" if low_use else "none", events=sorted(events), expected_outcome=RETIRE,
            requires_customer=True, default_last_used=random_date(r, date(2018, 1, 1), date(2025, 9, 30)),
        ))

    # 38 merged into 9.
    for base, size in MERGE_GROUPS:
        group = base.lower().replace(" ", "-")
        columns = r.sample(COLUMN_POOL, 6)
        for i in range(size):
            variation = [*columns[:5], r.choice(COLUMN_POOL)]
            items.append(build(
                f"{base} {MERGE_QUALIFIERS[i]}", r.choice(["monthly", "weekly"]), columns=sorted(set(variation)),
                expected_outcome=KEEP, expected_action="merge_survivor" if i == 0 else "merge_into",
                merge_group=group,
            ))

    # 31 replaced by a standard report.
    for i in range(31):
        standard = STANDARD_REPORTS[i % len(STANDARD_REPORTS)]
        suffix = " (custom)" if i < len(STANDARD_REPORTS) else " - office view"
        items.append(build(f"{standard}{suffix}", r.choice(["monthly", "weekly"]), expected_outcome=STANDARD))

    # 18 rebuilt, three of them hand-written.
    for name in REBUILD_REPORTS:
        items.append(build(name, r.choice(["monthly", "weekly"]), expected_outcome=KEEP, expected_action="rebuild"))
    fixtures = FIXTURES / "reports"
    items.append(Item(
        item_id="RP-077", item_type="RP", name="WIP ageing by partner", subtype="spreadsheet_addin", module="projects",
        owner="Project controls", documented=True, frequency="weekly",
        definition=json.loads((fixtures / "RP-077.json").read_text(encoding="utf-8")),
        events=_usage(r, "weekly"), expected_outcome=KEEP, expected_action="rebuild", planted_issue="M4",
    ))
    items.append(Item(
        item_id="RP-084", item_type="RP", name="Utilisation by grade", subtype="report_layout", module="projects",
        owner="Group reporting", documented=True, frequency="monthly",
        definition=json.loads((fixtures / "RP-084.json").read_text(encoding="utf-8")),
        events=_usage(r, "monthly"), expected_outcome=KEEP, expected_action="rebuild",
    ))
    items.append(Item(
        item_id="RP-112", item_type="RP", name="Year-end audit pack", subtype="report_layout", module="financials",
        owner="Group reporting", documented=True, frequency="annual",
        definition=json.loads((fixtures / "RP-112.json").read_text(encoding="utf-8")),
        events=[(date(2026, 1, 14), 1, UK)], expected_outcome=KEEP, expected_action="rebuild", expected_state="held",
        requires_customer=True, planted_issue="M3",
    ))
    return sorted(items, key=lambda item: item.item_id)


def generate_workflows() -> list[Item]:
    r = rng("workflows")
    items = []
    for item_id, name, flow, annual, rule, entity, steps, outcome, action in WORKFLOWS:
        share = annual // 12
        events = [(_month_start(i), share, entity) for i in range(12)] if annual >= 12 else []
        if events:
            events[-1] = (events[-1][0], annual - share * 11, entity)
        else:
            events = [(date(2026, 2, 9), 1, entity), (date(2026, 6, 23), annual - 1, entity)]
        planted = "M5" if item_id == "WF-006" else None
        items.append(Item(
            item_id=item_id, item_type="WF", name=name, subtype=flow, module="procurement" if flow == "purchase" else "time_expenses",
            owner=r.choice(OWNERS), documented=True, frequency="on_event",
            definition={"approval_steps": steps, "enforced_rule": rule, "entity": entity},
            events=events, expected_outcome=outcome, expected_action=action, requires_customer=True,
            planted_issue=planted,
        ))
    return items


def generate_integrations() -> list[Item]:
    r = rng("integrations")
    return [
        Item(item_id=item_id, item_type="INT", name=name, subtype=direction, module=None, owner=r.choice(OWNERS),
             documented=True, frequency="daily",
             definition={"external_system": system, "tables_read": reads, "tables_written": writes})
        for item_id, name, direction, system, reads, writes in INTEGRATIONS
    ]


def generate_config_items() -> list[Item]:
    r = rng("config")
    planted = {"CF-203": "M6", "CF-204": "M9"}
    return [
        Item(item_id=item_id, item_type="CF", name=name, subtype="configuration", module="financials", owner=r.choice(OWNERS),
             documented=True, frequency=None, definition={"area": name}, expected_outcome=STANDARD,
             planted_issue=planted.get(item_id))
        for item_id, name in CONFIG_ITEMS
    ]


def generate_j2x(items: list[Item]) -> tuple[Table, dict[str, Any]]:
    """Simulated, because the real J2X output format is an open question for Unit4."""
    r = rng("j2x")
    coverage = {"CC": 0.62, "RP": 0.70, "WF": 1.0, "INT": 1.0, "CF": 0.5}
    rows = []
    for item in items:
        if r.random() >= coverage[item.item_type] and item.item_id != "CC-014":
            continue
        complexity = "high" if item.direct_db_write else r.choice(["low", "low", "medium"])
        rows.append((item.item_id, complexity, f"{item.name}: {item.subtype.replace('_', ' ')} in {item.module or 'an unknown module'}."))
    by_type: dict[str, int] = {}
    for item_id, *_ in rows:
        key = item_id.split("-")[0]
        by_type[key] = by_type.get(key, 0) + 1
    report = {
        "assessment_date": "2026-09-14",
        "customer": "Ardleigh Consulting Group",
        "explained_items_by_type": by_type,
        "readiness": "amber",
        "scope_note": "Readiness assessment and customisation explanation only. No execution steps.",
        "simulated": True,
    }
    return (["item_id", "complexity", "summary"], rows), report


MISSED_STANDARD = {"Purchase requisition default buyer"}
LOW_CONFIDENCE = {"Credit note reason list"}
STANDARD_FEATURES = {
    "scripted_rule": "Standard field validation rules",
    "custom_field": "Standard flexible fields",
    "custom_table": "Standard value lists",
    "server_process": "Standard scheduled notifications",
}


def _summary(item: Item) -> str:
    if item.item_type == "RP":
        return f"{item.subtype.replace('_', ' ').capitalize()} over {', '.join(item.definition['tables'])}."
    if item.item_type == "WF":
        return f"Approval by {' then '.join(item.definition['approval_steps'])}."
    if item.item_type == "CF":
        return f"Configuration area: {item.name}."
    reads, writes = item.definition["tables_read"], item.definition["tables_written"]
    text = f"{item.subtype.replace('_', ' ').capitalize()}. Reads {', '.join(reads)}."
    return f"{text} Writes {', '.join(writes)}." if writes else text


def agent_signals(items: list[Item]) -> Table:
    """Hand-authored stand-in for the code-reading agent, which needs a model. Reports and workflows
    are not here: engines.agents.analysis works those out from the estate itself. One miss is
    deliberate, so decision quality is measured rather than perfect.
    """
    heroes = json.loads((FIXTURES / "agent_cache" / "hero_analysis.json").read_text(encoding="utf-8"))
    r = rng("signals")
    rows = []
    for item in sorted(items, key=lambda i: i.item_id):
        if item.item_type == "INT":
            continue
        hero = heroes.get(item.item_id, {})
        feature = None
        if item.expected_outcome == STANDARD and item.name not in MISSED_STANDARD:
            if item.item_type == "CF":
                feature = "ERPx standard configuration"
            elif item.item_type == "CC":
                feature = STANDARD_FEATURES[item.subtype]
        confidence = None
        if feature:
            confidence = r.randint(60, 68) if item.name in LOW_CONFIDENCE else r.randint(82, 96)
        rows.append((
            item.item_id, hero.get("summary", _summary(item)), hero.get("purpose_known", True), feature, confidence,
            None, hero.get("action_note"), hero.get("proposal_note"), hero.get("question"),
            compact_json(hero["conflict"]) if "conflict" in hero else None, compact_json(hero.get("evidence", [])),
        ))
    return (["item_id", "summary", "purpose_known", "standard_feature", "standard_confidence", "merge_target",
             "action_note", "proposal_note", "question", "conflict", "evidence"], rows)


def estate_rows(items: list[Item], explained: set[str]) -> tuple[Table, Table]:
    item_rows = []
    event_rows = []
    for item in sorted(items, key=lambda i: i.item_id):
        last_used = max((event[0] for event in item.events), default=item.default_last_used)
        item_rows.append((
            item.item_id, CASE_ID, item.item_type, item.name, item.subtype, item.module, item.owner, item.documented,
            item.item_id in explained, item.frequency, sum(event[1] for event in item.events), last_used,
            item.direct_db_write, compact_json(item.definition), item.source_text,
        ))
        event_rows += [(item.item_id, *event) for event in item.events]
    return (
        (["item_id", "case_id", "item_type", "name", "subtype", "module", "owner", "documented", "j2x_explained",
          "frequency", "usage_12m", "last_used", "direct_db_write", "definition", "source_text"], item_rows),
        (["item_id", "event_date", "event_count", "entity_code"], event_rows),
    )


def expected_rows(items: list[Item]) -> Table:
    rows = [
        (item.item_id, item.expected_outcome, item.expected_action, item.expected_state, item.requires_customer,
         item.merge_group, item.planted_issue, item.note)
        for item in sorted(items, key=lambda i: i.item_id) if item.item_type != "INT"
    ]
    return (["item_id", "expected_outcome", "expected_action", "expected_state", "requires_customer", "merge_group",
             "planted_issue", "note"], rows)


def generate_precedents() -> Table:
    """Decisions from other fictional customers, so that mapping memory is not empty in a one-customer demo."""
    gaps = [item[0] for item in CODE_ITEMS if item[3] == GAP]
    rows = []
    number = 1
    for pattern in gaps:
        for label in "BCDEFG":
            rows.append((f"PR-{number:03d}", pattern, f"Customer {label} (sandbox)", EXTENSION, "approved", True))
            number += 1
    for pattern, outcome, status in [
        ("Nightly job writing billing adjustments", EXTENSION, "approved"),
        ("Unused report older than three years", RETIRE, "approved"),
        ("Near-duplicate aged debtors report", KEEP, "approved"),
        ("Annual statutory report with low usage", RETIRE, "rejected"),
    ]:
        for label in "BC":
            rows.append((f"PR-{number:03d}", pattern, f"Customer {label} (sandbox)", outcome, status, True))
            number += 1
    return ["precedent_id", "pattern", "source_customer", "outcome", "review_status", "synthetic"], rows


def standard_catalogue() -> dict[str, Any]:
    return {
        "note": "Reference list, pending Unit4's ERPx standard content.",
        "reports": sorted(STANDARD_REPORTS),
    }
