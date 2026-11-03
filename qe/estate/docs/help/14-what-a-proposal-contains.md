# 14. What a proposal contains

Last updated: August 2025

Open a proposal from the **Proposals** list. The heading shows its reference, for example **Invoice proposal P00012**. The reference is not the invoice number. The invoice number is given when you finalise.

## Messages at the top

Some proposals show a coloured message under the heading:

- why entries were held back by a not-to-exceed limit, or why the proposal was deferred,
- "No exchange rate to CHF for 31 Oct 2026 yet. Amounts are shown in EUR until the rate is entered." See [Currencies and exchange rates](17-currencies-and-exchange-rates.md).

## The header

| Field | Meaning |
|---|---|
| **Status** | *Proposal*, or *Deferred*. |
| **Invoice number** | "Assigned when finalised". |
| **Project** and **Customer** | Who the invoice is for. |
| **Period end** and **Invoice date** | As entered when the proposal was created. |
| **Currency** | The customer's invoice currency. |
| **Exchange rate** | The rate from EUR, or *Missing*. EUR invoices show 1.0000. |

Below the header there may be a note that will be printed on the invoice, for example the reverse charge wording. See [Reverse charge](16-reverse-charge.md).

The **Purchase order** field and **Save PO** button are below that. See [Purchase orders](20-purchase-orders.md).

## The lines

| Column | Meaning |
|---|---|
| **#** | Line number. |
| **Type** | *Time*, *Expense* or *Milestone*. |
| **Description** | What the line is for. A write-up or write-down reason is shown underneath. |
| **Qty** | Hours for time lines, 1.00 for others. |
| **Unit price (EUR)** | The hourly rate, the expense including markup, or the milestone amount. Always in EUR. |
| **Discount** | The agreement discount, on time lines only. |
| **Adjustment (EUR)** | Any write-up (+) or write-down (−), in EUR. |
| **Amount** | The line amount in the invoice currency, after discount, adjustment and conversion, rounded. |
| **Tax** | The tax code and rate, for example *S 25.5%*. |
| **Tax amount** | The tax on the line, in the invoice currency. |

On the right of each line are the **Adjustment** and **Reason** fields and the **Adjust** button. See [Write-ups and write-downs](19-write-ups-and-write-downs.md).

## The totals

- **Subtotal**: the sum of the line amounts.
- **Tax**: the sum of the line tax amounts.
- **Total**: subtotal plus tax, with the currency.

## Example

A proposal for P-1001 Halden ERP rollout, standard VAT 25.5%, expense markup 10%:

| # | Type | Description | Qty | Unit price (EUR) | Amount (EUR) | Tax | Tax amount |
|---|---|---|---|---|---|---|---|
| 1 | Time | 2026-10-12 Juha Niemi - CONS | 7.50 | 140.00 | 1,050.00 | S 25.5% | 267.75 |
| 2 | Expense | 2026-10-12 Train ticket | 1.00 | 53.46 | 53.46 | S 25.5% | 13.63 |

Subtotal 1,103.46, Tax 281.38, Total 1,384.84 EUR.

Juha Niemi is a senior consultant. Halden Group Oy's agreed rate for that role is 140.00 EUR. The train ticket cost 48.60 EUR, plus 10% markup.

## Buttons

- **Finalise invoice** turns the proposal into a final invoice. See [Finalising an invoice](22-finalising-an-invoice.md).
- **Delete proposal** removes it and returns its entries to unbilled.
