using Kestrel.Billing.Data;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Services;

public class ExchangeRateService
{
    private readonly BillingContext _db;

    public ExchangeRateService(BillingContext db)
    {
        _db = db;
    }

    /// <summary>
    /// The rate in force on a date: the most recent rate whose effective date is on or before it.
    /// Returns null when no rate has been entered yet.
    /// </summary>
    public decimal? GetRate(string fromCurrency, string toCurrency, DateOnly onDate)
    {
        if (string.Equals(fromCurrency, toCurrency, StringComparison.OrdinalIgnoreCase))
        {
            return 1m;
        }

        var candidates = _db.ExchangeRates.AsNoTracking()
            .Where(r => r.FromCurrency == fromCurrency && r.ToCurrency == toCurrency)
            .ToList();

        var rate = candidates
            .Where(r => r.EffectiveDate <= onDate)
            .OrderByDescending(r => r.EffectiveDate)
            .FirstOrDefault();

        return rate?.Rate;
    }

    public List<ExchangeRate> History(string toCurrency)
    {
        return _db.ExchangeRates.AsNoTracking()
            .Where(r => r.ToCurrency == toCurrency)
            .OrderByDescending(r => r.EffectiveDate)
            .ToList();
    }

    public void Add(string fromCurrency, string toCurrency, DateOnly effective, decimal rate)
    {
        var existing = _db.ExchangeRates.FirstOrDefault(r =>
            r.FromCurrency == fromCurrency && r.ToCurrency == toCurrency && r.EffectiveDate == effective);
        if (existing != null)
        {
            existing.Rate = rate;
        }
        else
        {
            _db.ExchangeRates.Add(new ExchangeRate
            {
                FromCurrency = fromCurrency,
                ToCurrency = toCurrency,
                EffectiveDate = effective,
                Rate = rate,
            });
        }
        _db.SaveChanges();
    }
}
