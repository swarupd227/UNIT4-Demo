using Kestrel.Billing.Data;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Customers;

public class IndexModel : PageModel
{
    private readonly BillingContext _db;

    public IndexModel(BillingContext db)
    {
        _db = db;
    }

    public List<Customer> Customers { get; set; } = new();

    public void OnGet()
    {
        Customers = _db.Customers.OrderBy(c => c.Code).ToList();
    }
}
