using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;

namespace Kestrel.Billing.Services;

public class AdjustmentService
{
    private const decimal WD_LIMIT = 0.10m;

    private readonly BillingContext _db;
    private readonly ProposalService _proposals;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public AdjustmentService(BillingContext db, ProposalService proposals, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _proposals = proposals;
        _user = user;
        _clock = clock;
    }

    /// <summary>
    /// Writes a proposal line up or down. The amount is in the company currency: positive is a
    /// write-up, negative a write-down. Entering 0 removes the adjustment.
    /// </summary>
    public void Adjust(int invoiceId, int lineId, decimal adjustment, string? reason)
    {
        var invoice = _proposals.Load(invoiceId);
        if (invoice == null)
        {
            throw new BillingException("Proposal not found.");
        }
        if (InvoiceService.IsLocked(invoice))
        {
            throw new BillingException("This invoice is final. Changes are made with a credit note.");
        }
        if (invoice.Status == InvoiceStatus.Deferred)
        {
            throw new BillingException("A deferred proposal cannot be adjusted.");
        }

        var line = invoice.Lines.FirstOrDefault(l => l.Id == lineId);
        if (line == null)
        {
            throw new BillingException("Line not found on this proposal.");
        }

        if (adjustment != 0 && string.IsNullOrWhiteSpace(reason))
        {
            throw new BillingException(adjustment > 0
                ? "Enter a reason for the write-up."
                : "Enter a reason for the write-down.");
        }
        if (adjustment < 0 && line.SourceAmount + adjustment < 0)
        {
            throw new BillingException("A write-down cannot take a line below zero.");
        }

        line.Adjustment = adjustment;
        line.AdjustmentReason = adjustment == 0 ? null : reason!.Trim();
        ProposalService.Recalculate(invoice);

        var writeDowns = invoice.Lines.Where(l => l.Adjustment < 0).Sum(l => -l.Adjustment);
        var before = invoice.Lines.Sum(l => l.SourceAmount);
        if (before > 0 && writeDowns / before > WD_LIMIT)
        {
            invoice.Status = InvoiceStatus.PendingApproval;
            invoice.ApprovedBy = null;
            invoice.ApprovedAt = null;
        }
        else if (invoice.Status == InvoiceStatus.PendingApproval)
        {
            invoice.Status = InvoiceStatus.Proposal;
        }

        BillingHelper.Audit(_db, _user.Name, adjustment >= 0 ? "Write-up" : "Write-down",
            $"{invoice.Id}/{line.Sequence} {adjustment} {reason}", _clock.Now);
        _db.SaveChanges();
    }
}
