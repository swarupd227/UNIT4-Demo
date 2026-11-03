# 7. Hourly rates and the agreement discount

Last updated: June 2025

On a time and materials project, each time entry is priced at an hourly rate. The rate depends on the role of the person who recorded the time. All hourly rates are in EUR.

## Which rate is used

Project Billing looks for a rate in this order and uses the first one it finds:

1. **The customer's agreed rate** for the role. These are shown in the **Agreed rates** table on the customer page.
2. **The project's rate card** for the role. This is shown in the **Rate card** table on the project page.
3. **The role's standard rate.**

An agreed customer rate always wins, even when the project has its own rate card.

## Standard rates

| Role | Code | Standard rate (EUR) |
|---|---|---|
| Junior consultant | JUN | 85.00 |
| Developer | DEV | 110.00 |
| Consultant | CONS | 120.00 |
| Senior consultant | SNR | 150.00 |
| Project manager | MGR | 165.00 |
| Solution architect | ARCH | 185.00 |

## Example

Halden Group Oy has agreed rates for SNR (140.00) and ARCH (175.00). Project P-1003 Halden support retainer has a rate card for SNR (155.00) and MGR (170.00).

On P-1003:

- a senior consultant is billed at 140.00, the customer's agreed rate,
- a project manager is billed at 170.00, from the project rate card,
- a junior consultant is billed at 85.00, the standard rate.

## When the rate is set

The rate is looked up when the proposal is created, using the person's current role. It is shown in the **Unit price (EUR)** column of the proposal. If a rate changes after the proposal is created, delete and recreate the proposal to use the new rate.

If no rate can be found for a role, the proposal is not created and you see "No rate found for role ARCH on project P-1001." Contact the finance systems team.

## The agreement discount

A customer can have an **Agreement discount (%)**, set on the customer page. It is taken off time lines only. It is never taken off expenses or milestones.

On a time line:

- **Unit price (EUR)** shows the hourly rate before discount,
- **Discount** shows the percentage,
- **Amount** is the hours times the rate, less the discount.

For example, 7.50 hours at 140.00 EUR with a 5% discount gives 1,050.00 less 52.50, an amount of 997.50 EUR.

The discount is taken when the proposal is created. Changing the discount on the customer does not change proposals that already exist.

If the customer has a framework discount and agreed rates at the same time, both apply: the agreed rate is used, and the discount is then taken off it. Check the customer's contract if you are not sure this is intended.
