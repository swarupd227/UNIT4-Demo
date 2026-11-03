# 12. Quarter-hour billing

Last updated: May 2024

Kestrel bills time in quarter hours. Consultants can record time in any unit, but the hours on the invoice are always a multiple of 0.25.

## How it works

Each time entry is rounded **up** to the next quarter hour. Rounding is done for each entry separately, when the proposal is created. An entry that is already a whole quarter hour is not changed.

| Hours recorded | Hours billed |
|---|---|
| 0.10 | 0.25 |
| 0.25 | 0.25 |
| 0.60 | 0.75 |
| 1.10 | 1.25 |
| 2.00 | 2.00 |
| 7.60 | 7.75 |

The billed hours are shown in the **Qty** column of the proposal and the invoice. The amount of the line is the billed hours times the hourly rate, less any agreement discount.

## Rounding is per entry

Because each entry is rounded on its own, several short entries can bill more than the same time recorded as one entry. For example:

- two entries of 0.10 hours each are billed as 0.25 + 0.25 = 0.50 hours,
- one entry of 0.20 hours is billed as 0.25 hours.

This is intended. Consultants are asked to record short calls as separate entries when they are separate pieces of work.

## Where you see recorded hours

Two places show the hours as recorded, before rounding:

- the **Hours** column in the **Unbilled time** table on the project page,
- the **Unbilled hours** column in the project list.

So the hours on a proposal can be a little higher than the unbilled hours shown on the project before the proposal was created.

## Example

On P-1020 Norrsken grid analytics, Sara Holm recorded two calls with the grid operator, each of 0.25 hours. Each is billed as 0.25 hours, as recorded.

If a consultant records 3.4 hours of workshop time, the proposal shows **Qty** 3.50.

## Questions from customers

If a customer asks why billed hours differ from their own records, explain that time is billed in quarter hours, rounded up per entry. The rounding is part of Kestrel's standard terms. If the customer's contract says otherwise, write the line down with a reason. See [Write-ups and write-downs](19-write-ups-and-write-downs.md).
