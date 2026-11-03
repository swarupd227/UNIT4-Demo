"""Writes the test data catalogue: what the seeded test environment holds, for people and agents.

    python -m qe.tools.export_test_data <seed.db>

The seed database comes from the lab image (/seed/billing.db). The catalogue lists the reference data
and the open work from September 2026 a proposal would pick up, with no computed amounts: working out what an
invoice should show is the job of whoever reads it.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml

OUT = Path(__file__).resolve().parents[1] / "estate" / "test-data" / "catalogue.yaml"
STATUS = {0: "Draft", 1: "Submitted", 2: "Approved", 3: "Rejected"}
BILLING_TYPE = {0: "Time and materials", 1: "Fixed price"}
PROJECT_STATUS = {0: "Active", 1: "Closing", 2: "Closed"}


def _rows(db: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    cursor = db.execute(sql)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _number(value: Any) -> Any:
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return value
        return int(number) if number.is_integer() else number
    return value


def catalogue(db: sqlite3.Connection) -> dict[str, Any]:
    customers = _rows(
        db,
        """SELECT Code, Name, Currency, CountryCode, VatNumber, IsBusiness, PaymentTermsDays,
                  DiscountPercent, PoRequired, IsOnHold, HoldReason FROM Customers ORDER BY Code""",
    )
    rates = _rows(
        db,
        """SELECT c.Code AS customer, r.RoleCode AS role, r.Rate AS rate
           FROM CustomerRates r JOIN Customers c ON c.Id = r.CustomerId""",
    )
    projects = _rows(
        db,
        """SELECT p.Code, p.Name, c.Code AS Customer, p.BillingType, p.Status, p.TaxCode,
                  p.ExpenseMarkupPercent, p.NotToExceed, p.IsOnHold, p.HoldReason
           FROM Projects p JOIN Customers c ON c.Id = p.CustomerId ORDER BY p.Code""",
    )
    project_rates = _rows(
        db,
        """SELECT p.Code AS project, r.RoleCode AS role, r.Rate AS rate
           FROM ProjectRates r JOIN Projects p ON p.Id = r.ProjectId""",
    )
    time = _rows(
        db,
        """SELECT p.Code AS project, t.Date AS date, e.Name AS employee, e.RoleCode AS role,
                  t.Hours AS hours, t.ActivityCode AS activity, t.Comment AS comment,
                  t.Status AS status, t.Billable AS billable
           FROM TimeEntries t JOIN Projects p ON p.Id = t.ProjectId JOIN Employees e ON e.Id = t.EmployeeId
           WHERE t.InvoiceLineId IS NULL AND t.Date >= '2026-09-01' ORDER BY p.Code, t.Date, t.Id""",
    )
    expenses = _rows(
        db,
        """SELECT p.Code AS project, x.Date AS date, x.Description AS description, x.Amount AS cost,
                  x.Status AS status, x.Billable AS billable
           FROM Expenses x JOIN Projects p ON p.Id = x.ProjectId
           WHERE x.InvoiceLineId IS NULL AND x.Date >= '2026-09-01' ORDER BY p.Code, x.Date""",
    )
    milestones = _rows(
        db,
        """SELECT p.Code AS project, m.Name AS name, m.Amount AS amount, m.PlannedDate AS planned,
                  m.IsComplete AS complete, m.CompletedOn AS completed_on,
                  m.BilledInvoiceId IS NOT NULL AS billed
           FROM Milestones m JOIN Projects p ON p.Id = m.ProjectId ORDER BY p.Code, m.PlannedDate""",
    )
    fx = _rows(
        db,
        """SELECT ToCurrency AS currency, EffectiveDate AS effective, Rate AS rate FROM ExchangeRates
           WHERE EffectiveDate >= '2026-09-01' ORDER BY ToCurrency, EffectiveDate""",
    )
    by_project: dict[str, dict[str, Any]] = {}
    for p in projects:
        by_project[p["Code"]] = {
            "name": p["Name"],
            "customer": p["Customer"],
            "billing_type": BILLING_TYPE[p["BillingType"]],
            "status": PROJECT_STATUS[p["Status"]],
            "tax_code": p["TaxCode"],
            "expense_markup_percent": _number(p["ExpenseMarkupPercent"]),
            "not_to_exceed_eur": _number(p["NotToExceed"]),
            "on_hold": p["HoldReason"] if p["IsOnHold"] else None,
            "project_rates": {
                r["role"]: _number(r["rate"]) for r in project_rates if r["project"] == p["Code"]
            },
            "unbilled_time": [
                {
                    "date": t["date"],
                    "employee": t["employee"],
                    "role": t["role"],
                    "hours": _number(t["hours"]),
                    "activity": t["activity"],
                    "comment": t["comment"],
                    "status": STATUS[t["status"]],
                    "billable": bool(t["billable"]),
                }
                for t in time
                if t["project"] == p["Code"]
            ],
            "unbilled_expenses": [
                {**{k: _number(v) for k, v in x.items() if k != "project"}, "status": STATUS[x["status"]]}
                for x in expenses
                if x["project"] == p["Code"]
            ],
            "milestones": [
                {k: _number(v) for k, v in m.items() if k != "project"}
                for m in milestones
                if m["project"] == p["Code"]
            ],
        }
    return {
        "business_date": "2026-10-30",
        "company": {"name": "Kestrel Consulting Oy", "currency": "EUR", "country": "FI"},
        "roles": {
            r["Code"]: {"name": r["Name"], "standard_rate": _number(r["DefaultRate"])}
            for r in _rows(db, "SELECT * FROM Roles ORDER BY Code")
        },
        "employees": {r["Name"]: r["RoleCode"] for r in _rows(db, "SELECT * FROM Employees ORDER BY Id")},
        "tax_codes": {
            r["Code"]: {
                "description": r["Description"],
                "rate_percent": _number(r["Rate"]),
                "exempt": bool(r["IsExempt"]),
            }
            for r in _rows(db, "SELECT * FROM TaxCodes ORDER BY Code")
        },
        "exchange_rates_from_eur": [{**r, "rate": _number(r["rate"])} for r in fx],
        "customers": {
            c["Code"]: {
                "name": c["Name"],
                "currency": c["Currency"],
                "country": c["CountryCode"],
                "vat_number": c["VatNumber"],
                "business": bool(c["IsBusiness"]),
                "payment_terms_days": c["PaymentTermsDays"],
                "agreement_discount_percent": _number(c["DiscountPercent"]),
                "po_required": bool(c["PoRequired"]),
                "on_hold": c["HoldReason"] if c["IsOnHold"] else None,
                "agreed_rates": {r["role"]: _number(r["rate"]) for r in rates if r["customer"] == c["Code"]},
            }
            for c in customers
        },
        "projects": by_project,
    }


def main() -> None:
    db = sqlite3.connect(sys.argv[1])
    header = (
        "# Test data catalogue: the seeded test environment, as loaded on every reset.\n"
        "# Written by qe/tools/export_test_data.py from the lab's seed database. Do not edit by hand.\n"
    )
    body = yaml.safe_dump(catalogue(db), sort_keys=False, allow_unicode=True, width=110)
    OUT.write_text(header + body, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
