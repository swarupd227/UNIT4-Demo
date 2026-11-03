# 20. Purchase orders

Last updated: May 2024

Many customers, especially public sector bodies, will only pay an invoice that quotes their purchase order (PO) number. Project Billing can enforce this.

## Customers that require a PO

On the customer page, the setting **Purchase order number required on invoices** is ticked for these customers. The customer list shows *Yes* in the **PO required** column. For example, Norrsken Energi AB and Koivula Municipality require a PO number.

For these customers, an invoice cannot be finalised without a valid PO number.

## Adding a PO number to a proposal

1. Open the proposal.
2. Enter the number in the **Purchase order** field.
3. Select **Save PO**.

The message "Purchase order saved." confirms it.

Project Billing removes spaces at the start and end and changes letters to capitals. For example, ` po-77812 ` is saved as `PO-77812`.

To remove a PO number, clear the field and select **Save PO**.

You can add a PO number to any proposal, even when the customer does not require one. It is then shown on the invoice.

## What makes a PO number valid

When the customer requires a PO, the number must be between 4 and 30 characters long, after spaces at the start and end are removed.

A shorter or longer number can be saved on the proposal, but the invoice cannot be finalised with it.

## When the PO is checked

The PO number is checked when you select **Finalise invoice**, not when you save it. If the customer requires a PO and the number is missing or not valid, you see:

"A purchase order number is required for Norrsken Energi AB."

Add or correct the PO number, select **Save PO**, then finalise again.

The check uses the customer's setting at the moment you finalise. If the setting is ticked after a proposal was created, the proposal needs a PO number before it can be finalised.

## On the invoice

The PO number is shown as **Purchase order** on the final invoice. It cannot be changed once the invoice is final. If an invoice went out with the wrong PO number, credit it and bill again. See [Final invoices and corrections](24-final-invoices-and-corrections.md).

## Tips

- Ask the project manager for the PO number before the billing run, not after.
- Some customers issue a new PO each year. Check the date on the PO if the customer has rejected an invoice before.
- Do not invent a placeholder number such as "TBC1" to get past the check. The customer will reject the invoice.
