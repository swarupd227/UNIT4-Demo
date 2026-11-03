# 26. The invoice list and export

Last updated: December 2025

Select **Invoices** in the menu. The page **Invoices and credit notes** lists every final invoice and credit note. Proposals, including deferred ones, are not shown here. They are in the **Proposals** list.

## The list

| Column | Meaning |
|---|---|
| **Number** | INV- or CN- number. Select it to open the document. |
| **Customer** | The customer name. |
| **Project** | The project code. |
| **Invoice date** | The date on the document. |
| **Due date** | The payment due date. Empty for credit notes. |
| **Total** | The total including tax, in the document's currency. Credit notes are negative. |

The list is sorted by when the document was finalised, newest first.

The page shows the latest 200 documents. The line under the table gives the full count, for example "1240 documents, showing the latest 200." Use **Search** to find older ones.

## Searching

- **Search**: enter part of an invoice number, a customer name or a project code, for example `INV-0001`, `Halden` or `P-1001`. Upper and lower case do not matter. Customers are searched by name, not by customer code.
- **Type**: *All*, *Invoices* or *Credit notes*.

Select **Search** to apply the filter.

## Exporting

Select **Export** to download the list as a file called `invoices.csv`.

The export:

- uses the text in the **Search** field, as last applied with **Search**,
- does **not** use the **Type** filter. It always contains both invoices and credit notes that match the search,
- contains **every** matching document, not only the 200 shown on screen,
- is sorted in the same order as the list.

The file has a header line and one line per document. Fields are separated by semicolons:

`Number;Kind;Customer;Project;Invoice date;Due date;Currency;Subtotal;Tax;Total;Status`

| Field | Content |
|---|---|
| Number | INV- or CN- number. |
| Kind | `Invoice` or `CreditNote`. |
| Customer | The customer **code**, for example C100. |
| Project | The project code. |
| Invoice date, Due date | In the form 2026-10-31. The due date is empty for credit notes. |
| Currency | The document currency. |
| Subtotal, Tax, Total | In the document currency, with a full stop for decimals and no thousands separator. Credit notes are negative. |
| Status | `Final`. |

## Opening the file in Excel

The file is UTF-8 text. If Excel puts everything in one column, use **Data > From Text/CSV** and choose **Semicolon** as the delimiter. If amounts appear as dates or text, set the decimal separator to a full stop in the import options.

Amounts are in each document's own currency. Do not add up the **Total** column across currencies. Filter by **Currency** first.

## Month-end report

To export one month's invoices, search by a project code or customer name as needed, export, then filter the **Invoice date** column in Excel. The search box does not filter by date.
