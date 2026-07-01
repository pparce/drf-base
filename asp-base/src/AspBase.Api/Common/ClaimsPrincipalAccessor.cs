namespace AspBase.Api.Common;

/// <summary>
/// Scoped helper injected into endpoints to read the current user's id and staff status,
/// the .NET equivalent of DRF's <c>request.user</c>.
/// </summary>
public class ClaimsPrincipalAccessor(IHttpContextAccessor accessor)
{
    private System.Security.Claims.ClaimsPrincipal? Principal => accessor.HttpContext?.User;

    public long UserId => Principal?.GetUserId() ?? 0;
    public bool IsStaff => Principal?.IsStaff() ?? false;
}
