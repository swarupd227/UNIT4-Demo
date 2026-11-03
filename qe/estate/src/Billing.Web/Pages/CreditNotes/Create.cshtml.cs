using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.CreditNotes;

public class CreateModel : PageModel
{
    private readonly CreditNoteService _credits;

    public CreateModel(CreditNoteService credits)
    {
        _credits = credits;
    }

    public Invoice Original { get; set; }
    public decimal Remaining { get; set; }
    public Dictionary<int, string> Entered { get; set; } = new();
    public string? Reason { get; set; }
    public string? Error { get; set; }

    private bool Load(int invoiceId)
    {
        Original = _credits.LoadOriginal(invoiceId)!;
        if (Original == null)
        {
            return false;
        }
        Remaining = _credits.Remaining(Original);
        return true;
    }

    public IActionResult OnGet(int invoiceId)
    {
        return Load(invoiceId) ? Page() : NotFound();
    }

    public async Task<IActionResult> OnPostAsync(int invoiceId, Dictionary<int, string> credit, string? reason)
    {
        Entered = credit ?? new();
        Reason = reason;
        try
        {
            var amounts = new Dictionary<int, decimal>();
            foreach (var (lineId, text) in Entered)
            {
                amounts[lineId] = BillingHelper.ParseMoney(text);
            }
            var note = await _credits.CreateAsync(invoiceId, amounts, reason);
            TempData["Message"] = "Credit note " + note.Number + " issued.";
            return RedirectToPage("/Invoices/Posting", new { id = note.Id });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Load(invoiceId) ? Page() : NotFound();
        }
    }
}
