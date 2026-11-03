# 13. Creating a proposal

Last updated: August 2025

A proposal is a draft invoice. It collects everything billable on one project up to a period end. You check and adjust it, then finalise it to produce the invoice.

## Steps

1. Select **Proposals** in the menu, then **New proposal**. Or open the project page and select **Create proposal**. The project is then already selected.
2. On the **New invoice proposal** page, select the **Project**. Closed projects are not listed.
3. Check the **Period end**. It defaults to the last day of the month of the business date.
4. Check the **Invoice date**. It defaults to the period end. It cannot be earlier than the period end.
5. Select **Create proposal**.

Project Billing opens the new proposal. Its reference is shown in the heading, for example **Invoice proposal P00012**. See [What a proposal contains](14-what-a-proposal-contains.md).

To leave without creating anything, select **Cancel**.

## What Project Billing checks first

Before anything is calculated, Project Billing checks these in order. If one fails, the proposal is not created and the message is shown at the top of the page.

| Check | Message |
|---|---|
| No project selected | "Select a project." |
| Customer on hold | "Billing hold: customer Ostra Logistics Oy is on hold. Disputed invoices, see case 4471." |
| Project on hold | "Billing hold: project P-1011 is on hold. Scope change under review." |
| Project closed | "Project P-1001 is closed." |
| Invoice date too early | "The invoice date cannot be before the period end." |
| Open proposal already exists | "Project P-1001 already has an open proposal. Finalise or delete it first." |
| Nothing billable | "There is nothing to bill on P-1001 up to 31 Oct 2026." |

## One open proposal per project

A project can have only one open proposal at a time. Finalise or delete the open proposal before you create another. A deferred proposal does not count as open. See [Minimum invoice amount and deferred proposals](21-minimum-invoice-amount.md).

## What is calculated

When the proposal is created, Project Billing:

- picks up approved, billable, unbilled time and expenses dated on or before the period end (see [How time and expenses become billable](11-billable-time-and-expenses.md)),
- picks up completed, unbilled milestones on fixed-price projects (see [Fixed-price projects and milestones](10-fixed-price-milestones.md)),
- rounds hours up to the quarter hour and prices them at the right rate,
- adds the expense markup and takes off the agreement discount,
- applies the not-to-exceed limit, if there is one,
- sets the tax code on every line, including reverse charge where it applies,
- looks up the exchange rate for the invoice date and converts every line,
- reserves the time and expenses so that no other proposal can pick them up.

If the proposal is worth less than the minimum invoice amount, it is saved as *Deferred* instead and nothing is reserved.

## Deleting a proposal

Open the proposal and select **Delete proposal**. Confirm the question "Delete this proposal? Its entries go back to unbilled." The message "Proposal deleted." confirms it. All its time and expenses become unbilled again, and you can create a new proposal for the project.

Delete and recreate a proposal when you need a different period end or invoice date, or after rates, discounts or entries have changed.
