# 5. Billing holds

Last updated: May 2024

A billing hold stops new invoices for a customer or a project. Use it when invoices are disputed, when a contract is being renegotiated, or when the project manager asks you to stop billing while scope is reviewed.

## Customer hold

1. Open the customer from **Customers**.
2. Tick **Billing hold**.
3. Enter the **Hold reason**. Write something a colleague will understand, for example "Disputed invoices, see case 4471."
4. Select **Save**.

A customer hold applies to all of the customer's projects. The customer's **Status** in the customer list changes to *On hold*.

## Project hold

1. Open the project from **Projects**.
2. Tick **Billing hold**.
3. Enter the **Reason**, for example "Scope change under review."
4. Select **Save hold**.

The message "Project P-1011 is on hold." confirms the hold. In the project list, the project's **Status** shows *On hold*.

A project hold applies to that project only. The customer's other projects can still be billed.

## A reason is required

You cannot set a hold without a reason. If the reason is empty you see "Enter a reason for the billing hold."

## Releasing a hold

Untick **Billing hold** and select **Save** (customer) or **Save hold** (project). The reason is cleared. For a project, the message "Hold released on P-1011." confirms it.

Time and expenses recorded during the hold were not lost. They are still unbilled, and the next proposal picks them up as usual.

## What a hold does

While a customer or project is on hold, **Create proposal** stops with a message that names the hold and gives the reason:

- "Billing hold: customer Ostra Logistics Oy is on hold. Disputed invoices, see case 4471."
- "Billing hold: project P-1011 is on hold. Scope change under review."

A hold stops new proposals only. It does not remove or block a proposal that already existed when the hold was set. That proposal can still be adjusted and finalised. If the hold means the invoice must not go out, delete the open proposal. Its entries go back to unbilled.

A hold does not affect invoices that are already final, and it does not stop you issuing credit notes.

## Seeing all holds

The home page has a **Billing holds** list. It shows every customer and project on hold, with the reason. Check it at the start of each billing run, and ask the person who set each hold whether it still applies.
