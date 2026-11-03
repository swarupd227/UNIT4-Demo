# 10. Fixed-price projects and milestones

Last updated: January 2025

A fixed-price project is billed in agreed instalments called milestones. Each milestone has a fixed amount in EUR. Hours recorded on a fixed-price project are not billed, whatever their status.

## The milestones table

The project page of a fixed-price project has a **Milestones** table:

| Column | Meaning |
|---|---|
| **Milestone** | The name of the milestone, for example *Solution design*. |
| **Planned** | The date the milestone is planned to be reached. |
| **Amount (EUR)** | The amount to bill when it is complete. |
| **Status** | *Open*, *Complete* with the completion date, or *Billed*. |

## Marking a milestone complete

When the project manager confirms that a milestone has been delivered:

1. Open the project page.
2. Select **Mark complete** next to the milestone.

The message "Milestone Solution design marked complete." confirms it. The status changes to *Complete* with the business date as the completion date.

The **Mark complete** button disappears once the milestone is complete. A completion cannot be undone from this page. If a milestone was marked complete by mistake, contact the finance systems team before the next proposal is created.

## When a milestone is billed

A milestone is added to a proposal when:

- the project's billing type is *Fixed price*,
- the milestone is complete,
- its completion date is on or before the proposal's **Period end**,
- it has not been billed before.

A milestone completed after the period end waits for a later proposal. For example, P-1080 Pacific freight tracking has a milestone *Solution design* completed on 16 Oct 2026. A proposal with a period end of 15 Oct 2026 does not include it. A proposal with a period end of 31 Oct 2026 does.

Each milestone is billed once. Its status changes to *Billed* when the invoice is finalised. Until then it stays *Complete*. If you delete the proposal, the milestone is still unbilled and the next proposal picks it up.

## How milestones appear on a proposal

- **Type** is *Milestone*.
- **Description** is "Milestone:" and the name, for example "Milestone: Discovery".
- **Qty** is 1.00 and **Unit price (EUR)** is the milestone amount.
- The agreement discount is not taken off milestones.

Milestone lines come after time and expense lines, in the order of their planned dates.

## Expenses on fixed-price projects

Approved, billable expenses are billed on fixed-price projects in the same way as on time and materials projects. See [Expenses and expense markup](08-expenses-and-markup.md).

## Not-to-exceed

Milestones count against a not-to-exceed limit if the project has one. See [Not-to-exceed limits](09-not-to-exceed-limits.md).
