# 21. Minimum invoice amount and deferred proposals

Last updated: September 2024

A very small invoice costs more to process and collect than it is worth. Project Billing therefore holds back small amounts until there is enough to bill.

## The minimum

The minimum invoice amount is **50.00 EUR**, before tax. It is measured in EUR, whatever the invoice currency.

When you create a proposal and its value before tax is less than 50.00 EUR, the proposal is saved with the status *Deferred*. You see this message on the proposal:

"Below the minimum invoice amount of 50.00 EUR. The entries stay unbilled and are picked up by the next billing run."

## What a deferred proposal means

- The time and expenses on it are **not** reserved. They stay unbilled, and they still appear in the **Unbilled time** and **Unbilled expenses** tables on the project page.
- The proposal cannot be finalised. If you try, you see "A deferred proposal cannot be finalised. Its entries are billed in the next run."
- The proposal cannot be adjusted. If you try, you see "A deferred proposal cannot be adjusted."
- It does not stop you creating another proposal for the same project.

A deferred proposal stays in the **Proposals** list with the status *Deferred*, so you can see which projects were deferred in the run. When you no longer need it, open it and select **Delete proposal**.

## Next month

In the next billing run, create a proposal for the project as usual. It picks up the deferred entries together with the new ones. If the total is now 50.00 EUR or more, it is a normal proposal.

## Example

P-1131 Polar crew app fixes has one approved entry of 0.50 hours by a junior consultant at 85.00 EUR. The proposal is worth 42.50 EUR, so it is deferred. Next month, another 4 hours are recorded. The new proposal is worth 382.50 EUR and is created normally.

## Closing projects

The minimum does not apply to projects with the status *Closing*. A proposal for a closing project is created normally, however small, so that the last amounts can be billed before the project is closed.

For example, P-1132 Polar legacy closeout is *Closing*. A proposal for 0.50 hours is created as a normal proposal.

If a small amount on an active project must be billed now, ask the finance systems team to set the project to *Closing*.

## What counts

The test uses the value of the proposal lines in EUR, before tax, after the discount and markup. It is checked once, when the proposal is created.
