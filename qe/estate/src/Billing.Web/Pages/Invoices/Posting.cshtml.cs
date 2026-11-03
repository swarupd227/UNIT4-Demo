using Kestrel.Billing.Data;
using Kestrel.Billing.Infrastructure;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Invoices;

public class PostingModel : PageModel
{
    private readonly BillingContext _db;
    private readonly LedgerSync _ledger;

    public PostingModel(BillingContext db, LedgerSync ledger)
    {
        _db = db;
        _ledger = ledger;
    }

    public int Id { get; set; }
    public string? Number { get; set; }

    public IActionResult OnGet(int id)
    {
        var invoice = _db.Invoices.Find(id);
        if (invoice == null)
        {
            return NotFound();
        }
        Id = id;
        Number = invoice.Number;
        return Page();
    }

    public IActionResult OnGetStatus(int id)
    {
        return new JsonResult(new { posted = _ledger.IsPosted(id) });
    }
}
