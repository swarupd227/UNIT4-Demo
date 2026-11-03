using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Services;

public class InvoiceService
{
    private readonly BillingContext _db;
    private readonly ProposalService _proposals;
    private readonly ExchangeRateService _rates;
    private readonly NumberingService _numbering;
    private readonly LedgerSync _ledger;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public InvoiceService(BillingContext db, ProposalService proposals, ExchangeRateService rates,
        NumberingService numbering, LedgerSync ledger, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _proposals = proposals;
        _rates = rates;
        _numbering = numbering;
        _ledger = ledger;
        _user = user;
        _clock = clock;
    }

    /// <summary>A final invoice can no longer be changed. Corrections go through a credit note.</summary>
    public static bool IsLocked(Invoice invoice)
    {
        return invoice.Status == InvoiceStatus.Final || invoice.Status == InvoiceStatus.Cancelled;
    }

    public async Task<Invoice> FinaliseAsync(int invoiceId)
    {
        var invoice = _proposals.Load(invoiceId);
        if (invoice == null)
        {
            throw new BillingException("Proposal not found.");
        }
        if (IsLocked(invoice))
        {
            throw new BillingException("This invoice is already final.");
        }
        if (invoice.Status == InvoiceStatus.PendingApproval)
        {
            throw new BillingException("Write-downs on this proposal are waiting for a billing manager's approval.");
        }
        if (invoice.Status == InvoiceStatus.Deferred)
        {
            throw new BillingException("A deferred proposal cannot be finalised. Its entries are billed in the next run.");
        }

        var customer = invoice.Customer;
        if (customer.PoRequired && !BillingHelper.IsValidPoNumber(invoice.PoNumber))
        {
            throw new BillingException("A purchase order number is required for " + customer.Name + ".");
        }

        var company = _db.Companies.First();
        var rate = _rates.GetRate(company.BaseCurrency, invoice.Currency, invoice.InvoiceDate);
        if (rate == null)
        {
            throw new BillingException("No exchange rate from " + company.BaseCurrency + " to " + invoice.Currency +
                " on or before " + invoice.InvoiceDate.ToString("d MMM yyyy") + ". Add the rate before finalising.");
        }
        invoice.ExchangeRate = rate;
        ProposalService.Recalculate(invoice);

        invoice.Number = _numbering.Next(InvoiceKind.Invoice);
        invoice.DueDate = BillingHelper.DueDate(invoice.InvoiceDate, customer);
        invoice.Status = InvoiceStatus.Final;
        invoice.FinalisedBy = _user.Name;
        invoice.FinalisedAt = _clock.Now;

        var milestoneIds = invoice.Lines.Where(l => l.Kind == LineKind.Milestone && l.SourceLineId != null)
            .Select(l => l.SourceLineId!.Value).ToList();
        foreach (var m in _db.Milestones.Where(m => milestoneIds.Contains(m.Id)))
        {
            m.BilledInvoiceId = invoice.Id;
        }

        BillingHelper.Audit(_db, _user.Name, "Invoice finalised", invoice.Number, _clock.Now);
        _db.SaveChanges();
        _ledger.Post(invoice.Id);
        return invoice;
    }

    public List<Invoice> List(string? search, InvoiceKind? kind)
    {
        var query = _db.Invoices.AsNoTracking()
            .Include(i => i.Customer)
            .Include(i => i.Project)
            .Where(i => i.Status == InvoiceStatus.Final);
        if (kind.HasValue)
        {
            query = query.Where(i => i.Kind == kind.Value);
        }
        var list = query.ToList();
        if (!string.IsNullOrWhiteSpace(search))
        {
            var s = search.Trim();
            list = list.Where(i =>
                (i.Number ?? "").Contains(s, StringComparison.OrdinalIgnoreCase) ||
                i.Customer.Name.Contains(s, StringComparison.OrdinalIgnoreCase) ||
                i.Project.Code.Contains(s, StringComparison.OrdinalIgnoreCase)).ToList();
        }
        return list.OrderByDescending(i => i.FinalisedAt).ThenByDescending(i => i.Id).ToList();
    }

    public decimal CreditedSoFar(int invoiceId)
    {
        return _db.Invoices.AsNoTracking()
            .Where(c => c.OriginalInvoiceId == invoiceId && c.Kind == InvoiceKind.CreditNote && c.Status == InvoiceStatus.Final)
            .ToList()
            .Sum(c => Math.Abs(c.Total));
    }
}
