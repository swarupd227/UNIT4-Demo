using Kestrel.Billing.Data;

namespace Kestrel.Billing.Services;

/// <summary>
/// Invoice and credit note numbers. Numbers are given out only when a document is finalised,
/// so the sequence has no gaps. Invoices and credit notes have separate sequences.
/// </summary>
public class NumberingService
{
    private static readonly object Gate = new();

    private readonly BillingContext _db;

    public NumberingService(BillingContext db)
    {
        _db = db;
    }

    public string Next(InvoiceKind kind)
    {
        lock (Gate)
        {
            var company = _db.Companies.First();
            _db.Entry(company).Reload();
            string number;
            if (kind == InvoiceKind.CreditNote)
            {
                number = "CN-" + company.NextCreditNoteNumber.ToString("000000");
                company.NextCreditNoteNumber++;
            }
            else
            {
                number = "INV-" + company.NextInvoiceNumber.ToString("000000");
                company.NextInvoiceNumber++;
            }
            _db.SaveChanges();
            return number;
        }
    }
}
