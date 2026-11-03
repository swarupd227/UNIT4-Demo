# 18. Rounding

Last updated: March 2026

This page explains how Project Billing rounds amounts. It matters most for invoices in a currency other than EUR.

## The rule

Amounts are converted and rounded **line by line**. The total is the **sum of the rounded lines**.

For each line, Project Billing:

1. takes the line's EUR value, including any write-up or write-down,
2. multiplies it by the exchange rate,
3. rounds the result to the decimal places of the invoice currency. This is the line **Amount**,
4. works out the tax on the rounded line amount and rounds that too. This is the line **Tax amount**.

Then:

- **Subtotal** is the sum of the rounded line amounts,
- **Tax** is the sum of the rounded line tax amounts,
- **Total** is Subtotal plus Tax.

The totals are never converted or rounded separately. This means the lines printed on the invoice always add up exactly to the printed total.

## Decimal places

Most currencies are rounded to two decimal places. JPY, ISK and KRW have no decimal places and are rounded to whole units.

Amounts exactly halfway are rounded away from zero. For example, 0.125 is rounded to 0.13, and 170,467.5 JPY is rounded to 170,468 JPY.

## Example

Polar Marine Oy is invoiced in USD with standard VAT at 25.5%. Suppose the rate is 1.0850 and the proposal has three lines of 33.33 EUR each.

| Line | EUR | × 1.0850 | Amount (USD) | Tax 25.5% | Tax amount (USD) |
|---|---|---|---|---|---|
| 1 | 33.33 | 36.16305 | 36.16 | 9.2208 | 9.22 |
| 2 | 33.33 | 36.16305 | 36.16 | 9.2208 | 9.22 |
| 3 | 33.33 | 36.16305 | 36.16 | 9.2208 | 9.22 |

Subtotal 108.48, Tax 27.66, Total 136.14 USD.

Converting the EUR total of 99.99 in one step would give 108.49 USD. Project Billing does not do this. The subtotal is 108.48 USD, because that is what the three printed lines add up to.

## Small differences

Because each line is rounded on its own, the converted total can differ by a few cents from the EUR total times the rate. This is expected and correct. If a customer queries a difference of this kind, explain that each line is converted and rounded separately.

## Hours

Hours are rounded too, but separately. Each time entry is rounded up to the next quarter hour before it is priced. See [Quarter-hour billing](12-quarter-hour-billing.md).

## Agreement discounts and markup

The discount and the expense markup are taken in EUR before conversion. The EUR value of the line is not rounded at that point. Rounding happens once, when the line is converted to the invoice currency.

## Credit notes

Credit note lines are rounded in the same way, to the decimal places of the invoice currency. They are shown as negative amounts. See [Credit notes](25-credit-notes.md).
