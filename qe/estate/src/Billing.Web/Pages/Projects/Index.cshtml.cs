using Kestrel.Billing.Data;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Pages.Projects;

public class IndexModel : PageModel
{
    private readonly BillingContext _db;

    public IndexModel(BillingContext db)
    {
        _db = db;
    }

    public string? Q { get; set; }
    public List<(Project Project, decimal UnbilledHours)> Rows { get; set; } = new();

    public void OnGet(string? q)
    {
        Q = q;
        var projects = _db.Projects.Include(p => p.Customer).OrderBy(p => p.Code).ToList();
        if (!string.IsNullOrWhiteSpace(q))
        {
            projects = projects.Where(p => p.Code.Contains(q, StringComparison.OrdinalIgnoreCase)
                                           || p.Name.Contains(q, StringComparison.OrdinalIgnoreCase)
                                           || p.Customer.Name.Contains(q, StringComparison.OrdinalIgnoreCase)).ToList();
        }
        var unbilled = _db.TimeEntries
            .Where(t => t.Status == EntryStatus.Approved && t.Billable && t.InvoiceLineId == null)
            .Select(t => new { t.ProjectId, t.Hours })
            .ToList()
            .GroupBy(t => t.ProjectId)
            .ToDictionary(g => g.Key, g => g.Sum(t => t.Hours));
        foreach (var p in projects)
        {
            var hours = p.BillingType == BillingType.FixedPrice ? 0m : unbilled.GetValueOrDefault(p.Id);
            Rows.Add((p, hours));
        }
    }
}
