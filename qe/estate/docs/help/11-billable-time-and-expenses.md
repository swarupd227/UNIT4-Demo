# 11. How time and expenses become billable

Last updated: May 2025

Consultants record their time and expenses in the time recording system. Project Billing reads these entries. You do not enter time in Project Billing.

## The life of an entry

Each time entry and expense has a status:

| Status | Meaning | Billed? |
|---|---|---|
| *Draft* | Recorded but not sent for approval. | No |
| *Submitted* | Sent to the project manager for approval. | No |
| *Approved* | Approved by the project manager. | Yes, if billable |
| *Rejected* | Sent back by the project manager. | No |

Each entry is also marked as billable or not billable. Internal work, such as training or rework that the customer does not pay for, is recorded as not billable.

## What a proposal picks up

On a time and materials project, a proposal includes every time entry that:

1. has the status *Approved*,
2. is marked billable,
3. has not already been billed and is not on another proposal,
4. is dated on or before the proposal's **Period end**.

Expenses follow the same four conditions. See [Expenses and expense markup](08-expenses-and-markup.md).

Entries that do not meet all four conditions stay where they are. When they are approved later, the next proposal picks them up. There is no need to re-enter or move them.

On a fixed-price project, time entries are never billed. Milestones are billed instead. See [Fixed-price projects and milestones](10-fixed-price-milestones.md).

## Older entries

There is no start date. An approved, billable entry from an earlier month that was never billed is included in the next proposal, as long as it is dated on or before the period end. Check the dates on the proposal lines if the total is higher than expected.

## Reserved entries

When a proposal is created, its time and expense entries are reserved for it. They no longer appear in the **Unbilled time** and **Unbilled expenses** tables on the project page, and no other proposal can pick them up.

If you delete the proposal, the entries are released and become unbilled again.

When the invoice is finalised, the entries are billed. They will not be billed again.

## Checking before you bill

On the project page:

- **Unbilled time** shows entries from the last three months, with their **Billable** flag and **Status**.
- **Unbilled expenses** shows unbilled expenses with their **Status**.

Look for *Draft* and *Submitted* entries. If they should be on this month's invoice, ask the project manager to approve them before you create the proposal.

The **Unbilled hours** column in the project list shows approved, billable hours that are not on a proposal, for all dates.

## How time appears on a proposal

Each time entry becomes one line. The **Description** is the date, the employee name and the activity code, followed by the entry's comment in brackets if there is one. For example:

"2026-10-01 Sara Holm - CONS (Call with grid operator)"

Time lines are listed first, in date order. The hours are rounded up to the next quarter hour. See [Quarter-hour billing](12-quarter-hour-billing.md).
