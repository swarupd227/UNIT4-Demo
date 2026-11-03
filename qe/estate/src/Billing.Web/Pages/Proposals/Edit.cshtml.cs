using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Proposals;

public class EditModel : PageModel
{
    private readonly ProposalService _proposals;
    private readonly AdjustmentService _adjustments;
    private readonly InvoiceService _invoices;

    public EditModel(ProposalService proposals, AdjustmentService adjustments, InvoiceService invoices)
    {
        _proposals = proposals;
        _adjustments = adjustments;
        _invoices = invoices;
    }

    public Invoice Invoice { get; set; }
    public bool Locked { get; set; }
    public string? Error { get; set; }

    private bool Load(int id)
    {
        Invoice = _proposals.Load(id)!;
        if (Invoice == null)
        {
            return false;
        }
        Locked = InvoiceService.IsLocked(Invoice);
        return true;
    }

    public IActionResult OnGet(int id)
    {
        return Load(id) ? Page() : NotFound();
    }

    public IActionResult OnPostPo(int id, string? poNumber)
    {
        try
        {
            _proposals.SetPurchaseOrder(id, poNumber);
            TempData["Message"] = "Purchase order saved.";
            return RedirectToPage(new { id });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Load(id) ? Page() : NotFound();
        }
    }

    public IActionResult OnPostAdjust(int id, int lineId, string? adjustment, string? reason)
    {
        try
        {
            var amount = BillingHelper.ParseMoney(adjustment);
            _adjustments.Adjust(id, lineId, amount, reason);
            var invoice = _proposals.Load(id)!;
            TempData["Message"] = invoice.Status == InvoiceStatus.PendingApproval
                ? "Adjustment saved. The proposal now needs a billing manager's approval."
                : "Adjustment saved.";
            return RedirectToPage(new { id });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Load(id) ? Page() : NotFound();
        }
    }

    public async Task<IActionResult> OnPostFinaliseAsync(int id)
    {
        try
        {
            var invoice = await _invoices.FinaliseAsync(id);
            TempData["Message"] = "Invoice " + invoice.Number + " finalised.";
            return RedirectToPage("/Invoices/Posting", new { id });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Load(id) ? Page() : NotFound();
        }
    }

    public IActionResult OnPostDelete(int id)
    {
        try
        {
            _proposals.Delete(id);
            TempData["Message"] = "Proposal deleted.";
            return RedirectToPage("/Proposals/Index");
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Load(id) ? Page() : NotFound();
        }
    }
}
