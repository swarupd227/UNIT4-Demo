using Kestrel.Billing.Data;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Admin;

public class TaxCodesModel : PageModel
{
    private readonly TaxService _tax;

    public TaxCodesModel(TaxService tax)
    {
        _tax = tax;
    }

    public List<TaxCode> Codes { get; set; } = new();

    public void OnGet()
    {
        Codes = _tax.All();
    }
}
