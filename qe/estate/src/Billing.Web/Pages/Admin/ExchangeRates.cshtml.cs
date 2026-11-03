using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Kestrel.Billing.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.Admin;

public class ExchangeRatesModel : PageModel
{
    private readonly ExchangeRateService _rates;
    private readonly BillingContext _db;

    public ExchangeRatesModel(ExchangeRateService rates, BillingContext db)
    {
        _rates = rates;
        _db = db;
    }

    public List<string> Currencies { get; set; } = new();
    public string Currency { get; set; } = "GBP";
    public List<ExchangeRate> History { get; set; } = new();
    public string? Error { get; set; }

    private void Load(string? currency)
    {
        Currencies = _db.Customers.Select(c => c.Currency).Distinct().ToList()
            .Where(c => c != "EUR").OrderBy(c => c).ToList();
        Currency = currency ?? Currencies.FirstOrDefault() ?? "GBP";
        History = _rates.History(Currency);
    }

    public void OnGet(string? currency)
    {
        Load(currency);
    }

    public IActionResult OnPost(string currency, DateOnly? effectiveDate, string? rate)
    {
        try
        {
            if (effectiveDate == null)
            {
                throw new BillingException("Enter the date the rate is effective from.");
            }
            var value = BillingHelper.ParseMoney(rate);
            if (value <= 0)
            {
                throw new BillingException("Enter a rate greater than zero.");
            }
            _rates.Add("EUR", currency, effectiveDate.Value, value);
            TempData["Message"] = "Rate saved.";
            return RedirectToPage(new { currency });
        }
        catch (BillingException ex)
        {
            Error = ex.Message;
            Load(currency);
            return Page();
        }
    }
}
