using System.Globalization;
using System.Text;
using Kestrel.Billing.Data;
using Kestrel.Billing.Infrastructure;

namespace Kestrel.Billing.Helpers;

/// <summary>
/// Shared billing functions. Started as a few formatting helpers in 2023 and grew from there.
/// Used by the proposal, invoice and credit note code and by several pages.
/// </summary>
public static class BillingHelper
{
    public static readonly string[] EuCountries =
    {
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE",
        "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    };

    public const decimal MinimumInvoiceAmount = 50m;
    public const int DefaultPaymentTerms = 30;

    private static readonly CultureInfo Money = CultureInfo.InvariantCulture;

    // ----- rates -----------------------------------------------------------------------------

    /// <summary>
    /// The hourly rate for a role. A rate agreed with the customer wins over the project's rate card,
    /// and the role's standard rate is used when neither has one.
    /// </summary>
    public static decimal ResolveRate(BillingContext db, Customer customer, Project project, string roleCode)
    {
        var agreed = customer.Rates.FirstOrDefault(r => r.RoleCode == roleCode);
        if (agreed != null)
        {
            return agreed.Rate;
        }

        var card = project.Rates.FirstOrDefault(r => r.RoleCode == roleCode);
        if (card != null)
        {
            return card.Rate;
        }

        var role = db.Roles.Find(roleCode);
        if (role != null)
        {
            return role.DefaultRate;
        }

        throw new BillingException($"No rate found for role {roleCode} on project {project.Code}.");
    }

    /// <summary>Customer agreement discount. Applies to time only, never to expenses or milestones.</summary>
    public static decimal ApplyDiscount(decimal amount, decimal discountPercent, LineKind kind)
    {
        if (kind != LineKind.Time || discountPercent <= 0)
        {
            return amount;
        }
        return amount * (100m - discountPercent) / 100m;
    }

    public static decimal ExpenseWithMarkup(decimal cost, decimal markupPercent)
    {
        if (markupPercent == 0)
        {
            return cost;
        }
        return cost + cost * markupPercent / 100m;
    }

    // ----- dates -----------------------------------------------------------------------------

    public static DateOnly DueDate(DateOnly invoiceDate, Customer customer)
    {
        var days = customer.PaymentTermsDays > 0 ? customer.PaymentTermsDays : DefaultPaymentTerms;
        return invoiceDate.AddDays(days);
    }

    public static string PeriodLabel(DateOnly periodEnd)
    {
        return periodEnd.ToString("MMMM yyyy", CultureInfo.InvariantCulture);
    }

    public static DateOnly EndOfMonth(DateOnly date)
    {
        return new DateOnly(date.Year, date.Month, DateTime.DaysInMonth(date.Year, date.Month));
    }

    public static string FiscalPeriod(DateOnly date)
    {
        // The company's fiscal year follows the calendar year.
        return $"{date.Year}-P{date.Month:00}";
    }

    public static bool IsWeekend(DateOnly date)
    {
        return date.DayOfWeek == DayOfWeek.Saturday || date.DayOfWeek == DayOfWeek.Sunday;
    }

    // ----- tax -------------------------------------------------------------------------------

    public static bool IsEu(string? countryCode)
    {
        return countryCode != null && EuCountries.Contains(countryCode.ToUpperInvariant());
    }

    /// <summary>
    /// Intra-EU business-to-business services: the customer accounts for VAT, so the invoice
    /// carries no VAT and says so.
    /// </summary>
    public static bool IsReverseCharge(Customer customer, Company company)
    {
        if (!customer.IsBusiness)
        {
            return false;
        }
        if (string.IsNullOrWhiteSpace(customer.VatNumber))
        {
            return false;
        }
        return IsEu(customer.CountryCode) && customer.CountryCode != company.CountryCode;
    }

    // ----- formatting ------------------------------------------------------------------------

    public static string FormatMoney(decimal amount, string currency)
    {
        var places = RoundingHelper.MinorUnits(currency);
        return amount.ToString(places == 0 ? "#,##0" : "#,##0.00", Money) + " " + currency;
    }

    public static string FormatAmount(decimal amount, string currency)
    {
        var places = RoundingHelper.MinorUnits(currency);
        return amount.ToString(places == 0 ? "#,##0" : "#,##0.00", Money);
    }

    public static decimal ParseMoney(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return 0m;
        }
        var cleaned = text.Replace(" ", "").Replace(",", "");
        if (decimal.TryParse(cleaned, NumberStyles.Number, CultureInfo.InvariantCulture, out var value))
        {
            return value;
        }
        throw new BillingException($"'{text}' is not a valid amount.");
    }

    public static string StatusLabel(InvoiceStatus status)
    {
        switch (status)
        {
            case InvoiceStatus.Proposal:
                return "Proposal";
            case InvoiceStatus.PendingApproval:
                return "Awaiting approval";
            case InvoiceStatus.Deferred:
                return "Deferred";
            case InvoiceStatus.Final:
                return "Final";
            case InvoiceStatus.Cancelled:
                return "Cancelled";
        }
        return status.ToString();
    }

    public static string CustomerDisplayName(Customer customer)
    {
        return $"{customer.Name} ({customer.Code})";
    }

    public static string LineKindLabel(LineKind kind)
    {
        return kind switch
        {
            LineKind.Time => "Time",
            LineKind.Expense => "Expense",
            LineKind.Milestone => "Milestone",
            _ => kind.ToString(),
        };
    }

    // ----- purchase orders -------------------------------------------------------------------

    public static bool IsValidPoNumber(string? po)
    {
        if (string.IsNullOrWhiteSpace(po))
        {
            return false;
        }
        var trimmed = po.Trim();
        return trimmed.Length >= 4 && trimmed.Length <= 30;
    }

    public static string NormalisePo(string? po)
    {
        return (po ?? "").Trim().ToUpperInvariant();
    }

    // ----- export ----------------------------------------------------------------------------

    /// <summary>Semicolon separated export for the finance team's spreadsheet.</summary>
    public static string ExportCsv(IEnumerable<Invoice> invoices)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Number;Kind;Customer;Project;Invoice date;Due date;Currency;Subtotal;Tax;Total;Status");
        foreach (var i in invoices)
        {
            sb.Append(i.Number ?? "").Append(';')
              .Append(i.Kind).Append(';')
              .Append(i.Customer?.Code).Append(';')
              .Append(i.Project?.Code).Append(';')
              .Append(i.InvoiceDate.ToString("yyyy-MM-dd")).Append(';')
              .Append(i.DueDate?.ToString("yyyy-MM-dd")).Append(';')
              .Append(i.Currency).Append(';')
              .Append(i.Subtotal.ToString(CultureInfo.InvariantCulture)).Append(';')
              .Append(i.TaxTotal.ToString(CultureInfo.InvariantCulture)).Append(';')
              .Append(i.Total.ToString(CultureInfo.InvariantCulture)).Append(';')
              .Append(StatusLabel(i.Status))
              .AppendLine();
        }
        return sb.ToString();
    }

    // ----- percentage of completion ----------------------------------------------------------

    /// <summary>
    /// Interim billing by percentage of completion, for fixed-price projects.
    /// </summary>
    public static decimal PercentCompleteAmount(decimal contractValue, decimal costToDate, decimal estimatedCost, decimal billedToDate)
    {
        if (estimatedCost <= 0)
        {
            return 0m;
        }
        var percent = Math.Min(1m, costToDate / estimatedCost);
        var earned = contractValue * percent;
        return Math.Max(0m, earned - billedToDate);
    }

    public static void Audit(BillingContext db, string user, string action, string detail, DateTime at)
    {
        db.Audit.Add(new AuditEntry { At = at, User = user, Action = action, Detail = detail });
    }
}
