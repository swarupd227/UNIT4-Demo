using Kestrel.Billing.Data;

namespace Kestrel.Billing.Infrastructure;

public class BillingException : Exception
{
    public BillingException(string message) : base(message)
    {
    }
}

/// <summary>
/// The business date. Finance runs billing against a fixed system date, set in configuration,
/// so that period ends do not move while a billing run is in progress.
/// </summary>
public class SystemClock
{
    private readonly DateOnly? _today;

    public SystemClock(IConfiguration configuration)
    {
        var configured = configuration["Billing:BusinessDate"];
        if (!string.IsNullOrWhiteSpace(configured))
        {
            _today = DateOnly.Parse(configured);
        }
    }

    public DateOnly Today => _today ?? DateOnly.FromDateTime(DateTime.Today);

    public DateTime Now => DateTime.UtcNow;
}

/// <summary>
/// Posts finalised documents to the general ledger. The ledger interface is slow and its response
/// time varies with load, so posting runs in the background and the user waits on the posting page.
/// </summary>
public class LedgerSync
{
    private readonly int _minMs;
    private readonly int _maxMs;
    private readonly Random _random = new();
    private readonly System.Collections.Concurrent.ConcurrentDictionary<int, DateTime> _postedAt = new();

    public LedgerSync(IConfiguration configuration)
    {
        var range = (configuration["Billing:LedgerDelayMs"] ?? "400-2600").Split('-');
        _minMs = int.Parse(range[0]);
        _maxMs = int.Parse(range[^1]);
    }

    public void Post(int invoiceId)
    {
        int delay;
        lock (_random)
        {
            delay = _random.Next(_minMs, _maxMs + 1);
        }
        _postedAt[invoiceId] = DateTime.UtcNow.AddMilliseconds(delay);
    }

    /// <summary>Documents finalised before the last restart were posted long ago.</summary>
    public bool IsPosted(int invoiceId)
    {
        return !_postedAt.TryGetValue(invoiceId, out var at) || DateTime.UtcNow >= at;
    }
}

public class CurrentUser
{
    public const string CookieName = "billing_user";

    public static readonly Dictionary<string, (string Name, string Role)> Users = new()
    {
        ["anna"] = ("Anna Virtanen", "Billing clerk"),
        ["mikko"] = ("Mikko Laine", "Billing manager"),
        ["sofia"] = ("Sofia Berg", "Project manager"),
    };

    private readonly IHttpContextAccessor _accessor;

    public CurrentUser(IHttpContextAccessor accessor)
    {
        _accessor = accessor;
    }

    public string Key
    {
        get
        {
            var value = _accessor.HttpContext?.Request.Cookies[CookieName];
            return value != null && Users.ContainsKey(value) ? value : "anna";
        }
    }

    public string Name => Users[Key].Name;

    public string Role => Users[Key].Role;

    public bool IsBillingManager => Role == "Billing manager";
}
