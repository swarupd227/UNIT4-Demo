# 8. Expenses and expense markup

Last updated: November 2024

Consultants record travel and other project costs as expenses. Approved, billable expenses are passed on to the customer on the next invoice.

## Which expenses are billed

An expense is added to a proposal when all of these are true:

- its status is *Approved*,
- it is marked billable,
- it has not been billed before and is not on another proposal,
- its date is on or before the proposal's **Period end**.

Expenses are billed on both time and materials and fixed-price projects.

## Expense markup

Some contracts allow Kestrel to add a handling charge to expenses. This is set on the project as the **Expense markup** percentage, shown on the project page. When the markup is 0%, expenses are billed at cost.

The billed amount is the cost plus the markup. For example, on P-1001 Halden ERP rollout the markup is 10%:

| Expense | Cost (EUR) | Markup 10% | Billed (EUR) |
|---|---|---|---|
| Train ticket | 48.60 | 4.86 | 53.46 |
| Hotel, one night | 129.00 | 12.90 | 141.90 |

The agreement discount is never taken off expenses. See [Hourly rates and the agreement discount](07-rates.md).

## How expenses appear on a proposal

Each expense is one line on the proposal:

- **Type** is *Expense*.
- **Description** is the expense date and its description, for example "2026-10-15 Train Helsinki - Tampere return".
- **Qty** is 1.00.
- **Unit price (EUR)** is the cost including the markup.
- **Discount** is empty.
- **Amount** is the unit price, converted to the invoice currency if needed.

The project's tax code applies to expense lines in the same way as to time lines. See [VAT and tax codes](15-vat-and-tax-codes.md).

Expense lines come after the time lines on the proposal, in date order.

## Checking expenses before billing

The project page has an **Unbilled expenses** table. It lists every expense on the project that is not billed and not on a proposal, with **Date**, **Description**, **Cost (EUR)** and **Status**. Rejected expenses are not shown.

The **Cost (EUR)** column is the cost before markup. Only expenses with the status *Approved* are billed. If an expense you expect to bill is still *Draft* or *Submitted*, ask the project manager to approve it before you create the proposal.

The table does not show whether an expense is billable. If an approved expense does not appear on the proposal, it may be marked as not billable. Check with the project manager.

## Expenses and the not-to-exceed limit

On a project with a not-to-exceed limit, expenses count towards the limit, including the markup. See [Not-to-exceed limits](09-not-to-exceed-limits.md).
