using Microsoft.EntityFrameworkCore;

namespace Kestrel.Billing.Data;

public class BillingContext : DbContext
{
    public BillingContext(DbContextOptions<BillingContext> options) : base(options)
    {
    }

    public DbSet<Company> Companies => Set<Company>();
    public DbSet<Customer> Customers => Set<Customer>();
    public DbSet<Project> Projects => Set<Project>();
    public DbSet<Role> Roles => Set<Role>();
    public DbSet<ProjectRate> ProjectRates => Set<ProjectRate>();
    public DbSet<CustomerRate> CustomerRates => Set<CustomerRate>();
    public DbSet<Employee> Employees => Set<Employee>();
    public DbSet<TimeEntry> TimeEntries => Set<TimeEntry>();
    public DbSet<ExpenseEntry> Expenses => Set<ExpenseEntry>();
    public DbSet<Milestone> Milestones => Set<Milestone>();
    public DbSet<TaxCode> TaxCodes => Set<TaxCode>();
    public DbSet<ExchangeRate> ExchangeRates => Set<ExchangeRate>();
    public DbSet<Invoice> Invoices => Set<Invoice>();
    public DbSet<InvoiceLine> InvoiceLines => Set<InvoiceLine>();
    public DbSet<AuditEntry> Audit => Set<AuditEntry>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Role>().HasKey(r => r.Code);
        modelBuilder.Entity<TaxCode>().HasKey(t => t.Code);
        modelBuilder.Entity<Customer>().HasIndex(c => c.Code).IsUnique();
        modelBuilder.Entity<Project>().HasIndex(p => p.Code).IsUnique();
        modelBuilder.Entity<Invoice>().HasIndex(i => i.Number).IsUnique();
        modelBuilder.Entity<ExchangeRate>().HasIndex(r => new { r.FromCurrency, r.ToCurrency, r.EffectiveDate }).IsUnique();

        // SQLite has no decimal type. Amounts are stored as text so that no precision is lost.
        foreach (var property in modelBuilder.Model.GetEntityTypes().SelectMany(t => t.GetProperties()))
        {
            if (property.ClrType == typeof(decimal) || property.ClrType == typeof(decimal?))
            {
                property.SetColumnType("TEXT");
            }
        }
    }
}
