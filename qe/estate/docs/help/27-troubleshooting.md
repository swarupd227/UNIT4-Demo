# 27. Troubleshooting: messages and what they mean

Last updated: October 2026

This page lists the messages Project Billing shows when something cannot be done. Names, codes, amounts and dates in the messages are examples.

## Creating a proposal

| Message | What to do |
|---|---|
| "Select a project." | Choose a project in the **Project** list. |
| "Billing hold: customer Ostra Logistics Oy is on hold. Disputed invoices, see case 4471." | The customer is on hold. Ask the person who set the hold. See [Billing holds](05-billing-holds.md). |
| "Billing hold: project P-1011 is on hold. Scope change under review." | The project is on hold. |
| "Project P-1001 is closed." | Closed projects cannot be billed. |
| "The invoice date cannot be before the period end." | Set the invoice date to the period end or later. |
| "Project P-1001 already has an open proposal. Finalise or delete it first." | Open the existing proposal from **Proposals**. |
| "There is nothing to bill on P-1001 up to 31 Oct 2026." | No approved, billable, unbilled entries or completed milestones up to the period end. Check the project page for draft or submitted entries. |
| "Nothing can be billed: the not-to-exceed limit of 20,000.00 EUR has been reached." | See [Not-to-exceed limits](09-not-to-exceed-limits.md). |
| "No rate found for role ARCH on project P-1001." | No hourly rate exists for the role. Contact the finance systems team. |
| "Tax code R3 does not exist." | The project's tax code is wrong. Contact the finance systems team. |
| "Project not found." | The project no longer exists. Reload the page. |

## On a proposal

| Message | What to do |
|---|---|
| "Enter a reason for the write-up." / "Enter a reason for the write-down." | Fill in **Reason** and select **Adjust** again. |
| "A write-down cannot take a line below zero." | Write the line down by no more than its EUR value. |
| "A deferred proposal cannot be adjusted." | See [Minimum invoice amount and deferred proposals](21-minimum-invoice-amount.md). |
| "Line not found on this proposal." | Reload the proposal and try again. |
| "'abc' is not a valid amount." | Enter a number, with a full stop for decimals. |
| "Proposal not found." | The proposal was deleted or finalised by someone else. Check **Proposals** and **Invoices**. |

## Finalising

| Message | What to do |
|---|---|
| "This invoice is already final." | Nothing to do. Open it from **Invoices**. |
| "A deferred proposal cannot be finalised. Its entries are billed in the next run." | Wait for the next billing run. |
| "A purchase order number is required for Norrsken Energi AB." | Add a PO number of 4 to 30 characters and select **Save PO**. |
| "No exchange rate from EUR to CHF on or before 31 Oct 2026. Add the rate before finalising." | Enter a rate effective on or before the invoice date. See [Currencies and exchange rates](17-currencies-and-exchange-rates.md). |
| "This invoice is final. Changes are made with a credit note." | See [Final invoices and corrections](24-final-invoices-and-corrections.md). |
| "A final invoice cannot be deleted. Raise a credit note instead." | As above. |

## Credit notes

| Message | What to do |
|---|---|
| "Enter a reason for the credit note." | Fill in **Reason**. |
| "Enter an amount to credit on at least one line." | Enter an amount in **Credit before tax**. |
| "Enter credit amounts as positive numbers." | Remove the minus sign. |
| "Line 2 cannot be credited by more than its amount of 1,050.00 EUR." | Reduce the amount on that line. |
| "The credit of 1,317.75 EUR is more than the 1,000.00 EUR still open on invoice INV-000123." | The total including tax is too high. Reduce the amounts. |
| "Only a final invoice can be credited." | Proposals cannot be credited. Adjust or delete them instead. |

## Customers, projects and rates

| Message | What to do |
|---|---|
| "The discount must be between 0 and 50%." | Enter a discount from 0 to 50. Use a full stop for decimals. |
| "Enter a reason for the billing hold." | Fill in the reason. |
| "Enter the date the rate is effective from." | Fill in **Effective from**. |
| "Enter a rate greater than zero." | Fill in **Rate**. |

## Other problems

- **The proposal shows amounts in EUR for a foreign customer.** The exchange rate is missing. See [Currencies and exchange rates](17-currencies-and-exchange-rates.md).
- **Finalising takes several seconds.** This is the ledger posting. Wait for the invoice page to open.
- **"Something went wrong"**. Try once more, then contact the finance systems team.
