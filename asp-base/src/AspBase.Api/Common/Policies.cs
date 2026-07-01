namespace AspBase.Api.Common;

/// <summary>Named authorization policies used across endpoints.</summary>
public static class Policies
{
    /// <summary>Requires the caller to be staff or superuser (DRF <c>IsAdminUser</c>).</summary>
    public const string StaffOnly = "StaffOnly";
}
