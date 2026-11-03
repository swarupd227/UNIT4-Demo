using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Pages.Projects;

public class DetailsModel : PageModel
{
    private readonly BillingContext _db;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public DetailsModel(BillingContext db, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _user = user;
        _clock = clock;
    }

    public Project Project { get; set; }
    public List<TimeEntry> Unbilled { get; set; } = new();
    public List<ExpenseEntry> Expenses { get; set; } = new();
    public string? Error { get; set; }

    private bool Load(int id)
    {
        Project = _db.Projects
            .Include(p => p.Customer)
            .Include(p => p.Rates)
            .Include(p => p.Milestones)
            .FirstOrDefault(p => p.Id == id)!;
        if (Project == null)
        {
            return false;
        }
        Unbilled = _db.TimeEntries.Include(t => t.Employee)
            .Where(t => t.ProjectId == id && t.InvoiceLineId == null && t.Status != EntryStatus.Rejected)
            .OrderBy(t => t.Date).ToList()
            .Where(t => t.Date >= _clock.Today.AddMonths(-3)).ToList();
        Expenses = _db.Expenses
            .Where(x => x.ProjectId == id && x.InvoiceLineId == null && x.Status != EntryStatus.Rejected)
            .OrderBy(x => x.Date).ToList();
        return true;
    }

    public IActionResult OnGet(int id)
    {
        return Load(id) ? Page() : NotFound();
    }

    public IActionResult OnPostHold(int id, bool isOnHold, string? holdReason)
    {
        if (!Load(id))
        {
            return NotFound();
        }
        if (isOnHold && string.IsNullOrWhiteSpace(holdReason))
        {
            Error = "Enter a reason for the billing hold.";
            return Page();
        }
        Project.IsOnHold = isOnHold;
        Project.HoldReason = isOnHold ? holdReason!.Trim() : null;
        BillingHelper.Audit(_db, _user.Name, isOnHold ? "Project hold set" : "Project hold released", Project.Code, _clock.Now);
        _db.SaveChanges();
        TempData["Message"] = isOnHold ? "Project " + Project.Code + " is on hold." : "Hold released on " + Project.Code + ".";
        return RedirectToPage(new { id });
    }

    public IActionResult OnPostComplete(int id, int milestoneId)
    {
        if (!Load(id))
        {
            return NotFound();
        }
        var milestone = Project.Milestones.FirstOrDefault(m => m.Id == milestoneId);
        if (milestone == null)
        {
            return NotFound();
        }
        milestone.IsComplete = true;
        milestone.CompletedOn = _clock.Today;
        BillingHelper.Audit(_db, _user.Name, "Milestone complete", Project.Code + " " + milestone.Name, _clock.Now);
        _db.SaveChanges();
        TempData["Message"] = "Milestone " + milestone.Name + " marked complete.";
        return RedirectToPage(new { id });
    }
}
