# 25. Credit notes

Last updated: October 2026

A credit note reduces what a customer owes on a final invoice. Use it to correct an overcharge or to cancel an invoice.

## Creating a credit note

1. Open the final invoice from **Invoices**.
2. Select **Create credit note**.
3. The page **Credit invoice INV-000123** opens. It shows the **Customer**, the **Invoice total** and the amount **Still open to credit**.
4. For each line you want to credit, enter the amount in the **Credit before tax** field. Leave the other lines empty.
5. Enter the **Reason**.
6. Select **Issue credit note**.

The credit note opens with the message "Credit note CN-000045 issued." It is final straight away. There is no draft stage.

## How amounts are entered

- Enter amounts **before tax**. Project Billing adds the tax.
- Enter amounts in the **invoice currency**, as shown in the **Amount** column. Not in EUR.
- Enter amounts as **positive numbers**. Project Billing shows them as negative on the credit note.
- Use a full stop for decimals.

## Tax on a credit note

Each credit line uses the tax code and rate of the invoice line it credits. This applies even if the rate has changed since the invoice was issued. For example, a line invoiced at 24% before 1 September 2024 is credited at 24%, not at today's 25.5%.

The tax on each credit line is the credit amount times the line's tax rate, rounded to the currency's decimal places.

For example, crediting 200.00 EUR on a line taxed at 25.5% gives a credit of 200.00 plus 51.00 tax. The credit note total is −251.00 EUR.

## The credit limit

A credit note can never take the total credited above the invoice total.

- Each line can be credited by at most its own amount. Otherwise: "Line 2 cannot be credited by more than its amount of 1,050.00 EUR."
- The credit note total, **including tax**, cannot be more than the amount **Still open to credit**. Otherwise: "The credit of 1,317.75 EUR is more than the 1,000.00 EUR still open on invoice INV-000123."

**Still open to credit** is the invoice total including tax, less the totals of all credit notes already issued against it. You can issue several credit notes against the same invoice until nothing is left open.

## Other messages

- "Enter a reason for the credit note."
- "Enter an amount to credit on at least one line."
- "Enter credit amounts as positive numbers."
- "Only a final invoice can be credited."

## What the credit note contains

- A number from the credit note sequence, for example CN-000045.
- The heading **Credit note** and the number. **Credits invoice** links back to the original.
- The **Invoice date** is the business date on the day it is issued. There is no due date.
- The same currency and **Exchange rate** as the original invoice.
- A note: "Credit for invoice INV-000123." followed by your reason.
- One line for each credited line, described as "Credit:" and the original description.

The credit note is posted to the general ledger when it is issued. As with finalising, this can take a few seconds.

## On the original invoice

The original invoice shows **Credited so far** with the total credited, including tax, and a list of its credit notes with their numbers, dates and totals.

Crediting does not return time or expenses to unbilled. See [Final invoices and corrections](24-final-invoices-and-corrections.md).
