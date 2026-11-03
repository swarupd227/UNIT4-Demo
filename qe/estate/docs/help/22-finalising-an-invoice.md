# 22. Finalising an invoice

Last updated: June 2026

Finalising turns a proposal into an invoice. The invoice gets its number and due date, it is posted to the general ledger, and it can no longer be changed.

## Before you finalise

Check the proposal with the project manager:

- Are the lines, hours and amounts right?
- Are write-ups and write-downs entered, with reasons?
- Is the purchase order number in place, if the customer needs one?
- Is the exchange rate shown, and not *Missing*?
- Is the VAT right, including any reverse charge or exempt note?

## Finalising

1. Open the proposal.
2. Select **Finalise invoice**.
3. Wait. The page "Posting INV-000123 to the ledger" shows while Project Billing posts the invoice to the general ledger. This can take a few seconds, depending on how busy the ledger is. You do not need to refresh the page.

When posting is done, the invoice page opens by itself. The invoice is already final and numbered while it is posting.

## What Project Billing checks

When you select **Finalise invoice**, Project Billing checks these in order. If one fails, the invoice is not finalised and the message is shown at the top of the proposal.

| Check | Message |
|---|---|
| Already final | "This invoice is already final." |
| Deferred proposal | "A deferred proposal cannot be finalised. Its entries are billed in the next run." |
| PO number needed | "A purchase order number is required for Norrsken Energi AB." |
| No exchange rate | "No exchange rate from EUR to CHF on or before 31 Oct 2026. Add the rate before finalising." |

## What happens when you finalise

Project Billing:

1. looks up the exchange rate for the invoice date again and recalculates every line with it,
2. gives the invoice the next invoice number, for example INV-000123,
3. sets the due date from the customer's payment terms (see [Invoice numbers and due dates](23-invoice-numbers-and-due-dates.md)),
4. sets the status to *Final* and records your name and the time,
5. marks any milestones on the invoice as *Billed*,
6. posts the invoice to the general ledger.

The time and expenses on the invoice were reserved when the proposal was created. From now on they are billed and cannot be billed again.

## The invoice page

The heading is **Invoice** and the number. The page shows the **Status**, **Customer**, **Project**, **Invoice date**, **Due date**, **Currency**, **Exchange rate**, **Purchase order** (if there is one), and **Finalised** with the date, time and your name. The time is shown in UTC.

Below are the lines with **#**, **Type**, **Description**, **Qty**, **Amount**, **Tax** and **Tax amount**, and the **Subtotal**, **Tax** and **Total**. The unit prices, discounts and adjustments are not shown on the invoice.

At the bottom are **Credited so far** and the **Create credit note** button. See [Credit notes](25-credit-notes.md).

## After finalising

The invoice appears in the **Invoices** list. It is no longer in the **Proposals** list, and you can create the next proposal for the project.

A final invoice cannot be changed or deleted. See [Final invoices and corrections](24-final-invoices-and-corrections.md).
