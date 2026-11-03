using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Pages.Customers;

public class EditModel : PageModel
{
    private readonly BillingContext _db;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public EditModel(BillingContext db, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _user = user;
        _clock = clock;
    }

    public Customer Customer { get; set; }
    public string? Error { get; set; }

    public IActionResult OnGet(int id)
    {
        Customer = _db.Customers.Include(c => c.Rates).FirstOrDefault(c => c.Id == id)!;
        return Customer == null ? NotFound() : Page();
    }

    public IActionResult OnPost(int id, int paymentTermsDays, string? discountPercent, bool poRequired, bool isOnHold, string? holdReason)
    {
        Customer = _db.Customers.Include(c => c.Rates).FirstOrDefault(c => c.Id == id)!;
        if (Customer == null)
        {
            return NotFound();
        }
        try
        {
            var discount = BillingHelper.ParseMoney(discountPercent);
            if (discount < 0 || discount > 50)
            {
                throw new BillingException("The discount must be between 0 and 50%.");
            }
            if (isOnHold && string.IsNullOrWhiteSpace(holdReason))
            {
                throw new BillingException("Enter a reason for the billing hold.");
            }
            Customer.PaymentTermsDays = paymentTermsDays;
            Customer.DiscountPercent = discount;
            Customer.PoRequired = poRequired;
            Customer.IsOnHold = isOnHold;
            Customer.HoldReason = isOnHold ? holdReason!.Trim() : null;
            BillingHelper.Audit(_db, _user.Name, "Customer changed", Customer.Code, _clock.Now);
            _db.SaveChanges();
            TempData["Message"] = "Customer " + Customer.Code + " saved.";
            return RedirectToPage(new { id });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            return Page();
        }
    }
}
