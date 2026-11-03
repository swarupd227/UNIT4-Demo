# 17. Currencies and exchange rates

Last updated: March 2026

Kestrel's company currency is the euro. Rates, expenses, milestones, adjustments and limits are all held in EUR. Each customer is invoiced in its own currency, shown on the customer page. When that currency is not EUR, every line is converted.

## Exchange rates

Select **Exchange rates** in the menu. The page explains: "Rates from EUR. An invoice uses the latest rate whose effective date is on or before the invoice date."

A rate says how much of the customer's currency one euro buys. For example, a GBP rate of 0.8642 means 100.00 EUR is invoiced as 86.42 GBP.

The table shows the **Currency**, **Effective from** date and **Rate** for one currency at a time, newest first. Use **Show** to pick the currency. The list contains every currency that a customer is invoiced in, apart from EUR.

## Which rate an invoice uses

An invoice uses the latest rate whose **Effective from** date is on or before its **Invoice date**. A rate effective from a later date is not used, even if it was entered earlier.

For example, if GBP rates are effective from 1 Sep 2026 and 1 Oct 2026, an invoice dated 31 Oct 2026 uses the 1 October rate. An invoice dated 30 Sep 2026 uses the 1 September rate.

The rate is looked up when the proposal is created, and again when you finalise. If a new rate was entered in between, the invoice is recalculated with it when you finalise.

EUR invoices always use a rate of 1.

## Entering a rate

1. Select the **Currency**.
2. Enter the **Effective from** date.
3. Enter the **Rate**. Use a full stop for decimals, for example 0.8642. A comma is read as a thousands separator and ignored.
4. Select **Save rate**.

The message "Rate saved." confirms it. If a rate already exists for that currency and date, it is replaced.

Messages:

- "Enter the date the rate is effective from."
- "Enter a rate greater than zero."

Exchange rates are normally entered by a billing manager from the treasury rate sheet at the start of each month.

## When no rate exists yet

If there is no rate on or before the invoice date, the proposal is still created. The **Exchange rate** shows *Missing*, and this message is shown:

"No exchange rate to CHF for 31 Oct 2026 yet. Amounts are shown in EUR until the rate is entered."

The amounts on the proposal are then the EUR values. The invoice cannot be finalised until a rate is entered. If you try, you see:

"No exchange rate from EUR to CHF on or before 31 Oct 2026. Add the rate before finalising."

Enter a rate with an **Effective from** date on or before the invoice date, then select **Finalise invoice** again. A rate effective from a later date, for example 1 Nov 2026, does not help an invoice dated 31 Oct 2026.

## Conversion and rounding

Each line is converted from EUR and rounded on its own. The totals are the sum of the rounded lines. See [Rounding](18-rounding.md).

The **Unit price (EUR)** and **Adjustment (EUR)** columns on a proposal always stay in EUR. Only the **Amount**, **Tax amount** and totals are in the invoice currency.

## Credit notes

A credit note uses the same exchange rate as the invoice it credits. Credit amounts are entered in the invoice currency.
