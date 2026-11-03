namespace Kestrel.Billing.Helpers;

/// <summary>
/// Money rounding for invoices. Every amount on an invoice goes through here.
/// Amounts are converted and rounded line by line, and totals are the sum of the rounded lines,
/// so that the printed lines always add up to the printed total.
/// </summary>
public static class RoundingHelper
{
    /// <summary>Decimal places for a currency (ISO 4217 minor units).</summary>
    public static int MinorUnits(string currency)
    {
        switch (currency?.ToUpperInvariant())
        {
            case "JPY":
            case "ISK":
            case "KRW":
                return 0;
            default:
                return 2;
        }
    }

    public static decimal RoundMoney(decimal amount, string currency)
    {
        return Math.Round(amount, MinorUnits(currency), MidpointRounding.AwayFromZero);
    }

    /// <summary>Converts one line from the company currency and rounds it in the invoice currency.</summary>
    public static decimal Convert(decimal sourceAmount, decimal rate, string currency)
    {
        return RoundMoney(sourceAmount * rate, currency);
    }

    /// <summary>Tax on one line, worked out on the rounded line amount.</summary>
    public static decimal LineTax(decimal sourceAmount, decimal rate, decimal taxPercent, string currency)
    {
        var lineAmount = Convert(sourceAmount, rate, currency);
        return RoundMoney(lineAmount * taxPercent / 100m, currency);
    }

    public static decimal SumLines(IEnumerable<decimal> roundedAmounts)
    {
        return roundedAmounts.Sum();
    }

    /// <summary>Credit note lines are negative. They round the same way as invoice lines.</summary>
    public static decimal CreditAmount(decimal amount, string currency)
    {
        return -RoundMoney(Math.Abs(amount), currency);
    }

    /// <summary>Time is billed in quarter hours, rounded up per entry.</summary>
    public static decimal RoundHours(decimal hours)
    {
        return Math.Ceiling(hours * 4m) / 4m;
    }
}
