using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Proposals;

public class CreateModel : PageModel
{
    private readonly BillingContext _db;
    private readonly ProposalService _proposals;
    private readonly SystemClock _clock;

    public CreateModel(BillingContext db, ProposalService proposals, SystemClock clock)
    {
        _db = db;
        _proposals = proposals;
        _clock = clock;
    }

    public List<Project> Projects { get; set; } = new();
    public int? ProjectId { get; set; }
    public DateOnly PeriodEnd { get; set; }
    public DateOnly InvoiceDate { get; set; }
    public string? Error { get; set; }

    private void LoadProjects()
    {
        Projects = _db.Projects.Where(p => p.Status != ProjectStatus.Closed).OrderBy(p => p.Code).ToList();
    }

    public void OnGet(int? projectId)
    {
        LoadProjects();
        ProjectId = projectId;
        PeriodEnd = BillingHelper.EndOfMonth(_clock.Today);
        InvoiceDate = PeriodEnd;
    }

    public IActionResult OnPost(int? projectId, DateOnly? periodEnd, DateOnly? invoiceDate)
    {
        LoadProjects();
        ProjectId = projectId;
        PeriodEnd = periodEnd ?? BillingHelper.EndOfMonth(_clock.Today);
        InvoiceDate = invoiceDate ?? PeriodEnd;
        if (projectId == null)
        {
            Error = "Select a project.";
            return Page();
        }
        try
        {
            var invoice = _proposals.CreateProposal(projectId.Value, PeriodEnd, InvoiceDate);
            return RedirectToPage("/Proposals/Edit", new { id = invoice.Id });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Page();
        }
    }
}
