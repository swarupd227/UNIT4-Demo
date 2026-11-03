# 19. Write-ups and write-downs

Last updated: July 2025

Sometimes the amount on a proposal line is not what should be invoiced. The project manager may agree with the customer to charge less for rework, or to charge more for out-of-hours support. You change the line with an adjustment.

- A **write-up** increases a line. Enter a positive amount.
- A **write-down** reduces a line. Enter a negative amount.

## Making an adjustment

1. Open the proposal.
2. Find the line. On the right of the line are two fields, **Adjustment** (shown as *+/- EUR*) and **Reason**.
3. Enter the amount in EUR, for example `-150` for a write-down of 150.00 EUR, or `75.50` for a write-up of 75.50 EUR.
4. Enter the reason, for example "Rework agreed with customer, not chargeable".
5. Select **Adjust**.

The message "Adjustment saved." confirms the change. The **Adjustment (EUR)** column shows the amount with a + or − sign, and the reason appears under the line description. The line **Amount**, its **Tax amount** and the totals are recalculated straight away.

## Adjustments are in EUR

The adjustment is always in EUR, even when the customer is invoiced in another currency. Project Billing adds it to the line's EUR value and then converts and rounds the line as usual. See [Rounding](18-rounding.md).

Use a full stop for decimals. A comma is read as a thousands separator and ignored, so `1,5` is read as 15.

## Each line has one adjustment

A line holds one adjustment at a time. A new adjustment **replaces** the previous one. It is not added to it. If a line has a write-down of −100 and you enter −50, the write-down becomes −50.

To remove an adjustment, enter `0` or leave the field empty and select **Adjust**. No reason is needed to remove an adjustment.

## Rules

- **A reason is required.** Without one you see "Enter a reason for the write-up." or "Enter a reason for the write-down."
- **A line cannot go below zero.** A write-down can reduce a line to exactly 0.00, but not further. If you try, you see "A write-down cannot take a line below zero."
- **Only open proposals can be adjusted.** A final invoice cannot be changed: "This invoice is final. Changes are made with a credit note." A deferred proposal cannot be adjusted: "A deferred proposal cannot be adjusted."

## Writing off a whole line

To bill nothing for a line, write it down by its full EUR value. The line stays on the invoice at 0.00, with the reason. Its time or expense is still billed, so it will not come back on a later proposal.

If the entry should be billed later instead, do not write it down. Delete the proposal, ask the project manager to correct the entry, then create the proposal again.

## Good reasons

The reason is printed under the line and kept with the invoice. Write it for the auditor and the customer, not for yourself. Good reasons say what was agreed and with whom:

- "Travel time not chargeable under framework agreement"
- "Weekend support, 50% uplift agreed by O. Rantanen"
