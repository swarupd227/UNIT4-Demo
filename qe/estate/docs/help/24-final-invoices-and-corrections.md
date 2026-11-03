# 24. Final invoices and corrections

Last updated: January 2026

Once an invoice is final it has been sent to the general ledger and, usually, to the customer. It can no longer be changed or deleted. This keeps the ledger, the customer's records and Kestrel's records in step.

## What is locked

On a final invoice you cannot:

- change, add or remove lines,
- write lines up or down,
- change the purchase order number,
- change the invoice date or due date,
- delete the invoice.

If you open a final invoice from an old link to its proposal, the page shows "This invoice is final. Changes are made with a credit note." with a link to open the invoice. The **Adjust**, **Save PO**, **Finalise invoice** and **Delete proposal** controls are not shown.

If an attempt to change a final invoice reaches Project Billing in another way, you see one of these messages:

- "This invoice is final. Changes are made with a credit note."
- "A final invoice cannot be deleted. Raise a credit note instead."
- "This invoice is already final."

## How to correct a final invoice

All corrections are made with a credit note. See [Credit notes](25-credit-notes.md).

| Problem | What to do |
|---|---|
| A line was overcharged | Credit the difference on that line. |
| A line should not have been charged at all | Credit the full line. |
| The whole invoice is wrong (wrong customer, wrong PO, wrong VAT) | Credit the whole invoice. Then ask the finance systems team to correct the setting before the next proposal. |
| A line was undercharged | Speak to the billing manager. A credit note cannot increase an invoice. |

## Crediting does not re-open the work

Crediting a line does not return its time or expenses to unbilled. A credited milestone stays *Billed*. The entries will not appear on a later proposal.

So when you credit an invoice in full because of a setting error, the corrected amounts are not re-invoiced automatically. Agree with the billing manager how the customer is to be re-invoiced before you issue the credit note.

## Effect on not-to-exceed limits

Credit notes reduce the amount billed to date on the project. On a project with a not-to-exceed limit, a credit note makes room for entries that were held back. The next proposal can then include them. See [Not-to-exceed limits](09-not-to-exceed-limits.md).

## Before you finalise

The easiest correction is the one you do not need. Before you select **Finalise invoice**, check:

- the period end and invoice date,
- the PO number,
- the VAT code and any note on the invoice,
- the exchange rate,
- any write-ups and write-downs, and their reasons.

If anything is wrong at proposal stage, delete the proposal and create it again. That is quicker than a credit note and keeps the customer's account clean.

## Audit

Project Billing records who created each proposal, who finalised each invoice and who issued each credit note, with the time. Write-ups, write-downs, deletions and changes to customers and holds are also recorded. The finance systems team can provide this history for audits.
