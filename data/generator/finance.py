"""CR finance data for the UK entity: masters, open items, WIP and the trial balance.

Amounts are integer minor units. Planted issues M6, M7, M8 and M9 are created here so that
they surface when the data is migrated, rather than being written into the check results.
"""

from collections import defaultdict
from datetime import date, timedelta
from random import Random

from data.generator.common import (
    AP_CONTROL,
    AR_CONTROL,
    BANK,
    FX_RATES,
    M6_ACCOUNT_A,
    M6_ACCOUNT_B,
    M7_DIFFERENCE_MINOR,
    M9_DUPLICATE,
    M9_VALUE,
    PERIODS,
    WINDOW_END,
    WINDOW_START,
    WIP_CONTROL,
    Table,
    multiply_rate,
    random_date,
    rng,
    round_rate,
)

NAME_STEMS = (
    "Alderholt Ashcombe Barrowden Beckworth Birchanger Blythburgh Bourton Brackley Bramfield Brockhurst "
    "Calverleigh Carnforth Chalford Chilworth Claydon Coldharbour Cranmere Dalwood Denholme Dunsmore "
    "Eastleach Edgecote Elmstead Fairlight Farnsfield Fenwick Fordingley Garsdale Glenrothby Goathurst "
    "Halstock Hambleton Harbury Hartwell Hazelbury Holmbridge Hurstwick Ickford Kelmarsh Kingsmead "
    "Langford Larkfield Lindhurst Lowick Marlstone Melbury Merrington Milverton Netherby Northleach "
    "Oakhanger Orwell Oxenhope Pendleford Pickwell Quarrendon Radwell Ravensden Redmarley Rushbrooke "
    "Saltwick Sandleigh Shalford Silverstone Stanwick Stoneleigh Swinford Tarrant Thornbury Tilshead "
    "Upwood Wadhurst Walkford Warbleton Westerleigh Whitwell Wickford Winterbourne Wolvercote Yarcombe"
).split()
CUSTOMER_SECTORS = (
    "Logistics Energy Foods Utilities Housing Pharma Retail Marine Aerospace Insurance Media Telecoms "
    "Education Water Rail Mutual Foundation Trust Council Laboratories"
).split()
SUPPLIER_SECTORS = (
    "Facilities Software Print Couriers Catering Recruitment Associates Travel Stationery Cleaning "
    "Training Legal Translation Hosting Security Events"
).split()
SUFFIXES = ["Ltd", "Limited", "plc", "Group", "Holdings", "LLP"]
GIVEN_NAMES = (
    "Avery Bryn Cameron Dara Eden Finley Greer Harley Indigo Jules Kit Lennon Morgan Noor Oakley Parker "
    "Quinn Reese Sasha Tatum Umi Vesper Wren Yael Zion"
).split()
FAMILY_NAMES = (
    "Aldous Barrowclough Cresswell Dunmore Elsworth Fairbrother Greatorex Hathersage Ingleby Jessop "
    "Kirkbride Lockwood Maplethorpe Northcott Ormerod Pemberton Quickenden Rawcliffe Sedgewick "
    "Thackeray Underhill Verrall Whitcombe Yeadon"
).split()
GRADES = ["Partner", "Director", "Senior Manager", "Manager", "Senior Consultant", "Consultant", "Analyst"]
SERVICE_LINES = [
    ("STRAT", "Strategy"),
    ("OPSEX", "Operational excellence"),
    ("TRANS", "Business transformation"),
    ("DIGIT", "Digital and technology"),
    ("DATAI", "Data and analytics"),
    ("PROCU", "Procurement advisory"),
    ("FINAD", "Finance advisory"),
    ("PEOPL", "People and change"),
    ("SUSTA", "Sustainability"),
    ("REGUL", "Regulatory advisory"),
    ("DEALS", "Deal advisory"),
    ("PUBSE", "Public sector"),
    ("HEALT", "Health and care"),
    (M9_VALUE, "Risk advisory"),
]
REGIONS = ["LON", "MAN", "EDI", "BIR", "BRS", "AMS", "ROT", "NYC", "BOS"]
ACCOUNT_PLAN = [
    (
        "asset",
        100000,
        380,
        [
            "Bank",
            "Trade debtors",
            "Accrued income",
            "Prepayments",
            "Fixed assets",
            "Staff loans",
            "Client deposits held",
            "Intercompany receivable",
        ],
    ),
    (
        "liability",
        200000,
        320,
        [
            "Trade creditors",
            "Accruals",
            "Deferred income",
            "VAT control",
            "Corporation charge",
            "Intercompany payable",
            "Provisions",
        ],
    ),
    ("equity", 300000, 40, ["Share capital", "Retained earnings", "Reserves"]),
    (
        "revenue",
        400000,
        360,
        [
            "Consulting fees",
            "Fixed fee income",
            "Recharged expenses",
            "Training income",
            "Licence income",
            "Other income",
        ],
    ),
    (
        "expense",
        500000,
        1212,
        [
            "Subcontractor costs",
            "Travel",
            "Accommodation",
            "Subsistence",
            "Software",
            "Premises",
            "Marketing",
            "Insurance",
            "Professional fees",
            "Recruitment",
            "Training",
            "Communications",
            "Depreciation",
            "Bank charges",
        ],
    ),
]
QUALIFIERS = [
    "UK",
    "Netherlands",
    "United States",
    "London",
    "Manchester",
    "Edinburgh",
    "Group",
    "Project",
    "Overhead",
    "Client",
    "Legacy",
    "Current",
    "Prior year",
    "Recoverable",
]
FIXED_ACCOUNTS = {
    BANK: ("Bank - Group current account", "asset", "N0"),
    AR_CONTROL: ("Trade debtors - control", "asset", "N0"),
    WIP_CONTROL: ("Work in progress - control", "asset", "N0"),
    AP_CONTROL: ("Trade creditors - control", "liability", "N0"),
    M6_ACCOUNT_A: ("Consulting fees - standard rated", "revenue", "S20"),
    M6_ACCOUNT_B: ("Consulting fees - exempt training", "revenue", "E0"),
}


def _company_names(r: Random, sectors: list[str], count: int) -> list[str]:
    combos = [f"{stem} {sector} {suffix}" for stem in NAME_STEMS for sector in sectors for suffix in SUFFIXES]
    return r.sample(combos, count)


def generate_accounts() -> tuple[Table, Table, dict[str, str]]:
    r = rng("accounts")
    accounts: dict[str, tuple[str, str, str]] = dict(FIXED_ACCOUNTS)
    for account_type, base, count, stems in ACCOUNT_PLAN:
        for i in range(count):
            code = str(base + (i + 1) * (10 if account_type != "expense" else 200))
            if code in accounts:
                continue
            name = f"{r.choice(stems)} - {r.choice(QUALIFIERS)}"
            vat = {
                "revenue": r.choice(["S20", "S20", "S20", "Z0"]),
                "expense": r.choice(["S20", "S20", "E0", "N0"]),
            }.get(account_type, "N0")
            accounts[code] = (name, account_type, vat)

    account_rows = []
    map_rows = []
    active_types: dict[str, str] = {}
    next_erpx = 10000
    previous: tuple[str, str, str, str] | None = None
    for code in sorted(accounts):
        name, account_type, vat = accounts[code]
        active = code in FIXED_ACCOUNTS or r.random() < 0.93
        account_rows.append((code, name, account_type, vat, active))
        if active:
            active_types[code] = account_type

        mergeable = (
            previous is not None
            and previous[0] not in (M6_ACCOUNT_A, M6_ACCOUNT_B)
            and code != M6_ACCOUNT_A
            and previous[2:] == (account_type, vat)
        )
        if code == M6_ACCOUNT_B:
            assert previous is not None
            erpx = previous[1]
        elif mergeable and r.random() < 0.14:
            assert previous is not None
            erpx = previous[1]
        else:
            erpx = str(next_erpx)
            next_erpx += 5
        map_rows.append((code, erpx))
        previous = (code, erpx, account_type, vat)

    return (
        (["account_code", "name", "account_type", "vat_code", "active"], account_rows),
        (["account_code", "erpx_account"], map_rows),
        active_types,
    )


def generate_dimensions() -> tuple[Table, Table, list[str], list[str]]:
    r = rng("dimensions")
    cost_centres = ["C000"] + [f"C{100 + i}" for i in range(119)]
    rows: list[tuple] = []
    maps: list[tuple] = []
    for value in cost_centres:
        rows.append(("COSTC", value, f"Cost centre {value[1:]}", r.random() < 0.95 or value == "C000"))
        maps.append(("COSTC", value, f"CC-{value[1:]}"))
    service_lines = [code for code, _ in SERVICE_LINES]
    for code, description in SERVICE_LINES:
        rows.append(("SERVLINE", code, description, True))
        maps.append(("SERVLINE", code, code[:4]))
    rows.append(("SERVLINE", M9_DUPLICATE, "Risk advisory", True))
    maps.append(("SERVLINE", M9_DUPLICATE, M9_VALUE[:4]))
    for value in REGIONS:
        rows.append(("REGION", value, f"Region {value}", True))
        maps.append(("REGION", value, value))
    return (
        (["dimension", "value", "description", "active"], rows),
        (["dimension", "value", "erpx_value"], maps),
        cost_centres,
        service_lines,
    )


def generate_parties() -> tuple[Table, Table, list[str], list[str]]:
    r = rng("parties")
    customer_names = _company_names(r, CUSTOMER_SECTORS, 980)
    supplier_names = _company_names(r, SUPPLIER_SECTORS, 1180)
    customers = [
        (f"C{10001 + i}", name, r.choice(["GB", "GB", "GB", "GB", "IE", "NL", "DE", "US"]), r.random() < 0.96)
        for i, name in enumerate(customer_names)
    ]
    suppliers = [
        (f"S{20001 + i}", name, r.choice(["GB", "GB", "GB", "NL", "US"]), r.random() < 0.94)
        for i, name in enumerate(supplier_names)
    ]
    return (
        (["customer_id", "name", "country", "active"], customers),
        (["supplier_id", "name", "country", "active"], suppliers),
        [row[0] for row in customers if row[3]],
        [row[0] for row in suppliers if row[3]],
    )


def generate_resources() -> tuple[Table, Table, list[str]]:
    """Invented partner reference and grade-level utilisation. No HR attributes, no individuals' time."""
    r = rng("resources")
    names = r.sample([f"{g} {f}" for g in GIVEN_NAMES for f in FAMILY_NAMES], 50)
    rows: list[tuple] = []
    # P041 to P046 joined after the RP-077 partner list was last changed in 2022 (M4).
    for i in range(1, 47):
        joined = r.randint(2009, 2021) if i <= 40 else r.randint(2023, 2026)
        rows.append((f"P{i:03d}", names[i - 1], "Partner", True, True, joined))
    for i in range(1, 5):
        rows.append((f"P90{i}", names[45 + i], "Partner", True, False, r.randint(2009, 2014)))
    utilisation = []
    for period in PERIODS:
        for grade, headcount, target in zip(
            GRADES, [46, 74, 130, 210, 260, 180, 90], [0.48, 0.58, 0.66, 0.72, 0.77, 0.80, 0.70], strict=True
        ):
            available = headcount * 150
            billable = int(available * (target + r.uniform(-0.04, 0.04)))
            utilisation.append((period, grade, available, billable))
    return (
        (["partner_code", "display_name", "grade", "is_partner", "active", "joined_year"], rows),
        (["period", "grade", "available_hours", "billable_hours"], utilisation),
        [row[0] for row in rows if row[4]],
    )


def generate_projects(customers: list[str], partners: list[str], service_lines: list[str]) -> Table:
    r = rng("projects")
    rows = []
    services = ["Review", "Programme", "Advisory", "Diagnostic", "Implementation", "Support", "Assurance"]
    specs = [("open", 860), ("closed_with_wip", 14), ("closed", 86)]
    number = 24001
    for kind, count in specs:
        for _ in range(count):
            line = r.choice(service_lines)
            if line == M9_VALUE and r.random() < 0.5:
                line = M9_DUPLICATE
            start = random_date(r, date(2023, 1, 1), date(2026, 8, 31))
            closed = random_date(r, date(2025, 6, 1), date(2026, 9, 30)) if kind != "open" else None
            if closed and closed < start:
                start = closed - timedelta(days=120)
            rows.append(
                (
                    f"PRJ-{number}",
                    f"{r.choice(NAME_STEMS)} {r.choice(services)}",
                    r.choice(customers),
                    r.choice(partners),
                    line,
                    "open" if kind == "open" else "closed",
                    start,
                    closed,
                )
            )
            number += 1
    return (
        [
            "project_id",
            "name",
            "customer_id",
            "partner_code",
            "service_line",
            "status",
            "start_date",
            "closed_date",
        ],
        rows,
    )


def generate_wip(projects: Table) -> Table:
    """WIP on open projects, plus the 14 closed projects that should hold none (M8)."""
    r = rng("wip")
    rows = []
    number = 1
    for project_id, _, _, _, _, status, _, closed in projects[1]:
        if status == "closed" and int(project_id.split("-")[1]) >= 24001 + 860 + 14:
            continue
        for _ in range(r.randint(1, 6) if status == "open" else r.randint(1, 3)):
            hours = r.randint(150, 12000)
            cost = hours * r.randint(45, 140)
            billable = hours * r.randint(110, 320)
            txn_date = closed or random_date(r, date(2026, 3, 1), WINDOW_END)
            rows.append((f"W{number:06d}", project_id, txn_date, hours, cost, billable))
            number += 1
    return ["wip_id", "project_id", "txn_date", "hours_x100", "cost_minor", "billable_minor"], rows


def generate_receivables(customers: list[str], decimals: int) -> Table:
    """Open receivables. Foreign balances are tuned so that revaluing them at a rate held to
    `decimals` places moves the total by exactly the M7 difference.

    Line rounding could account for £15.50 at most, so the cause has to be rate precision.
    """
    r = rng("receivables")
    rows: list[list] = []
    for i in range(3104):
        invoice_date = random_date(r, date(2026, 3, 1), WINDOW_END)
        currency = r.choices(["GBP", "EUR", "USD"], [84, 12, 4])[0]
        amount = int(r.lognormvariate(13.4, 0.9))
        if r.random() < 0.04:
            amount = -amount // 4
        rows.append(
            [
                f"AR{300001 + i}",
                r.choice(customers),
                invoice_date,
                invoice_date + timedelta(days=30),
                currency,
                amount,
            ]
        )

    def line_difference(currency: str, amount: int) -> int:
        if currency == "GBP":
            return 0
        rate = FX_RATES[currency]
        return multiply_rate(amount, round_rate(rate, decimals)) - multiply_rate(amount, rate)

    euro_rows = sorted(
        (row for row in rows if row[4] == "EUR" and row[5] > 0), key=lambda row: (-row[5], row[0])
    )
    rate_gap = 0.000346
    for _ in range(12):
        total = sum(line_difference(row[4], row[5]) for row in rows)
        residual = M7_DIFFERENCE_MINOR - total
        if abs(residual) <= 5:
            break
        step = int(residual / rate_gap / 40)
        for row in euro_rows[:40]:
            row[5] += step

    residual = M7_DIFFERENCE_MINOR - sum(line_difference(row[4], row[5]) for row in rows)
    if residual:
        target = euro_rows[0]
        current = line_difference("EUR", target[5])
        for k in sorted(range(-40000, 40001), key=abs):
            if line_difference("EUR", target[5] + k) - current == residual:
                target[5] += k
                break
    assert sum(line_difference(row[4], row[5]) for row in rows) == M7_DIFFERENCE_MINOR

    return (
        ["item_id", "customer_id", "invoice_date", "due_date", "currency", "amount_cur_minor", "base_minor"],
        [(*row, row[5] if row[4] == "GBP" else multiply_rate(row[5], FX_RATES[row[4]])) for row in rows],
    )


def generate_payables(suppliers: list[str]) -> Table:
    r = rng("payables")
    rows = []
    for i in range(1452):
        invoice_date = random_date(r, date(2026, 6, 1), WINDOW_END)
        currency = r.choices(["GBP", "EUR", "USD"], [95, 3, 2])[0]
        amount = int(r.lognormvariate(11.2, 1.0))
        base = amount if currency == "GBP" else multiply_rate(amount, FX_RATES[currency])
        rows.append(
            (
                f"AP{500001 + i}",
                r.choice(suppliers),
                invoice_date,
                invoice_date + timedelta(days=30),
                currency,
                amount,
                base,
            )
        )
    return [
        "item_id",
        "supplier_id",
        "invoice_date",
        "due_date",
        "currency",
        "amount_cur_minor",
        "base_minor",
    ], rows


def generate_gl(
    active_types: dict[str, str], cost_centres: list[str], service_lines: list[str], closing: dict[str, int]
) -> Table:
    """Monthly movements. Every period nets to zero and control accounts close on their sub-ledgers."""
    r = rng("gl")
    fixed = {BANK, M6_ACCOUNT_A, M6_ACCOUNT_B, *closing}
    candidates = sorted(code for code in active_types if code not in fixed)
    chosen = [*r.sample(candidates, 420), M6_ACCOUNT_A, M6_ACCOUNT_B]
    balances: dict[tuple[str, str, str, str], int] = defaultdict(int)
    combos = {
        code: [(r.choice(cost_centres), r.choice(service_lines)) for _ in range(r.randint(1, 3))]
        for code in chosen
    }
    # Both spellings of the M9 service line carry real balances.
    combos[chosen[0]].append(("C101", M9_VALUE))
    combos[chosen[1]].append(("C102", M9_DUPLICATE))
    combos[chosen[2]].append(("C103", M9_DUPLICATE))

    for period in PERIODS:
        for code in chosen:
            sign = -1 if active_types[code] in ("revenue", "liability", "equity") else 1
            for cost_centre, service_line in combos[code]:
                balances[(code, period, cost_centre, service_line)] += sign * r.randint(5_000, 4_000_000)
        for code, value in closing.items():
            share = int(value / len(PERIODS))
            amount = share if period != PERIODS[-1] else value - share * (len(PERIODS) - 1)
            balances[(code, period, "C000", "STRAT")] += amount
        period_total = sum(v for k, v in balances.items() if k[1] == period)
        balances[(BANK, period, "C000", "STRAT")] -= period_total

    rows = [(*key, value) for key, value in sorted(balances.items())]
    return ["account_code", "period", "cost_centre", "service_line", "amount_minor"], rows


def generate_fx_rates() -> Table:
    return (
        ["currency", "rate_date", "rate_text"],
        [(currency, WINDOW_END, rate) for currency, rate in sorted(FX_RATES.items())],
    )


def generate_finance(fx_rate_decimals: int) -> dict[str, Table]:
    accounts, account_map, active_types = generate_accounts()
    dimensions, dimension_map, cost_centres, service_lines = generate_dimensions()
    customers, suppliers, active_customers, active_suppliers = generate_parties()
    resources, utilisation, active_partners = generate_resources()
    projects = generate_projects(active_customers, active_partners, service_lines)
    wip = generate_wip(projects)
    receivables = generate_receivables(active_customers, fx_rate_decimals)
    payables = generate_payables(active_suppliers)
    closing = {
        AR_CONTROL: sum(row[6] for row in receivables[1]),
        AP_CONTROL: -sum(row[6] for row in payables[1]),
        WIP_CONTROL: sum(row[5] for row in wip[1]),
    }
    return {
        "account": accounts,
        "account_map": account_map,
        "dimension_value": dimensions,
        "dimension_map": dimension_map,
        "customer": customers,
        "supplier": suppliers,
        "resource_reference": resources,
        "utilisation_summary": utilisation,
        "project": projects,
        "wip_item": wip,
        "ar_open_item": receivables,
        "ap_open_item": payables,
        "fx_rate": generate_fx_rates(),
        "gl_balance": generate_gl(active_types, cost_centres, service_lines, closing),
    }


__all__ = ["WINDOW_START", "generate_finance"]
