using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Services;

/// <summary>
/// Interim billing of fixed-price projects by percentage of completion.
/// Built for the 2023 pilot with two customers. The pilot used its own menu entry.
/// </summary>
public class PercentCompleteBilling
{
    private readonly BillingContext _db;
    private readonly ExchangeRateService _rates;
    private readonly TaxService _tax;
    private readonly SystemClock _clock;

    public PercentCompleteBilling(BillingContext db, ExchangeRateService rates, TaxService tax, SystemClock clock)
    {
        _db = db;
        _rates = rates;
        _tax = tax;
        _clock = clock;
    }

    public Invoice BuildInterimProposal(int projectId, decimal estimatedCost, string user)
    {
        var project = _db.Projects
            .Include(p => p.Customer)
            .Include(p => p.Milestones)
            .FirstOrDefault(p => p.Id == projectId);
        if (project == null || project.BillingType != BillingType.FixedPrice)
        {
            throw new BillingException("Percentage of completion applies to fixed-price projects only.");
        }

        var company = _db.Companies.First();
        var contractValue = project.Milestones.Sum(m => m.Amount);
        var costToDate = _db.TimeEntries
            .Include(t => t.Employee)
            .Where(t => t.ProjectId == projectId && t.Status == EntryStatus.Approved)
            .ToList()
            .Sum(t => t.Hours * (_db.Roles.Find(t.Employee.RoleCode)?.DefaultRate ?? 0m));
        var billedToDate = _db.Invoices
            .Where(i => i.ProjectId == projectId && i.Status == InvoiceStatus.Final && i.Kind == InvoiceKind.Invoice)
            .ToList()
            .Sum(i => i.BaseSubtotal);

        var amount = BillingHelper.PercentCompleteAmount(contractValue, costToDate, estimatedCost, billedToDate);
        if (amount <= 0)
        {
            throw new BillingException("Nothing to bill: billing is ahead of completion.");
        }

        var rate = _rates.GetRate(company.BaseCurrency, project.Customer.Currency, _clock.Today) ?? 1m;
        var tax = _tax.Resolve(project.TaxCode, project.Customer, company);
        var invoice = new Invoice
        {
            Kind = InvoiceKind.Invoice,
            Status = InvoiceStatus.Proposal,
            CustomerId = project.CustomerId,
            ProjectId = project.Id,
            PeriodEnd = _clock.Today,
            InvoiceDate = _clock.Today,
            Currency = project.Customer.Currency,
            ExchangeRate = rate,
            CreatedBy = user,
            CreatedAt = _clock.Now,
            Notes = "Interim billing by percentage of completion.",
        };
        invoice.Lines.Add(new InvoiceLine
        {
            Sequence = 1,
            Kind = LineKind.Milestone,
            Description = "Progress billing " + Math.Round(costToDate / estimatedCost * 100m, 1) + "% complete",
            Quantity = 1,
            UnitPrice = amount,
            SourceAmount = amount,
            TaxCode = tax.Code,
            TaxRate = tax.Rate,
        });
        ProposalService.Recalculate(invoice);
        _db.Invoices.Add(invoice);
        _db.SaveChanges();
        return invoice;
    }
}
