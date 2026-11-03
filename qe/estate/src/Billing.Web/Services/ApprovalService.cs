using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Services;

public class ApprovalService
{
    private readonly BillingContext _db;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public ApprovalService(BillingContext db, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _user = user;
        _clock = clock;
    }

    public List<Invoice> Waiting()
    {
        return _db.Invoices
            .Include(i => i.Customer)
            .Include(i => i.Project)
            .Include(i => i.Lines)
            .Where(i => i.Status == InvoiceStatus.PendingApproval)
            .OrderBy(i => i.Id)
            .ToList();
    }

    public void Approve(int invoiceId)
    {
        if (!_user.IsBillingManager)
        {
            throw new BillingException("Only a billing manager can approve write-downs.");
        }
        var invoice = _db.Invoices.FirstOrDefault(i => i.Id == invoiceId);
        if (invoice == null || invoice.Status != InvoiceStatus.PendingApproval)
        {
            throw new BillingException("This proposal is not waiting for approval.");
        }
        invoice.Status = InvoiceStatus.Proposal;
        invoice.ApprovedBy = _user.Name;
        invoice.ApprovedAt = _clock.Now;
        BillingHelper.Audit(_db, _user.Name, "Write-downs approved", invoice.Id.ToString(), _clock.Now);
        _db.SaveChanges();
    }

    public void Reject(int invoiceId, string? comment)
    {
        if (!_user.IsBillingManager)
        {
            throw new BillingException("Only a billing manager can reject write-downs.");
        }
        var invoice = _db.Invoices.Include(i => i.Lines).FirstOrDefault(i => i.Id == invoiceId);
        if (invoice == null || invoice.Status != InvoiceStatus.PendingApproval)
        {
            throw new BillingException("This proposal is not waiting for approval.");
        }
        foreach (var line in invoice.Lines.Where(l => l.Adjustment < 0))
        {
            line.Adjustment = 0;
            line.AdjustmentReason = null;
        }
        ProposalService.Recalculate(invoice);
        invoice.Status = InvoiceStatus.Proposal;
        BillingHelper.Audit(_db, _user.Name, "Write-downs rejected", invoice.Id + " " + comment, _clock.Now);
        _db.SaveChanges();
    }
}
