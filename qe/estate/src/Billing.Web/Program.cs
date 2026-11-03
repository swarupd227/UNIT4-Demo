using Kestrel.Billing.Data;
using Kestrel.Billing.Infrastructure;
using Kestrel.Billing.Services;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorPages();
builder.Services.AddHttpContextAccessor();

var databasePath = builder.Configuration["Billing:Database"] ?? "billing.db";
builder.Services.AddDbContext<BillingContext>(options =>
    options.UseSqlite($"Data Source={databasePath};Default Timeout=30"));

builder.Services.AddSingleton<SystemClock>();
builder.Services.AddSingleton<LedgerSync>();
builder.Services.AddScoped<CurrentUser>();
builder.Services.AddScoped<ExchangeRateService>();
builder.Services.AddScoped<TaxService>();
builder.Services.AddScoped<ProposalService>();
builder.Services.AddScoped<AdjustmentService>();
builder.Services.AddScoped<InvoiceService>();
builder.Services.AddScoped<CreditNoteService>();
builder.Services.AddScoped<NumberingService>();
builder.Services.AddScoped<ApprovalService>();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<BillingContext>();
    if (db.Database.EnsureCreated())
    {
        SeedData.Load(db);
    }
}

if (builder.Configuration.GetValue<bool>("seed-only"))
{
    return;
}

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
}

app.UseStaticFiles();
app.UseRouting();
app.MapRazorPages();
app.MapGet("/health", () => Results.Text("ok"));

app.Run();
