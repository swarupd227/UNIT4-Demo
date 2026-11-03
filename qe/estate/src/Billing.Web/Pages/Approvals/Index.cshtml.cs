using Kestrel.Billing.Data;
using Kestrel.Billing.Infrastructure;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Approvals;

public class IndexModel : PageModel
{
    private readonly ApprovalService _approvals;

    public IndexModel(ApprovalService approvals)
    {
        _approvals = approvals;
    }

    public List<Invoice> Waiting { get; set; } = new();
    public string? Error { get; set; }

    public void OnGet()
    {
        Waiting = _approvals.Waiting();
    }

    public IActionResult OnPostApprove(int id)
    {
        try
        {
            _approvals.Approve(id);
            TempData["Message"] = "Write-downs approved.";
            return RedirectToPage();
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            Waiting = _approvals.Waiting();
            return Page();
        }
    }

    public IActionResult OnPostReject(int id, string? comment)
    {
        try
        {
            _approvals.Reject(id, comment);
            TempData["Message"] = "Write-downs rejected and removed.";
            return RedirectToPage();
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            Waiting = _approvals.Waiting();
            return Page();
        }
    }
}
