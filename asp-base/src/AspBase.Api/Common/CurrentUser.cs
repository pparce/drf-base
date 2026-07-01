using System.Security.Claims;
using AspBase.Api.Infrastructure.Auth;

namespace AspBase.Api.Common;

/// <summary>Convenience accessors for the authenticated principal's claims.</summary>
public static class CurrentUser
{
    public static long? GetUserId(this ClaimsPrincipal principal)
    {
        var id = principal.FindFirstValue("user_id");
        return long.TryParse(id, out var userId) ? userId : null;
    }

    public static bool IsStaff(this ClaimsPrincipal principal) =>
        principal.IsInRole(Roles.Staff) || principal.IsInRole(Roles.Superuser);
}
