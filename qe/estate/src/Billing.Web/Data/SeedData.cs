using Kestrel.Billing.Helpers;
using Kestrel.Billing.Services;

namespace Kestrel.Billing.Data;

/// <summary>
/// Test data for the billing test environment. Loaded into an empty database on start-up.
/// The data is fixed: the same seed always produces the same customers, entries and invoices,
/// so automated tests can rely on exact amounts.
/// </summary>
public static class SeedData
{
    private static readonly DateOnly HistoryStart = new(2024, 1, 1);
    private static readonly DateOnly HistoryEnd = new(2026, 9, 30);
    private static readonly DateOnly VatChange = new(2024, 9, 1);
    private static readonly DateTime SeededAt = new(2026, 10, 1, 6, 0, 0, DateTimeKind.Utc);

    private record ProjectSpec(
        string Code, string Name, string Customer, BillingType Type, string Tax, decimal Markup,
        decimal? Nte, DateOnly Start, string[] Team, bool RandomHistory, ProjectStatus Status = ProjectStatus.Active,
        string? Hold = null);

    public static void Load(BillingContext db)
    {
        var company = new Company
        {
            Code = "KCG",
            Name = "Kestrel Consulting Oy",
            BaseCurrency = "EUR",
            CountryCode = "FI",
        };
        db.Companies.Add(company);

        db.Roles.AddRange(
            new Role { Code = "JUN", Name = "Junior consultant", DefaultRate = 85m },
            new Role { Code = "DEV", Name = "Developer", DefaultRate = 110m },
            new Role { Code = "CONS", Name = "Consultant", DefaultRate = 120m },
            new Role { Code = "SNR", Name = "Senior consultant", DefaultRate = 150m },
            new Role { Code = "MGR", Name = "Project manager", DefaultRate = 165m },
            new Role { Code = "ARCH", Name = "Solution architect", DefaultRate = 185m });

        db.TaxCodes.AddRange(
            new TaxCode { Code = "S", Description = "Standard rate", Rate = 25.5m },
            new TaxCode { Code = "R1", Description = "Reduced rate", Rate = 14m },
            new TaxCode { Code = "R2", Description = "Reduced rate", Rate = 10m },
            new TaxCode { Code = "E", Description = "health and social care services", Rate = 0m, IsExempt = true },
            new TaxCode { Code = "Z", Description = "Outside the scope of Finnish VAT (services to non-EU businesses)", Rate = 0m });

        var employees = new Dictionary<string, Employee>
        {
            ["E01"] = new() { Name = "Aino Makela", RoleCode = "ARCH" },
            ["E02"] = new() { Name = "Juha Niemi", RoleCode = "SNR" },
            ["E03"] = new() { Name = "Laura Koskinen", RoleCode = "CONS" },
            ["E04"] = new() { Name = "Petri Heikkinen", RoleCode = "DEV" },
            ["E05"] = new() { Name = "Emma Lindqvist", RoleCode = "JUN" },
            ["E06"] = new() { Name = "Oskari Rantanen", RoleCode = "MGR" },
            ["E07"] = new() { Name = "Sara Holm", RoleCode = "SNR" },
            ["E08"] = new() { Name = "Ville Korhonen", RoleCode = "CONS" },
            ["E09"] = new() { Name = "Noora Salo", RoleCode = "DEV" },
            ["E10"] = new() { Name = "Henrik Dahl", RoleCode = "CONS" },
            ["E11"] = new() { Name = "Elina Virta", RoleCode = "JUN" },
            ["E12"] = new() { Name = "Timo Lehto", RoleCode = "SNR" },
        };
        db.Employees.AddRange(employees.Values);

        var customers = new Dictionary<string, Customer>
        {
            ["C100"] = new() { Code = "C100", Name = "Halden Group Oy", Currency = "EUR", CountryCode = "FI", VatNumber = "FI12345678" },
            ["C110"] = new() { Code = "C110", Name = "Brightwater Utilities Ltd", Currency = "GBP", CountryCode = "GB", VatNumber = "GB123456789", PaymentTermsDays = 45 },
            ["C120"] = new() { Code = "C120", Name = "Norrsken Energi AB", Currency = "SEK", CountryCode = "SE", VatNumber = "SE556677889901", PoRequired = true },
            ["C130"] = new() { Code = "C130", Name = "Vestfold Shipping AS", Currency = "NOK", CountryCode = "NO", VatNumber = "NO987654321MVA" },
            ["C140"] = new() { Code = "C140", Name = "Meridian Health Services Oy", Currency = "EUR", CountryCode = "FI", VatNumber = "FI23456789", PaymentTermsDays = 14 },
            ["C150"] = new() { Code = "C150", Name = "Atlas Retail GmbH", Currency = "EUR", CountryCode = "DE", VatNumber = "DE811234567" },
            ["C160"] = new() { Code = "C160", Name = "Lumo Design GmbH", Currency = "EUR", CountryCode = "DE" },
            ["C170"] = new() { Code = "C170", Name = "Sakura Components KK", Currency = "JPY", CountryCode = "JP", PaymentTermsDays = 60 },
            ["C180"] = new() { Code = "C180", Name = "Pacific Freight Inc", Currency = "USD", CountryCode = "US" },
            ["C190"] = new() { Code = "C190", Name = "Alpine Precision AG", Currency = "CHF", CountryCode = "CH", VatNumber = "CHE-123.456.789" },
            ["C200"] = new() { Code = "C200", Name = "Koivula Municipality", Currency = "EUR", CountryCode = "FI", IsBusiness = false, PoRequired = true, PaymentTermsDays = 21 },
            ["C210"] = new() { Code = "C210", Name = "Ostra Logistics Oy", Currency = "EUR", CountryCode = "FI", VatNumber = "FI34567890", IsOnHold = true, HoldReason = "Disputed invoices, see case 4471." },
            ["C220"] = new() { Code = "C220", Name = "Polar Marine Oy", Currency = "USD", CountryCode = "FI", VatNumber = "FI45678901" },
        };
        db.Customers.AddRange(customers.Values);

        // Rates agreed in the Halden framework agreement.
        customers["C100"].Rates.Add(new CustomerRate { RoleCode = "SNR", Rate = 140m });
        customers["C100"].Rates.Add(new CustomerRate { RoleCode = "ARCH", Rate = 175m });

        var specs = new[]
        {
            new ProjectSpec("P-1001", "Halden ERP rollout", "C100", BillingType.TimeAndMaterials, "S", 10m, null, new(2024, 1, 1), new[] { "E02", "E03", "E06" }, true),
            new ProjectSpec("P-1002", "Halden data platform", "C100", BillingType.TimeAndMaterials, "S", 0m, null, new(2024, 6, 1), new[] { "E04", "E08", "E09" }, true),
            new ProjectSpec("P-1003", "Halden support retainer", "C100", BillingType.TimeAndMaterials, "S", 0m, null, new(2024, 1, 1), new[] { "E05", "E06", "E07" }, true),
            new ProjectSpec("P-1010", "Brightwater asset survey", "C110", BillingType.TimeAndMaterials, "Z", 0m, null, new(2025, 2, 1), new[] { "E10", "E12" }, true),
            new ProjectSpec("P-1011", "Brightwater network study", "C110", BillingType.TimeAndMaterials, "Z", 0m, null, new(2026, 3, 1), new[] { "E10" }, true, Hold: "Scope change under review."),
            new ProjectSpec("P-1020", "Norrsken grid analytics", "C120", BillingType.TimeAndMaterials, "S", 0m, null, new(2025, 9, 1), new[] { "E03", "E07" }, true),
            new ProjectSpec("P-1030", "Vestfold fleet optimisation", "C130", BillingType.TimeAndMaterials, "Z", 15m, null, new(2025, 1, 1), new[] { "E12", "E04" }, true),
            new ProjectSpec("P-1040", "Meridian clinical scheduling", "C140", BillingType.TimeAndMaterials, "E", 12m, null, new(2024, 4, 1), new[] { "E08", "E11" }, true),
            new ProjectSpec("P-1050", "Atlas store analytics", "C150", BillingType.TimeAndMaterials, "S", 0m, null, new(2025, 5, 1), new[] { "E09", "E04" }, true),
            new ProjectSpec("P-1060", "Lumo brand system", "C160", BillingType.TimeAndMaterials, "S", 0m, null, new(2024, 3, 1), new[] { "E03", "E01" }, true),
            new ProjectSpec("P-1070", "Sakura supplier portal", "C170", BillingType.TimeAndMaterials, "Z", 0m, null, new(2025, 11, 1), new[] { "E03", "E09" }, true),
            new ProjectSpec("P-1080", "Pacific freight tracking", "C180", BillingType.FixedPrice, "Z", 0m, null, new(2026, 4, 1), new[] { "E01", "E04", "E09" }, true),
            new ProjectSpec("P-1081", "Pacific customs integration", "C180", BillingType.TimeAndMaterials, "Z", 0m, null, new(2025, 8, 1), new[] { "E01", "E10" }, true),
            new ProjectSpec("P-1090", "Alpine MES upgrade", "C190", BillingType.TimeAndMaterials, "Z", 0m, null, new(2026, 10, 1), new[] { "E01" }, false),
            new ProjectSpec("P-1100", "Koivula citizen services", "C200", BillingType.TimeAndMaterials, "S", 0m, 20000m, new(2026, 6, 1), new[] { "E01", "E02", "E03" }, false),
            new ProjectSpec("P-1101", "Koivula permit system", "C200", BillingType.FixedPrice, "S", 0m, null, new(2026, 5, 1), new[] { "E04", "E09" }, false),
            new ProjectSpec("P-1120", "Ostra warehouse WMS", "C210", BillingType.TimeAndMaterials, "S", 0m, null, new(2025, 3, 1), new[] { "E08", "E12" }, true),
            new ProjectSpec("P-1130", "Polar vessel reporting", "C220", BillingType.TimeAndMaterials, "S", 0m, null, new(2025, 10, 1), new[] { "E02", "E03" }, true),
            new ProjectSpec("P-1131", "Polar crew app fixes", "C220", BillingType.TimeAndMaterials, "S", 0m, null, new(2026, 10, 1), new[] { "E05" }, false),
            new ProjectSpec("P-1132", "Polar legacy closeout", "C220", BillingType.TimeAndMaterials, "S", 0m, null, new(2026, 10, 1), new[] { "E05" }, false, ProjectStatus.Closing),
        };

        var projects = new Dictionary<string, Project>();
        foreach (var s in specs)
        {
            var p = new Project
            {
                Code = s.Code,
                Name = s.Name,
                Customer = customers[s.Customer],
                BillingType = s.Type,
                Status = s.Status,
                TaxCode = s.Tax,
                ExpenseMarkupPercent = s.Markup,
                NotToExceed = s.Nte,
                IsOnHold = s.Hold != null,
                HoldReason = s.Hold,
                ProjectManager = "Oskari Rantanen",
            };
            projects[s.Code] = p;
            db.Projects.Add(p);
        }

        // Halden support has its own rate card. The framework agreement still wins where it has a rate.
        projects["P-1003"].Rates.Add(new ProjectRate { RoleCode = "SNR", Rate = 155m });
        projects["P-1003"].Rates.Add(new ProjectRate { RoleCode = "MGR", Rate = 170m });
        projects["P-1081"].Rates.Add(new ProjectRate { RoleCode = "ARCH", Rate = 195m });

        projects["P-1080"].Milestones.AddRange(new[]
        {
            new Milestone { Name = "Discovery", Amount = 12000m, PlannedDate = new(2026, 6, 30), IsComplete = true, CompletedOn = new(2026, 6, 26) },
            new Milestone { Name = "Solution design", Amount = 18000m, PlannedDate = new(2026, 10, 15), IsComplete = true, CompletedOn = new(2026, 10, 16) },
            new Milestone { Name = "Build and test", Amount = 30000m, PlannedDate = new(2026, 12, 18) },
            new Milestone { Name = "Go-live support", Amount = 10000m, PlannedDate = new(2027, 2, 26) },
        });
        projects["P-1101"].Milestones.AddRange(new[]
        {
            new Milestone { Name = "Requirements sign-off", Amount = 8000m, PlannedDate = new(2026, 9, 30), IsComplete = true, CompletedOn = new(2026, 10, 9) },
            new Milestone { Name = "Pilot release", Amount = 14000m, PlannedDate = new(2026, 12, 11) },
        });

        AddExchangeRates(db);
        db.SaveChanges();

        var random = new Random(20231);
        var entries = new List<TimeEntry>();
        var expenses = new List<ExpenseEntry>();

        // Three years of recorded time.
        foreach (var s in specs.Where(s => s.RandomHistory))
        {
            for (var month = s.Start; month <= HistoryEnd; month = month.AddMonths(1))
            {
                var count = random.Next(4, 10);
                for (var i = 0; i < count; i++)
                {
                    var day = random.Next(1, DateTime.DaysInMonth(month.Year, month.Month) + 1);
                    var date = new DateOnly(month.Year, month.Month, day);
                    if (BillingHelper.IsWeekend(date))
                    {
                        date = date.AddDays(date.DayOfWeek == DayOfWeek.Saturday ? -1 : 1);
                        if (date.Month != month.Month)
                        {
                            date = date.AddDays(-3);
                        }
                    }
                    var status = random.Next(100) < 96 ? EntryStatus.Approved : EntryStatus.Rejected;
                    entries.Add(new TimeEntry
                    {
                        Project = projects[s.Code],
                        Employee = employees[s.Team[random.Next(s.Team.Length)]],
                        Date = date,
                        Hours = new[] { 2m, 3.5m, 4m, 6m, 7.5m, 7.5m, 8m }[random.Next(7)],
                        ActivityCode = new[] { "CONS", "CONS", "WORKSHOP", "ANALYSIS", "BUILD", "TEST" }[random.Next(6)],
                        Billable = random.Next(100) < 93,
                        Status = status,
                    });
                }
                if (random.Next(100) < 35)
                {
                    expenses.Add(new ExpenseEntry
                    {
                        Project = projects[s.Code],
                        Date = new DateOnly(month.Year, month.Month, random.Next(1, 27)),
                        Description = new[] { "Train ticket", "Hotel, one night", "Taxi", "Flight", "Workshop venue" }[random.Next(5)],
                        Amount = new[] { 48.60m, 129.00m, 36.20m, 312.40m, 450.00m }[random.Next(5)],
                        Status = EntryStatus.Approved,
                    });
                }
            }
        }

        // Specific history that tests rely on.
        void Time(string project, string employee, DateOnly date, decimal hours, EntryStatus status = EntryStatus.Approved,
            bool billable = true, string activity = "CONS", string? comment = null)
        {
            entries.Add(new TimeEntry
            {
                Project = projects[project],
                Employee = employees[employee],
                Date = date,
                Hours = hours,
                Status = status,
                Billable = billable,
                ActivityCode = activity,
                Comment = comment,
            });
        }

        void Expense(string project, DateOnly date, string description, decimal amount, EntryStatus status = EntryStatus.Approved)
        {
            expenses.Add(new ExpenseEntry { Project = projects[project], Date = date, Description = description, Amount = amount, Status = status });
        }

        // Lumo, September 2026: the invoice that is later part-credited.
        entries.RemoveAll(e => e.Project.Code == "P-1060" && e.Date.Year == 2026 && e.Date.Month == 9);
        expenses.RemoveAll(e => e.Project.Code == "P-1060" && e.Date.Year == 2026 && e.Date.Month == 9);
        Time("P-1060", "E01", new(2026, 9, 14), 8m, activity: "WORKSHOP");
        Time("P-1060", "E03", new(2026, 9, 15), 7.5m);

        // Koivula: billed close to its not-to-exceed limit.
        for (var d = 0; d < 8; d++)
        {
            Time("P-1100", "E03", new DateOnly(2026, 6, 1).AddDays(d + (d >= 5 ? 2 : 0)), 7.5m);
        }
        Time("P-1100", "E03", new(2026, 6, 15), 5m);
        for (var d = 0; d < 5; d++)
        {
            Time("P-1100", "E02", new DateOnly(2026, 8, 3).AddDays(d), 8m);
        }
        Time("P-1100", "E02", new(2026, 8, 10), 4m);
        Time("P-1100", "E01", new(2026, 9, 7), 5m, activity: "ANALYSIS");
        Time("P-1100", "E01", new(2026, 9, 8), 5m, activity: "ANALYSIS");
        Time("P-1100", "E02", new(2026, 9, 9), 7.5m);
        Time("P-1100", "E02", new(2026, 9, 10), 7.5m);

        // October 2026: the current billing period.
        Time("P-1001", "E03", new(2026, 10, 5), 7.5m);
        Time("P-1001", "E02", new(2026, 10, 12), 6m, activity: "WORKSHOP");
        Time("P-1001", "E03", new(2026, 10, 20), 4m, EntryStatus.Draft);
        Time("P-1001", "E02", new(2026, 10, 29), 3m, EntryStatus.Submitted);
        Time("P-1001", "E06", new(2026, 10, 30), 2m, billable: false, activity: "ADMIN");
        Time("P-1001", "E02", new(2026, 10, 31), 1.5m, comment: "Cutover check");
        Time("P-1001", "E03", new(2026, 11, 2), 5m);

        Time("P-1002", "E04", new(2026, 10, 6), 8m, activity: "BUILD");
        Time("P-1002", "E08", new(2026, 10, 15), 6m);
        Expense("P-1002", new(2026, 10, 15), "Train Helsinki - Tampere return", 120.00m);

        Time("P-1003", "E07", new(2026, 10, 7), 4m);
        Time("P-1003", "E06", new(2026, 10, 8), 2m, activity: "ADMIN");
        Time("P-1003", "E05", new(2026, 10, 9), 8m, activity: "TEST");

        Time("P-1010", "E10", new(2026, 10, 13), 7m, activity: "ANALYSIS");
        Time("P-1011", "E10", new(2026, 10, 14), 6m, activity: "ANALYSIS");

        Time("P-1020", "E07", new(2026, 10, 1), 0.25m, comment: "Call with grid operator");
        Time("P-1020", "E07", new(2026, 10, 2), 0.25m, comment: "Call with grid operator");
        Time("P-1020", "E03", new(2026, 10, 5), 7.5m, activity: "ANALYSIS");

        Time("P-1030", "E12", new(2026, 10, 22), 6m, activity: "WORKSHOP");

        Time("P-1040", "E08", new(2026, 10, 21), 6m);
        Expense("P-1040", new(2026, 10, 21), "Hotel Oulu, two nights", 250.00m);

        Time("P-1050", "E09", new(2026, 10, 14), 5m, activity: "BUILD");
        Time("P-1060", "E03", new(2026, 10, 19), 3m);

        Time("P-1070", "E03", new(2026, 10, 7), 0.25m, comment: "Supplier call");
        Time("P-1070", "E09", new(2026, 10, 8), 8m, activity: "BUILD");

        Time("P-1080", "E04", new(2026, 10, 12), 8m, activity: "BUILD");
        Time("P-1080", "E09", new(2026, 10, 13), 8m, activity: "BUILD");

        Time("P-1081", "E01", new(2026, 10, 26), 4m, activity: "ANALYSIS");

        Time("P-1090", "E01", new(2026, 10, 20), 6m, activity: "WORKSHOP");

        Time("P-1100", "E03", new(2026, 10, 6), 7.5m);
        Time("P-1100", "E02", new(2026, 10, 7), 6m);
        Time("P-1100", "E01", new(2026, 10, 8), 2m, activity: "ANALYSIS");

        Time("P-1120", "E08", new(2026, 10, 9), 7.5m);

        Time("P-1130", "E02", new(2026, 10, 12), 8m, activity: "ANALYSIS");
        Time("P-1130", "E03", new(2026, 10, 13), 8m);
        Time("P-1130", "E03", new(2026, 10, 14), 2.1m, comment: "Report review");

        Time("P-1131", "E05", new(2026, 10, 9), 0.5m, activity: "TEST");
        Time("P-1132", "E05", new(2026, 10, 9), 0.5m, activity: "ADMIN");

        db.TimeEntries.AddRange(entries);
        db.Expenses.AddRange(expenses);
        db.SaveChanges();

        BillHistory(db, company, projects.Values.ToList());
        AddHistoricCreditNotes(db, company);
        db.SaveChanges();
    }

    private static void AddExchangeRates(BillingContext db)
    {
        var october = new Dictionary<string, decimal>
        {
            ["GBP"] = 0.8642m,
            ["USD"] = 1.0835m,
            ["SEK"] = 11.47m,
            ["NOK"] = 11.683m,
            ["JPY"] = 162.37m,
        };
        var drift = new Random(77);
        foreach (var (currency, latest) in october)
        {
            var value = latest;
            for (var month = new DateOnly(2026, 10, 1); month >= HistoryStart; month = month.AddMonths(-1))
            {
                db.ExchangeRates.Add(new ExchangeRate { FromCurrency = "EUR", ToCurrency = currency, EffectiveDate = month, Rate = value });
                var step = (decimal)(drift.NextDouble() - 0.5) * 0.012m * value;
                value = Math.Round(value - step, currency == "JPY" ? 2 : 4);
            }
        }
        db.ExchangeRates.Local.Single(r => r.ToCurrency == "GBP" && r.EffectiveDate == new DateOnly(2026, 9, 1)).Rate = 0.8571m;
        // Alpine signed in October. Treasury loads its rates from November.
        db.ExchangeRates.Add(new ExchangeRate { FromCurrency = "EUR", ToCurrency = "CHF", EffectiveDate = new(2026, 11, 1), Rate = 0.9312m });
    }

    /// <summary>Monthly billing runs up to September 2026, finalised in date order.</summary>
    private static void BillHistory(BillingContext db, Company company, List<Project> projects)
    {
        var rates = db.ExchangeRates.ToList();
        var roles = db.Roles.ToDictionary(r => r.Code);
        var number = 1;

        for (var month = HistoryStart; month <= HistoryEnd; month = month.AddMonths(1))
        {
            var monthEnd = BillingHelper.EndOfMonth(month);
            foreach (var project in projects.OrderBy(p => p.Code))
            {
                var customer = project.Customer;
                var lines = new List<InvoiceLine>();
                var linked = new List<(InvoiceLine, TimeEntry?, ExpenseEntry?, Milestone?)>();

                if (project.BillingType == BillingType.TimeAndMaterials)
                {
                    foreach (var e in project.TimeEntries.Where(e => e.Status == EntryStatus.Approved && e.Billable
                                 && e.InvoiceLineId == null && e.Date >= month && e.Date <= monthEnd).OrderBy(e => e.Date))
                    {
                        var unit = customer.Rates.FirstOrDefault(r => r.RoleCode == e.Employee.RoleCode)?.Rate
                                   ?? project.Rates.FirstOrDefault(r => r.RoleCode == e.Employee.RoleCode)?.Rate
                                   ?? roles[e.Employee.RoleCode].DefaultRate;
                        var hours = RoundingHelper.RoundHours(e.Hours);
                        var line = new InvoiceLine
                        {
                            Kind = LineKind.Time,
                            Description = e.Date.ToString("yyyy-MM-dd") + " " + e.Employee.Name + " - " + e.ActivityCode,
                            Quantity = hours,
                            UnitPrice = unit,
                            SourceAmount = hours * unit,
                        };
                        lines.Add(line);
                        linked.Add((line, e, null, null));
                    }
                }
                foreach (var x in project.Expenses.Where(x => x.Status == EntryStatus.Approved && x.InvoiceLineId == null
                             && x.Date >= month && x.Date <= monthEnd).OrderBy(x => x.Date))
                {
                    var amount = BillingHelper.ExpenseWithMarkup(x.Amount, project.ExpenseMarkupPercent);
                    var line = new InvoiceLine { Kind = LineKind.Expense, Description = x.Date.ToString("yyyy-MM-dd") + " " + x.Description, Quantity = 1, UnitPrice = amount, SourceAmount = amount };
                    lines.Add(line);
                    linked.Add((line, null, x, null));
                }
                foreach (var m in project.Milestones.Where(m => m.IsComplete && m.BilledInvoiceId == null && m.CompletedOn <= monthEnd && m.CompletedOn >= month))
                {
                    var line = new InvoiceLine { Kind = LineKind.Milestone, Description = "Milestone: " + m.Name, Quantity = 1, UnitPrice = m.Amount, SourceAmount = m.Amount };
                    lines.Add(line);
                    linked.Add((line, null, null, m));
                }
                if (lines.Count == 0)
                {
                    continue;
                }

                var rate = customer.Currency == "EUR"
                    ? 1m
                    : rates.Where(r => r.ToCurrency == customer.Currency && r.EffectiveDate <= monthEnd)
                        .OrderByDescending(r => r.EffectiveDate).First().Rate;
                var reverse = BillingHelper.IsReverseCharge(customer, company);
                var taxCode = reverse ? TaxService.ReverseChargeCode : project.TaxCode;
                var taxRate = reverse ? 0m : project.TaxCode switch
                {
                    "S" => monthEnd < VatChange ? 24m : 25.5m,
                    "R1" => 14m,
                    "R2" => 10m,
                    _ => 0m,
                };

                var invoice = new Invoice
                {
                    Number = "INV-" + number++.ToString("000000"),
                    Kind = InvoiceKind.Invoice,
                    Status = InvoiceStatus.Final,
                    Customer = customer,
                    Project = project,
                    PeriodEnd = monthEnd,
                    InvoiceDate = monthEnd,
                    DueDate = BillingHelper.DueDate(monthEnd, customer),
                    Currency = customer.Currency,
                    ExchangeRate = rate,
                    PoNumber = customer.PoRequired ? "PO-" + (4000 + number) : null,
                    Notes = reverse ? TaxService.ReverseChargeNote : null,
                    CreatedBy = "Anna Virtanen",
                    CreatedAt = monthEnd.ToDateTime(new TimeOnly(9, 0)),
                    FinalisedBy = "Anna Virtanen",
                    FinalisedAt = monthEnd.ToDateTime(new TimeOnly(15, 30)),
                };
                var seq = 1;
                foreach (var line in lines)
                {
                    line.Sequence = seq++;
                    line.TaxCode = taxCode;
                    line.TaxRate = taxRate;
                }
                invoice.Lines = lines;
                ProposalService.Recalculate(invoice);
                db.Invoices.Add(invoice);
                db.SaveChanges();

                foreach (var (line, e, x, m) in linked)
                {
                    if (e != null) e.InvoiceLineId = line.Id;
                    if (x != null) x.InvoiceLineId = line.Id;
                    if (m != null) m.BilledInvoiceId = invoice.Id;
                }
            }
        }
        company.NextInvoiceNumber = number;
        db.SaveChanges();
    }

    private static void AddHistoricCreditNotes(BillingContext db, Company company)
    {
        var number = 1;
        var originals = db.Invoices
            .Where(i => i.Kind == InvoiceKind.Invoice && i.Status == InvoiceStatus.Final)
            .ToList()
            .OrderBy(i => i.InvoiceDate).ThenBy(i => i.Number)
            .ToList();

        // A handful of corrections over the years, plus the September Lumo invoice, whose second line was credited.
        var lumo = originals.Single(i => i.Project.Code == "P-1060" && i.InvoiceDate == new DateOnly(2026, 9, 30));
        var picks = originals.Where((invoice, index) => index % 23 == 7 && invoice != lumo).Take(12).ToList();
        picks.Add(lumo);

        foreach (var original in picks.OrderBy(i => i.InvoiceDate))
        {
            var lines = db.InvoiceLines.Where(l => l.InvoiceId == original.Id).OrderBy(l => l.Sequence).ToList();
            var credited = original == lumo ? lines[1] : lines[0];
            var date = original.InvoiceDate.AddDays(12);
            var note = new Invoice
            {
                Number = "CN-" + number++.ToString("000000"),
                Kind = InvoiceKind.CreditNote,
                Status = InvoiceStatus.Final,
                CustomerId = original.CustomerId,
                ProjectId = original.ProjectId,
                PeriodEnd = original.PeriodEnd,
                InvoiceDate = date,
                DueDate = date,
                Currency = original.Currency,
                ExchangeRate = original.ExchangeRate,
                OriginalInvoiceId = original.Id,
                Notes = "Credit for invoice " + original.Number + ". " + (original == lumo ? "Workshop day cancelled by the customer." : "Hours booked to the wrong project."),
                CreatedBy = "Anna Virtanen",
                CreatedAt = date.ToDateTime(new TimeOnly(10, 0)),
                FinalisedBy = "Anna Virtanen",
                FinalisedAt = date.ToDateTime(new TimeOnly(10, 5)),
            };
            note.Lines.Add(new InvoiceLine
            {
                Sequence = 1,
                Kind = credited.Kind,
                Description = "Credit: " + credited.Description,
                Quantity = 1,
                UnitPrice = -credited.Amount,
                SourceAmount = -credited.SourceAmount,
                Amount = -credited.Amount,
                TaxCode = credited.TaxCode,
                TaxRate = credited.TaxRate,
                TaxAmount = -credited.TaxAmount,
                SourceLineId = credited.Id,
            });
            note.Subtotal = -credited.Amount;
            note.TaxTotal = -credited.TaxAmount;
            note.Total = note.Subtotal + note.TaxTotal;
            note.BaseSubtotal = -credited.SourceAmount;
            db.Invoices.Add(note);
        }
        company.NextCreditNoteNumber = number;
        db.SaveChanges();
    }
}
