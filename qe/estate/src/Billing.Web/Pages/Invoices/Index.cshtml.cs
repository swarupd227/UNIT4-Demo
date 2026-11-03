using Kestrel.Billing.Data;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Invoices;

public class IndexModel : PageModel
{
    private readonly InvoiceService _invoices;

    public IndexModel(InvoiceService invoices)
    {
        _invoices = invoices;
    }

    public string? Q { get; set; }
    public InvoiceKind? Kind { get; set; }
    public List<Invoice> Invoices { get; set; } = new();

    public void OnGet(string? q, InvoiceKind? kind)
    {
        Q = q;
        Kind = kind;
        Invoices = _invoices.List(q, kind);
    }
}
