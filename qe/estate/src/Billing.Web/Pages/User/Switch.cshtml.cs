using Kestrel.Billing.Infrastructure;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Kestrel.Billing.Pages.User;

[IgnoreAntiforgeryToken]
public class SwitchModel : PageModel
{
    public IActionResult OnPost(string user, string? returnUrl)
    {
        if (CurrentUser.Users.ContainsKey(user))
        {
            Response.Cookies.Append(CurrentUser.CookieName, user, new CookieOptions { HttpOnly = true, SameSite = SameSiteMode.Lax });
        }
        return LocalRedirect(string.IsNullOrEmpty(returnUrl) || !Url.IsLocalUrl(returnUrl) ? "/" : returnUrl);
    }

    public IActionResult OnGet() => LocalRedirect("/");
}
