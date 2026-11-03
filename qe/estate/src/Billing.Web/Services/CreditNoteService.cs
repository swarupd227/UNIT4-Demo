using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Services;

public class CreditNoteService
{
    private readonly BillingContext _db;
    private readonly InvoiceService _invoices;
    private readonly NumberingService _numbering;
    private readonly LedgerSync _ledger;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public CreditNoteService(BillingContext db, InvoiceService invoices, NumberingService numbering,
        LedgerSync ledger, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _invoices = invoices;
        _numbering = numbering;
        _ledger = ledger;
        _user = user;
        _clock = clock;
    }

    public Invoice? LoadOriginal(int invoiceId)
    {
        return _db.Invoices
            .Include(i => i.Customer)
            .Include(i => i.Project)
            .Include(i => i.Lines.OrderBy(l => l.Sequence))
            .FirstOrDefault(i => i.Id == invoiceId && i.Kind == InvoiceKind.Invoice);
    }

    public decimal Remaining(Invoice original)
    {
        return original.Total - _invoices.CreditedSoFar(original.Id);
    }

    /// <summary>
    /// Credits part or all of a final invoice. Amounts are per line, before tax, in the invoice
    /// currency. Tax is credited at the rate charged on the original line.
    /// </summary>
    public async Task<Invoice> CreateAsync(int originalId, Dictionary<int, decimal> creditPerLine, string? reason)
    {
        var original = LoadOriginal(originalId);
        if (original == null || original.Status != InvoiceStatus.Final)
        {
            throw new BillingException("Only a final invoice can be credited.");
        }
        if (string.IsNullOrWhiteSpace(reason))
        {
            throw new BillingException("Enter a reason for the credit note.");
        }

        var note = new Invoice
        {
            Kind = InvoiceKind.CreditNote,
            Status = InvoiceStatus.Final,
            CustomerId = original.CustomerId,
            ProjectId = original.ProjectId,
            PeriodEnd = original.PeriodEnd,
            InvoiceDate = _clock.Today,
            Currency = original.Currency,
            ExchangeRate = original.ExchangeRate,
            OriginalInvoiceId = original.Id,
            Notes = "Credit for invoice " + original.Number + ". " + reason!.Trim(),
            CreatedBy = _user.Name,
            CreatedAt = _clock.Now,
        };

        var seq = 1;
        foreach (var line in original.Lines)
        {
            if (!creditPerLine.TryGetValue(line.Id, out var credit) || credit == 0)
            {
                continue;
            }
            if (credit < 0)
            {
                throw new BillingException("Enter credit amounts as positive numbers.");
            }
            if (credit > line.Amount)
            {
                throw new BillingException("Line " + line.Sequence + " cannot be credited by more than its amount of " +
                    BillingHelper.FormatMoney(line.Amount, original.Currency) + ".");
            }

            var amount = RoundingHelper.CreditAmount(credit, original.Currency);
            note.Lines.Add(new InvoiceLine
            {
                Sequence = seq++,
                Kind = line.Kind,
                Description = "Credit: " + line.Description,
                Quantity = 1,
                UnitPrice = amount,
                SourceAmount = original.ExchangeRate.HasValue && original.ExchangeRate.Value != 0
                    ? amount / original.ExchangeRate.Value
                    : amount,
                Amount = amount,
                TaxCode = line.TaxCode,
                TaxRate = line.TaxRate,
                TaxAmount = RoundingHelper.CreditAmount(credit * line.TaxRate / 100m, original.Currency),
                SourceLineId = line.Id,
            });
        }

        if (note.Lines.Count == 0)
        {
            throw new BillingException("Enter an amount to credit on at least one line.");
        }

        note.Subtotal = RoundingHelper.SumLines(note.Lines.Select(l => l.Amount));
        note.TaxTotal = RoundingHelper.SumLines(note.Lines.Select(l => l.TaxAmount));
        note.Total = note.Subtotal + note.TaxTotal;
        note.BaseSubtotal = note.Lines.Sum(l => l.SourceAmount);

        var remaining = Remaining(original);
        if (Math.Abs(note.Total) > remaining)
        {
            throw new BillingException("The credit of " + BillingHelper.FormatMoney(Math.Abs(note.Total), original.Currency) +
                " is more than the " + BillingHelper.FormatMoney(remaining, original.Currency) +
                " still open on invoice " + original.Number + ".");
        }

        note.Number = _numbering.Next(InvoiceKind.CreditNote);
        note.FinalisedBy = _user.Name;
        note.FinalisedAt = _clock.Now;
        _db.Invoices.Add(note);
        BillingHelper.Audit(_db, _user.Name, "Credit note issued", note.Number + " for " + original.Number, _clock.Now);
        _db.SaveChanges();
        _ledger.Post(note.Id);
        return note;
    }
}
