using Kestrel.Billing.Data;
using Kestrel.Billing.Helpers;
using Kestrel.Billing.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Services;

public class ProposalService
{
    private readonly BillingContext _db;
    private readonly ExchangeRateService _rates;
    private readonly TaxService _tax;
    private readonly CurrentUser _user;
    private readonly SystemClock _clock;

    public ProposalService(BillingContext db, ExchangeRateService rates, TaxService tax, CurrentUser user, SystemClock clock)
    {
        _db = db;
        _rates = rates;
        _tax = tax;
        _user = user;
        _clock = clock;
    }

    /// <summary>
    /// Builds an invoice proposal for one project, from everything billable up to the period end.
    /// </summary>
    public Invoice CreateProposal(int projectId, DateOnly periodEnd, DateOnly invoiceDate)
    {
        var project = _db.Projects
            .Include(p => p.Customer).ThenInclude(c => c.Rates)
            .Include(p => p.Rates)
            .Include(p => p.Milestones)
            .FirstOrDefault(p => p.Id == projectId);
        if (project == null)
        {
            throw new BillingException("Project not found.");
        }
        var customer = project.Customer;
        var company = _db.Companies.First();

        // Billing holds stop a proposal before anything is calculated.
        if (customer.IsOnHold)
        {
            throw new BillingException(("Billing hold: customer " + customer.Name + " is on hold. " + (customer.HoldReason ?? "")).Trim());
        }
        if (project.IsOnHold)
        {
            throw new BillingException(("Billing hold: project " + project.Code + " is on hold. " + (project.HoldReason ?? "")).Trim());
        }
        if (project.Status == ProjectStatus.Closed)
        {
            throw new BillingException("Project " + project.Code + " is closed.");
        }
        if (invoiceDate < periodEnd)
        {
            throw new BillingException("The invoice date cannot be before the period end.");
        }

        var open = _db.Invoices.Any(i => i.ProjectId == projectId && i.Kind == InvoiceKind.Invoice &&
            (i.Status == InvoiceStatus.Proposal || i.Status == InvoiceStatus.PendingApproval));
        if (open)
        {
            throw new BillingException("Project " + project.Code + " already has an open proposal. Finalise or delete it first.");
        }

        var invoice = new Invoice
        {
            Kind = InvoiceKind.Invoice,
            Status = InvoiceStatus.Proposal,
            CustomerId = customer.Id,
            ProjectId = project.Id,
            PeriodEnd = periodEnd,
            InvoiceDate = invoiceDate,
            Currency = customer.Currency,
            CreatedBy = _user.Name,
            CreatedAt = _clock.Now,
        };

        var rate = _rates.GetRate(company.BaseCurrency, customer.Currency, invoiceDate);
        invoice.ExchangeRate = rate;
        var tax = _tax.Resolve(project.TaxCode, customer, company);
        if (tax.Note != null)
        {
            invoice.Notes = tax.Note;
        }

        // Not-to-exceed: what has been billed already counts against the limit.
        decimal billedToDate = 0m;
        if (project.NotToExceed.HasValue)
        {
            var finals = _db.Invoices.AsNoTracking()
                .Where(i => i.ProjectId == projectId && i.Status == InvoiceStatus.Final)
                .ToList();
            foreach (var f in finals)
            {
                if (f.Kind == InvoiceKind.Invoice)
                {
                    billedToDate += f.BaseSubtotal;
                }
                else
                {
                    billedToDate -= Math.Abs(f.BaseSubtotal);
                }
            }
        }

        var lines = new List<InvoiceLine>();
        var timeSources = new List<(InvoiceLine Line, TimeEntry Entry)>();
        var expenseSources = new List<(InvoiceLine Line, ExpenseEntry Entry)>();
        var running = 0m;
        var held = 0;
        var seq = 1;

        // Time. Fixed-price projects bill milestones, not hours.
        if (project.BillingType == BillingType.TimeAndMaterials)
        {
            var entries = _db.TimeEntries
                .Include(t => t.Employee)
                .Where(t => t.ProjectId == projectId
                            && t.Status == EntryStatus.Approved
                            && t.Billable
                            && t.InvoiceLineId == null
                            && t.Date <= periodEnd)
                .OrderBy(t => t.Date).ThenBy(t => t.Id)
                .ToList();

            foreach (var e in entries)
            {
                var hours = RoundingHelper.RoundHours(e.Hours);
                var unit = BillingHelper.ResolveRate(_db, customer, project, e.Employee.RoleCode);
                var gross = hours * unit;
                var net = BillingHelper.ApplyDiscount(gross, customer.DiscountPercent, LineKind.Time);

                if (project.NotToExceed.HasValue && billedToDate + running + net > project.NotToExceed.Value)
                {
                    held++;
                    continue;
                }

                running += net;
                var line = new InvoiceLine
                {
                    Sequence = seq++,
                    Kind = LineKind.Time,
                    Description = e.Date.ToString("yyyy-MM-dd") + " " + e.Employee.Name + " - " + e.ActivityCode +
                                  (string.IsNullOrWhiteSpace(e.Comment) ? "" : " (" + e.Comment + ")"),
                    Quantity = hours,
                    UnitPrice = unit,
                    DiscountPercent = customer.DiscountPercent,
                    SourceAmount = net,
                    SourceLineId = e.Id,
                };
                lines.Add(line);
                timeSources.Add((line, e));
            }
        }

        // Expenses, at cost plus the project's markup.
        var expenses = _db.Expenses
            .Where(x => x.ProjectId == projectId
                        && x.Status == EntryStatus.Approved
                        && x.Billable
                        && x.InvoiceLineId == null
                        && x.Date <= periodEnd)
            .OrderBy(x => x.Date).ThenBy(x => x.Id)
            .ToList();
        foreach (var x in expenses)
        {
            var amount = BillingHelper.ExpenseWithMarkup(x.Amount, project.ExpenseMarkupPercent);
            amount = BillingHelper.ApplyDiscount(amount, customer.DiscountPercent, LineKind.Expense);

            if (project.NotToExceed.HasValue && billedToDate + running + amount > project.NotToExceed.Value)
            {
                held++;
                continue;
            }

            running += amount;
            var line = new InvoiceLine
            {
                Sequence = seq++,
                Kind = LineKind.Expense,
                Description = x.Date.ToString("yyyy-MM-dd") + " " + x.Description,
                Quantity = 1,
                UnitPrice = amount,
                SourceAmount = amount,
                SourceLineId = x.Id,
            };
            lines.Add(line);
            expenseSources.Add((line, x));
        }

        // Milestones: only completed ones, and only once.
        var milestones = new List<(InvoiceLine Line, Milestone Milestone)>();
        if (project.BillingType == BillingType.FixedPrice)
        {
            foreach (var m in project.Milestones.OrderBy(m => m.PlannedDate))
            {
                if (!m.IsComplete)
                {
                    continue;
                }
                if (m.BilledInvoiceId != null)
                {
                    continue;
                }
                if (m.CompletedOn.HasValue && m.CompletedOn.Value > periodEnd)
                {
                    continue;
                }

                if (project.NotToExceed.HasValue && billedToDate + running + m.Amount > project.NotToExceed.Value)
                {
                    held++;
                    continue;
                }

                running += m.Amount;
                var line = new InvoiceLine
                {
                    Sequence = seq++,
                    Kind = LineKind.Milestone,
                    Description = "Milestone: " + m.Name,
                    Quantity = 1,
                    UnitPrice = m.Amount,
                    SourceAmount = m.Amount,
                    SourceLineId = m.Id,
                };
                lines.Add(line);
                milestones.Add((line, m));
            }
        }

        if (lines.Count == 0)
        {
            if (held > 0)
            {
                throw new BillingException("Nothing can be billed: the not-to-exceed limit of " +
                    BillingHelper.FormatMoney(project.NotToExceed!.Value, company.BaseCurrency) + " has been reached.");
            }
            throw new BillingException("There is nothing to bill on " + project.Code + " up to " + periodEnd.ToString("d MMM yyyy") + ".");
        }

        foreach (var line in lines)
        {
            line.TaxCode = tax.Code;
            line.TaxRate = tax.Rate;
        }
        invoice.Lines = lines;
        Recalculate(invoice);

        if (held > 0)
        {
            invoice.StatusReason = held + (held == 1 ? " entry was" : " entries were") + " held back: the not-to-exceed limit of " +
                BillingHelper.FormatMoney(project.NotToExceed!.Value, company.BaseCurrency) + " is reached.";
        }

        // Small invoices cost more to process than they are worth, so they wait for the next run,
        // unless the project is closing and this is the last chance to bill.
        if (invoice.BaseSubtotal < BillingHelper.MinimumInvoiceAmount && project.Status != ProjectStatus.Closing)
        {
            invoice.Status = InvoiceStatus.Deferred;
            invoice.StatusReason = "Below the minimum invoice amount of " +
                BillingHelper.FormatMoney(BillingHelper.MinimumInvoiceAmount, company.BaseCurrency) +
                ". The entries stay unbilled and are picked up by the next billing run.";
            _db.Invoices.Add(invoice);
            BillingHelper.Audit(_db, _user.Name, "Proposal deferred", project.Code, _clock.Now);
            _db.SaveChanges();
            return invoice;
        }

        _db.Invoices.Add(invoice);
        _db.SaveChanges();

        // Reserve the entries so that no other proposal picks them up.
        foreach (var (line, entry) in timeSources)
        {
            entry.InvoiceLineId = line.Id;
        }
        foreach (var (line, entry) in expenseSources)
        {
            entry.InvoiceLineId = line.Id;
        }

        BillingHelper.Audit(_db, _user.Name, "Proposal created", project.Code + " " + lines.Count + " lines", _clock.Now);
        _db.SaveChanges();
        return invoice;
    }

    /// <summary>
    /// Converts and rounds every line, then adds up the rounded lines.
    /// When the exchange rate is not known yet the lines keep their company-currency value.
    /// </summary>
    public static void Recalculate(Invoice invoice)
    {
        var rate = invoice.ExchangeRate ?? 1m;
        foreach (var line in invoice.Lines)
        {
            var value = line.SourceAmount + line.Adjustment;
            line.Amount = RoundingHelper.Convert(value, rate, invoice.Currency);
            line.TaxAmount = RoundingHelper.LineTax(value, rate, line.TaxRate, invoice.Currency);
        }
        invoice.BaseSubtotal = invoice.Lines.Sum(l => l.SourceAmount + l.Adjustment);
        invoice.Subtotal = RoundingHelper.SumLines(invoice.Lines.Select(l => l.Amount));
        invoice.TaxTotal = RoundingHelper.SumLines(invoice.Lines.Select(l => l.TaxAmount));
        invoice.Total = invoice.Subtotal + invoice.TaxTotal;
    }

    public Invoice? Load(int id)
    {
        return _db.Invoices
            .Include(i => i.Customer)
            .Include(i => i.Project)
            .Include(i => i.Lines.OrderBy(l => l.Sequence))
            .FirstOrDefault(i => i.Id == id);
    }

    /// <summary>Deletes an open proposal and releases its entries for the next run.</summary>
    public void Delete(int id)
    {
        var invoice = Load(id);
        if (invoice == null)
        {
            throw new BillingException("Proposal not found.");
        }
        if (invoice.Status == InvoiceStatus.Final)
        {
            throw new BillingException("A final invoice cannot be deleted. Raise a credit note instead.");
        }

        var lineIds = invoice.Lines.Select(l => l.Id).ToList();
        foreach (var t in _db.TimeEntries.Where(t => t.InvoiceLineId != null && lineIds.Contains(t.InvoiceLineId.Value)))
        {
            t.InvoiceLineId = null;
        }
        foreach (var x in _db.Expenses.Where(x => x.InvoiceLineId != null && lineIds.Contains(x.InvoiceLineId.Value)))
        {
            x.InvoiceLineId = null;
        }
        _db.InvoiceLines.RemoveRange(invoice.Lines);
        _db.Invoices.Remove(invoice);
        BillingHelper.Audit(_db, _user.Name, "Proposal deleted", invoice.Project.Code, _clock.Now);
        _db.SaveChanges();
    }

    public void SetPurchaseOrder(int id, string? po)
    {
        var invoice = Load(id);
        if (invoice == null || InvoiceService.IsLocked(invoice))
        {
            throw new BillingException("This invoice is final. Changes are made with a credit note.");
        }
        invoice.PoNumber = string.IsNullOrWhiteSpace(po) ? null : BillingHelper.NormalisePo(po);
        _db.SaveChanges();
    }
}
