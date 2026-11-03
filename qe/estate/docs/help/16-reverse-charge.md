# 16. Reverse charge

Last updated: October 2026

When Kestrel sells services to a business in another EU country, the customer accounts for the VAT in its own country. Kestrel's invoice carries no VAT and must say why. This is the reverse charge.

## When reverse charge applies

Project Billing applies reverse charge automatically when **all** of these are true for the customer:

1. The customer is a business. Public sector bodies and private persons are not.
2. The customer has a **VAT number**, shown on the customer page.
3. The customer's **Country** is an EU member state.
4. The customer's country is not Finland.

If any one of these is not true, the project's own tax code is used instead.

## What changes on the invoice

When reverse charge applies:

- every line gets the tax code *RC* at 0%,
- the project's own tax code is ignored,
- the invoice gets this note:

"Reverse charge: VAT to be accounted for by the recipient (Article 196, Directive 2006/112/EC)."

The note is shown on the proposal and the invoice.

## Examples

| Customer | Country | VAT number | Result |
|---|---|---|---|
| Atlas Retail GmbH | DE | DE811234567 | Reverse charge, *RC* 0% |
| Norrsken Energi AB | SE | SE556677889901 | Reverse charge, *RC* 0% |
| Lumo Design GmbH | DE | None | Project tax code, for example *S* 25.5% |
| Halden Group Oy | FI | FI12345678 | Project tax code, Finnish customer |
| Brightwater Utilities Ltd | GB | GB123456789 | Project tax code. The United Kingdom is not in the EU. |
| Vestfold Shipping AS | NO | NO987654321MVA | Project tax code. Norway is not in the EU. |

Lumo Design GmbH is in Germany but has no VAT number, so Finnish VAT is charged.

Customers outside the EU are usually on projects with tax code *Z*. See [VAT and tax codes](15-vat-and-tax-codes.md).

## The EU countries

Project Billing treats these country codes as EU member states: AT, BE, BG, CY, CZ, DE, DK, EE, ES, FI, FR, GR, HR, HU, IE, IT, LT, LU, LV, MT, NL, PL, PT, RO, SE, SI, SK.

Greece is entered as GR.

## When the customer's details change

Reverse charge is decided when the proposal is created. If a customer's VAT number or country is corrected after a proposal was created, delete and recreate the proposal.

Customer country and VAT number are maintained by the finance systems team. Before you finalise the first invoice for a new EU customer, check that the VAT number shown on the customer page matches the customer's purchase order or contract.

## Credit notes

A credit note for a reverse-charged invoice also uses *RC* at 0%, because it copies the tax code of each original line.
