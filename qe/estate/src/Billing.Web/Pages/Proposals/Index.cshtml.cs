using Kestrel.Billing.Data;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Pages.Proposals;

public class IndexModel : PageModel
{
    private readonly BillingContext _db;

    public IndexModel(BillingContext db)
    {
        _db = db;
    }

    public List<Invoice> Proposals { get; set; } = new();

    public void OnGet()
    {
        Proposals = _db.Invoices
            .Include(i => i.Project)
            .Include(i => i.Customer)
            .Where(i => i.Kind == InvoiceKind.Invoice && i.Status != InvoiceStatus.Final && i.Status != InvoiceStatus.Cancelled)
            .OrderByDescending(i => i.Id)
            .ToList();
    }
}
