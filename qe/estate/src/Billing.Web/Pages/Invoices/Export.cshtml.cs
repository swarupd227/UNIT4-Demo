using System.Text;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Invoices;

public class ExportModel : PageModel
{
    private readonly InvoiceService _invoices;

    public ExportModel(InvoiceService invoices)
    {
        _invoices = invoices;
    }

    public IActionResult OnGet(string? q)
    {
        var csv = BillingHelper.ExportCsv(_invoices.List(q, null));
        return File(Encoding.UTF8.GetBytes(csv), "text/csv", "invoices.csv");
    }
}
