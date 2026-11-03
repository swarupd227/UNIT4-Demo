# 4. Customers

Last updated: September 2025

Each customer carries the settings that decide how its invoices are produced. Select **Customers** in the menu, then select a customer code to open it.

## The customer list

| Column | Meaning |
|---|---|
| **Code** | The customer code, for example C100. |
| **Name** | The customer name, for example Halden Group Oy. |
| **Currency** | The currency the customer is invoiced in. |
| **Country** | The customer's country code. |
| **Payment terms** | The number of days the customer has to pay. |
| **Discount** | The agreement discount, if there is one. |
| **PO required** | *Yes* if invoices need a purchase order number. |
| **Status** | *Active* or *On hold*. |

## Changing a customer

The customer page has these fields:

- **Payment terms (days)**: a whole number from 0 to 120. The due date of each invoice is the invoice date plus this number of days. If it is 0, Project Billing uses 30 days. See [Invoice numbers and due dates](23-invoice-numbers-and-due-dates.md).
- **Agreement discount (%)**: a percentage from 0 to 50, taken off time lines. It is not taken off expenses or milestones. See [Hourly rates and the agreement discount](07-rates.md).
- **Purchase order number required on invoices**: when ticked, an invoice for this customer cannot be finalised without a purchase order number. See [Purchase orders](20-purchase-orders.md).
- **Billing hold** and **Hold reason**: when ticked, no new proposals can be created for any of the customer's projects. See [Billing holds](05-billing-holds.md).

Select **Save**. The message "Customer C100 saved." confirms the change.

Changes apply to proposals created after you save. Existing proposals keep the discount they were created with. Payment terms and the purchase order setting are checked when an invoice is finalised, so they apply to existing proposals too.

## Settings you cannot change here

The customer page also shows:

- **Currency**
- **Country**
- **VAT number**, or *None* if the customer has no VAT number.

These decide the invoice currency and how VAT is charged. They are maintained by the finance systems team. Ask them if one of these is wrong. Do not create proposals for the customer until it is corrected.

## Agreed rates

If the customer has a framework agreement with fixed hourly rates, the page shows an **Agreed rates** table with the **Role** and the **Rate (EUR)**. For example, Halden Group Oy has agreed rates of 140.00 EUR for a senior consultant (SNR) and 175.00 EUR for a solution architect (ARCH). Agreed rates take priority over every other rate. See [Hourly rates and the agreement discount](07-rates.md).

## Messages

- "The discount must be between 0 and 50%."
- "Enter a reason for the billing hold."
- "'abc' is not a valid amount." means the discount could not be read as a number.

Always use a full stop for decimals, for example 5.5. A comma is read as a thousands separator and ignored, so 5,5 is read as 55, and you see "The discount must be between 0 and 50%."
