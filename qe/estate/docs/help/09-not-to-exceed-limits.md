# 9. Not-to-exceed limits

Last updated: April 2026

Some contracts cap the total that Kestrel can bill on a project. This cap is the project's **Not-to-exceed** limit, shown on the project page. If the project has no cap, the page shows *None*.

The limit is in EUR and is before tax. For example, P-1100 Koivula citizen services has a not-to-exceed limit of 20,000.00 EUR.

## What counts against the limit

When you create a proposal, Project Billing adds up:

- the EUR value before tax of every final invoice already issued on the project,
- less the value of every credit note issued on the project,
- plus the lines on the new proposal, one by one.

Time, expenses (including markup) and milestones all count.

## What happens when the limit is reached

Project Billing works through the entries in order: time first, by date, then expenses, by date, then milestones. Each entry is added only if it fits under the limit. An entry that would take the total over the limit is **held back**. Project Billing then carries on with the next entry, so a later, smaller entry can still be included.

Held-back entries are not lost. They stay unbilled and are picked up by a later proposal if there is room, for example after a credit note or a contract change that raises the limit.

When at least one entry is held back, the proposal shows a message at the top, for example:

"3 entries were held back: the not-to-exceed limit of 20,000.00 EUR is reached."

When only one entry is held back, it says "1 entry was held back: ...".

If no entry fits at all, the proposal is not created and you see:

"Nothing can be billed: the not-to-exceed limit of 20,000.00 EUR has been reached."

## Example

P-1100 has a limit of 20,000.00 EUR. Invoices worth 18,500.00 EUR before tax are already final. The next proposal finds three entries:

| Entry | Value (EUR) | Running total | Result |
|---|---|---|---|
| Time, 6 Oct | 900.00 | 19,400.00 | Included |
| Time, 13 Oct | 750.00 | 20,150.00 | Held back |
| Time, 20 Oct | 300.00 | 19,700.00 | Included |

The proposal has two lines worth 1,200.00 EUR and the message "1 entry was held back: the not-to-exceed limit of 20,000.00 EUR is reached."

## What to do

Tell the project manager when entries are held back. They decide with the customer whether to raise the limit or write the work off. A change to the limit is made by the finance systems team.

Proposals that are not yet final do not count against the limit. Only final invoices and credit notes do.
