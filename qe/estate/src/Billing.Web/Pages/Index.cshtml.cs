using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Pages;

public class IndexModel : PageModel
{
    private readonly BillingContext _db;
    private readonly SystemClock _clock;

    public IndexModel(BillingContext db, SystemClock clock)
    {
        _db = db;
        _clock = clock;
    }

    public DateOnly PeriodEnd { get; set; }
    public int OpenProposals { get; set; }
    public int AwaitingApproval { get; set; }
    public int ProjectsToBill { get; set; }
    public int FinalisedThisMonth { get; set; }
    public List<(string Name, string Reason)> Holds { get; set; } = new();

    public void OnGet()
    {
        PeriodEnd = BillingHelper.EndOfMonth(_clock.Today);
        OpenProposals = _db.Invoices.Count(i => i.Status == InvoiceStatus.Proposal);
        AwaitingApproval = _db.Invoices.Count(i => i.Status == InvoiceStatus.PendingApproval);
        ProjectsToBill = _db.TimeEntries
            .Where(t => t.Status == EntryStatus.Approved && t.Billable && t.InvoiceLineId == null && t.Date <= PeriodEnd)
            .Select(t => t.ProjectId).Distinct().Count();
        var monthStart = new DateOnly(_clock.Today.Year, _clock.Today.Month, 1);
        FinalisedThisMonth = _db.Invoices.Count(i => i.Status == InvoiceStatus.Final && i.Kind == InvoiceKind.Invoice && i.InvoiceDate >= monthStart);
        foreach (var c in _db.Customers.Where(c => c.IsOnHold).OrderBy(c => c.Name))
        {
            Holds.Add((c.Name, c.HoldReason ?? ""));
        }
        foreach (var p in _db.Projects.Include(p => p.Customer).Where(p => p.IsOnHold).OrderBy(p => p.Code))
        {
            Holds.Add((p.Code + " " + p.Name, p.HoldReason ?? ""));
        }
    }
}
