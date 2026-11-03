# 15. VAT and tax codes

Last updated: November 2024

Every invoice line carries a tax code. The tax code decides the VAT rate on the line.

## Where the tax code comes from

Each project has one **Tax code**, shown on the project page. When a proposal is created, that code is set on every line of the proposal: time, expenses and milestones alike.

There is one exception. If the customer qualifies for reverse charge, the code *RC* is used instead of the project's code. See [Reverse charge](16-reverse-charge.md).

You cannot change the tax code on a single line. If the tax code on a project is wrong, contact the finance systems team, then delete and recreate the proposal.

## The tax codes

Select **Tax codes** in the menu to see the list. It shows the **Code**, **Description**, **Rate** and whether the code is **Exempt**.

| Code | Description | Rate | Exempt |
|---|---|---|---|
| S | Standard rate | 25.5% | |
| R1 | Reduced rate | 14% | |
| R2 | Reduced rate | 10% | |
| E | health and social care services | 0% | Yes |
| Z | Outside the scope of Finnish VAT (services to non-EU businesses) | 0% | |
| RC | Reverse charge (set automatically for EU business customers with a VAT number) | 0% | |

The standard rate has been 25.5% since 1 September 2024. Invoices from before that date show the old rate of 24%.

The tax code list is maintained by the finance systems team. You cannot change it from this page.

## Exempt services

When the project's tax code is exempt, the lines carry no VAT and the invoice gets a note, for example:

"Exempt from VAT: health and social care services."

The note is shown on the proposal and on the invoice. For example, P-1040 Meridian clinical scheduling uses code *E*.

## Outside the scope of Finnish VAT

Code *Z* is used for services to businesses outside the EU, for example Brightwater Utilities Ltd in the United Kingdom or Vestfold Shipping AS in Norway. The lines carry 0% VAT. No note is added.

## How VAT is worked out

VAT is worked out line by line. The tax on each line is the rounded line amount times the rate, rounded to the currency's decimal places. The **Tax** total is the sum of the line tax amounts. See [Rounding](18-rounding.md).

For example, a line of 53.46 EUR at 25.5% has tax of 13.63 EUR (53.46 × 25.5% = 13.6323).

## When the tax code is fixed

The tax code and rate are set when the proposal is created. They are not looked up again when you finalise.

When you credit an invoice, the credit note uses the tax code and rate of the original line, even if the rate has changed since. See [Credit notes](25-credit-notes.md).

If you see "Tax code R3 does not exist.", the project refers to a code that is not in the list. Contact the finance systems team.
