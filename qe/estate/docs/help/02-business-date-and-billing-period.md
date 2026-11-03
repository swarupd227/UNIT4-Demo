# 2. The business date and the billing period

Last updated: March 2025

## The business date

Project Billing does not use the calendar date. It uses a fixed **business date**, shown in the top bar of every page. The finance systems team sets it. It is usually moved forward once for each billing run, so that period ends do not change while a run is in progress.

You cannot change the business date yourself. If it looks wrong, contact the finance systems team before you create any proposals.

The business date is used for:

- the default **Period end** and **Invoice date** for new proposals,
- the **Billing period ending** date on the home page,
- the **Invoices this month** count on the home page,
- the completion date of a milestone when you select **Mark complete**,
- the invoice date of a credit note,
- the **Unbilled time** list on a project page, which shows the last three months before the business date.

## The period end

Each proposal has a **Period end**. Only time, expenses and milestones dated on or before the period end are billed. Anything later waits for the next period.

When you open **New proposal**, the period end is set to the last day of the month of the business date. For example, if the business date is 30 Oct 2026, the period end is 31 October 2026. You can change it if you need to bill a shorter period.

## The invoice date

Each proposal also has an **Invoice date**. It is set to the period end by default. The invoice date:

- appears on the invoice,
- decides which exchange rate is used (see [Currencies and exchange rates](17-currencies-and-exchange-rates.md)),
- is the start of the payment terms (see [Invoice numbers and due dates](23-invoice-numbers-and-due-dates.md)).

The invoice date cannot be earlier than the period end. If you try, you see "The invoice date cannot be before the period end."

The invoice date is fixed when the proposal is created. To use a different invoice date, delete the proposal and create it again.

## Example

The business date is 30 Oct 2026.

| Field | Default | Can be changed to |
|---|---|---|
| Period end | 31 Oct 2026 | 15 Oct 2026, to bill the first half of the month only |
| Invoice date | 31 Oct 2026 | 2 Nov 2026, but not 14 Oct 2026 |

If you set the period end to 15 Oct 2026, time recorded on 20 October stays unbilled and is picked up by a later proposal.

## Before you start a billing run

Check the business date in the top bar. Check the **Billing period ending** date on the home page. If either is not the month you expect to bill, stop and contact the finance systems team. Proposals created with the wrong period end pick up the wrong entries.
