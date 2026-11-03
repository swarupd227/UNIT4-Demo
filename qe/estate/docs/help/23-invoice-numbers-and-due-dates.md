# 23. Invoice numbers and due dates

Last updated: May 2024

## Proposal references

Every proposal has a reference such as **P00012**. It is shown in the **Proposals** list and in the heading of the proposal. It is for internal use only. Do not quote it to customers. It is not an invoice number.

## Invoice numbers

An invoice gets its number when it is finalised, never before. The proposal page shows **Invoice number** as "Assigned when finalised" until then.

Invoice numbers look like this: **INV-000123**. They are six digits, with leading zeros, and go up by one for each invoice.

Credit notes have their own sequence: **CN-000045**. A credit note does not use an invoice number, and an invoice does not use a credit note number.

## No gaps

Because numbers are given only on finalising, the sequences have no gaps:

- creating a proposal does not use a number,
- deleting a proposal does not use a number,
- a deferred proposal does not use a number,
- a finalise that fails, for example because the PO number is missing, does not use a number.

If an auditor asks about a missing number, the finance systems team can trace it. In normal use there are none.

The numbers are shared by the whole company. If two people finalise invoices at the same time, each invoice still gets its own number.

## Due dates

The due date is set when the invoice is finalised. It is the **invoice date** plus the customer's **Payment terms (days)**.

If the customer's payment terms are 0, Project Billing uses 30 days.

| Customer | Payment terms | Invoice date | Due date |
|---|---|---|---|
| Halden Group Oy | 30 days | 31 Oct 2026 | 30 Nov 2026 |
| Brightwater Utilities Ltd | 45 days | 31 Oct 2026 | 15 Dec 2026 |
| Meridian Health Services Oy | 14 days | 31 Oct 2026 | 14 Nov 2026 |
| Sakura Components KK | 60 days | 31 Oct 2026 | 30 Dec 2026 |

The due date is counted in calendar days. It is not moved if it falls on a weekend or public holiday.

The payment terms are read from the customer at the moment you finalise. If the terms were changed after the proposal was created, the new terms are used.

The due date cannot be changed on a final invoice. To give a customer longer to pay on one invoice, agree it with the credit control team. Do not change the customer's payment terms for a single invoice.

## Credit notes

Credit notes do not have a due date. Their invoice date is the business date on the day they are issued.
