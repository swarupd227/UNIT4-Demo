namespace Kestrel.Billing.Data;

public class Company
{
    public int Id { get; set; }
    public string Code { get; set; }
    public string Name { get; set; }
    public string BaseCurrency { get; set; } = "EUR";
    public string CountryCode { get; set; } = "FI";
    public int NextInvoiceNumber { get; set; } = 1;
    public int NextCreditNoteNumber { get; set; } = 1;
}

public class Customer
{
    public int Id { get; set; }
    public string Code { get; set; }
    public string Name { get; set; }
    public string Currency { get; set; } = "EUR";
    public string CountryCode { get; set; } = "FI";
    public string? VatNumber { get; set; }
    public bool IsBusiness { get; set; } = true;
    public int PaymentTermsDays { get; set; } = 30;
    public decimal DiscountPercent { get; set; }
    public bool PoRequired { get; set; }
    public bool IsOnHold { get; set; }
    public string? HoldReason { get; set; }
    public List<Project> Projects { get; set; } = new();
    public List<CustomerRate> Rates { get; set; } = new();
}

public enum BillingType
{
    TimeAndMaterials = 0,
    FixedPrice = 1,
}

public enum ProjectStatus
{
    Active = 0,
    Closing = 1,
    Closed = 2,
}

public class Project
{
    public int Id { get; set; }
    public string Code { get; set; }
    public string Name { get; set; }
    public int CustomerId { get; set; }
    public Customer Customer { get; set; }
    public BillingType BillingType { get; set; }
    public ProjectStatus Status { get; set; }
    public string TaxCode { get; set; } = "S";
    public decimal ExpenseMarkupPercent { get; set; }
    public decimal? NotToExceed { get; set; }
    public bool IsOnHold { get; set; }
    public string? HoldReason { get; set; }
    public string? ProjectManager { get; set; }
    public List<ProjectRate> Rates { get; set; } = new();
    public List<Milestone> Milestones { get; set; } = new();
    public List<TimeEntry> TimeEntries { get; set; } = new();
    public List<ExpenseEntry> Expenses { get; set; } = new();
}

public class Role
{
    public string Code { get; set; }
    public string Name { get; set; }
    public decimal DefaultRate { get; set; }
}

public class ProjectRate
{
    public int Id { get; set; }
    public int ProjectId { get; set; }
    public string RoleCode { get; set; }
    public decimal Rate { get; set; }
}

public class CustomerRate
{
    public int Id { get; set; }
    public int CustomerId { get; set; }
    public string RoleCode { get; set; }
    public decimal Rate { get; set; }
}

public class Employee
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string RoleCode { get; set; }
}

public enum EntryStatus
{
    Draft = 0,
    Submitted = 1,
    Approved = 2,
    Rejected = 3,
}

public class TimeEntry
{
    public int Id { get; set; }
    public int ProjectId { get; set; }
    public Project Project { get; set; }
    public int EmployeeId { get; set; }
    public Employee Employee { get; set; }
    public DateOnly Date { get; set; }
    public decimal Hours { get; set; }
    public string ActivityCode { get; set; } = "CONS";
    public string? Comment { get; set; }
    public bool Billable { get; set; } = true;
    public EntryStatus Status { get; set; }
    public int? InvoiceLineId { get; set; }
}

public class ExpenseEntry
{
    public int Id { get; set; }
    public int ProjectId { get; set; }
    public Project Project { get; set; }
    public DateOnly Date { get; set; }
    public string Description { get; set; }
    public decimal Amount { get; set; }
    public bool Billable { get; set; } = true;
    public EntryStatus Status { get; set; }
    public int? InvoiceLineId { get; set; }
}

public class Milestone
{
    public int Id { get; set; }
    public int ProjectId { get; set; }
    public string Name { get; set; }
    public decimal Amount { get; set; }
    public DateOnly PlannedDate { get; set; }
    public bool IsComplete { get; set; }
    public DateOnly? CompletedOn { get; set; }
    public int? BilledInvoiceId { get; set; }
}

public class TaxCode
{
    public string Code { get; set; }
    public string Description { get; set; }
    public decimal Rate { get; set; }
    public bool IsExempt { get; set; }
}

public class ExchangeRate
{
    public int Id { get; set; }
    public string FromCurrency { get; set; }
    public string ToCurrency { get; set; }
    public DateOnly EffectiveDate { get; set; }
    public decimal Rate { get; set; }
}

public enum InvoiceStatus
{
    Proposal = 0,
    PendingApproval = 1,
    Deferred = 2,
    Final = 3,
    Cancelled = 4,
}

public enum InvoiceKind
{
    Invoice = 0,
    CreditNote = 1,
}

public class Invoice
{
    public int Id { get; set; }
    public string? Number { get; set; }
    public InvoiceKind Kind { get; set; }
    public InvoiceStatus Status { get; set; }
    public int CustomerId { get; set; }
    public Customer Customer { get; set; }
    public int ProjectId { get; set; }
    public Project Project { get; set; }
    public DateOnly PeriodEnd { get; set; }
    public DateOnly InvoiceDate { get; set; }
    public DateOnly? DueDate { get; set; }
    public string Currency { get; set; } = "EUR";
    public decimal? ExchangeRate { get; set; }
    public string? PoNumber { get; set; }
    public decimal Subtotal { get; set; }
    public decimal TaxTotal { get; set; }
    public decimal Total { get; set; }
    public decimal BaseSubtotal { get; set; }
    public string? Notes { get; set; }
    public string? StatusReason { get; set; }
    public int? OriginalInvoiceId { get; set; }
    public string CreatedBy { get; set; }
    public DateTime CreatedAt { get; set; }
    public string? FinalisedBy { get; set; }
    public DateTime? FinalisedAt { get; set; }
    public string? ApprovedBy { get; set; }
    public DateTime? ApprovedAt { get; set; }
    public List<InvoiceLine> Lines { get; set; } = new();
}

public enum LineKind
{
    Time = 0,
    Expense = 1,
    Milestone = 2,
}

public class InvoiceLine
{
    public int Id { get; set; }
    public int InvoiceId { get; set; }
    public Invoice Invoice { get; set; }
    public int Sequence { get; set; }
    public LineKind Kind { get; set; }
    public string Description { get; set; }
    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal DiscountPercent { get; set; }
    public decimal SourceAmount { get; set; }
    public decimal Adjustment { get; set; }
    public string? AdjustmentReason { get; set; }
    public decimal Amount { get; set; }
    public string TaxCode { get; set; } = "S";
    public decimal TaxRate { get; set; }
    public decimal TaxAmount { get; set; }
    public int? SourceLineId { get; set; }
}

public class AuditEntry
{
    public int Id { get; set; }
    public DateTime At { get; set; }
    public string User { get; set; }
    public string Action { get; set; }
    public string Detail { get; set; }
}
