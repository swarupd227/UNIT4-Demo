using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;

namespace Kestrel.Billing.Services;

public record TaxResult(string Code, decimal Rate, string? Note);

public class TaxService
{
    public const string ReverseChargeCode = "RC";
    public const string ReverseChargeNote = "Reverse charge: VAT to be accounted for by the recipient (Article 196, Directive 2006/112/EC).";

    private readonly BillingContext _db;

    public TaxService(BillingContext db)
    {
        _db = db;
    }

    public TaxResult Resolve(string projectTaxCode, Customer customer, Company company)
    {
        if (BillingHelper.IsReverseCharge(customer, company))
        {
            return new TaxResult(ReverseChargeCode, 0m, ReverseChargeNote);
        }

        var code = _db.TaxCodes.Find(projectTaxCode);
        if (code == null)
        {
            throw new BillingException($"Tax code {projectTaxCode} does not exist.");
        }

        if (code.IsExempt)
        {
            return new TaxResult(code.Code, 0m, $"Exempt from VAT: {code.Description}.");
        }

        return new TaxResult(code.Code, code.Rate, null);
    }

    public List<TaxCode> All()
    {
        return _db.TaxCodes.OrderBy(t => t.Code).ToList();
    }
}
