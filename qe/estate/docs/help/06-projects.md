# 6. Projects

Last updated: February 2026

Every invoice belongs to one project. The project decides how work is charged, which tax code applies, and whether there is a limit on what can be billed.

## The project list

Select **Projects** in the menu. The list shows:

- **Code** and **Name**, for example P-1001 Halden ERP rollout.
- **Customer**.
- **Billing**: *Time and materials* or *Fixed price*.
- **Status**: *Active*, *Closing*, *Closed*, or *On hold* if the project has a billing hold.
- **Unbilled hours**: approved, billable hours that are not yet billed or on a proposal. This is the hours as recorded, before quarter-hour rounding, and it includes all dates. Fixed-price projects always show 0.00, because their hours are not billed.

Use **Search** to find a project by code, project name or customer name.

## The project page

Select a project code. The top of the page shows:

| Field | Meaning |
|---|---|
| **Customer** | The customer name and code. Select it to open the customer. |
| **Billing** | *Time and materials* or *Fixed price*. |
| **Status** | *Active*, *Closing* or *Closed*. |
| **Tax code** | The tax code used on every line of the project's invoices. See [VAT and tax codes](15-vat-and-tax-codes.md). |
| **Expense markup** | The percentage added to the cost of expenses. See [Expenses and expense markup](08-expenses-and-markup.md). |
| **Not-to-exceed** | The most that can be billed on the project, in EUR, or *None*. See [Not-to-exceed limits](09-not-to-exceed-limits.md). |
| **Project manager** | The person responsible for the project. |

Below these are the **Billing hold** controls (see [Billing holds](05-billing-holds.md)) and the **Create proposal** button.

## Time and materials or fixed price

- **Time and materials** projects bill approved hours at the hourly rate for each person's role, plus expenses.
- **Fixed price** projects bill agreed milestone amounts when each milestone is complete, plus expenses. Hours recorded on a fixed-price project are never billed. See [Fixed-price projects and milestones](10-fixed-price-milestones.md).

Both types bill approved, billable expenses.

## Project status

- **Active**: normal billing.
- **Closing**: the project is finishing. Proposals are not deferred for being below the minimum invoice amount, so the last small amounts can be billed. See [Minimum invoice amount and deferred proposals](21-minimum-invoice-amount.md).
- **Closed**: no more billing. Closed projects do not appear in the **Project** list on the new proposal page.

## Other sections

- **Rate card**: the project's own hourly rates by role, if it has any. See [Hourly rates and the agreement discount](07-rates.md).
- **Milestones**: fixed-price projects only.
- **Unbilled time**: time entries from the last three months that are not billed and not on a proposal, with **Date**, **Employee**, **Activity**, **Hours**, **Billable** and **Status**. Rejected entries are not shown. Draft and submitted entries are shown, but they are not billed until they are approved.
- **Unbilled expenses**: expenses that are not billed and not on a proposal, with **Date**, **Description**, **Cost (EUR)** and **Status**. Rejected expenses are not shown.

Project settings such as billing type, tax code, markup and the not-to-exceed limit are maintained by the finance systems team.
