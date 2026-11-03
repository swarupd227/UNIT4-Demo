using Kestrel.Billing.Data;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Pages.Invoices;

public class DetailsModel : PageModel
{
    private readonly BillingContext _db;
    private readonly ProposalService _proposals;
    private readonly InvoiceService _invoices;

    public DetailsModel(BillingContext db, ProposalService proposals, InvoiceService invoices)
    {
        _db = db;
        _proposals = proposals;
        _invoices = invoices;
    }

    public Invoice Invoice { get; set; }
    public Invoice? Original { get; set; }
    public decimal Credited { get; set; }
    public List<Invoice> CreditNotes { get; set; } = new();

    public IActionResult OnGet(int id)
    {
        Invoice = _proposals.Load(id)!;
        if (Invoice == null)
        {
            return NotFound();
        }
        if (Invoice.Status != InvoiceStatus.Final)
        {
            return RedirectToPage("/Proposals/Edit", new { id });
        }
        if (Invoice.OriginalInvoiceId != null)
        {
            Original = _db.Invoices.AsNoTracking().FirstOrDefault(o => o.Id == Invoice.OriginalInvoiceId);
        }
        Credited = _invoices.CreditedSoFar(id);
        CreditNotes = _db.Invoices.AsNoTracking()
            .Where(c => c.OriginalInvoiceId == id && c.Kind == InvoiceKind.CreditNote)
            .OrderBy(c => c.Id).ToList();
        return Page();
    }
}
