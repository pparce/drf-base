namespace AspBase.Api.Domain.Entities;

/// <summary>
/// Application user, email is the unique login identifier (equivalent to the DRF
/// custom <c>User</c> model where <c>USERNAME_FIELD = "email"</c>).
/// </summary>
public class User : BaseEntity
{
    public string Email { get; set; } = string.Empty;

    /// <summary>PBKDF2 hash produced by <see cref="Microsoft.AspNetCore.Identity.PasswordHasher{TUser}"/>. Null for OAuth-only accounts.</summary>
    public string? PasswordHash { get; set; }

    public string? FirstName { get; set; }
    public string? LastName { get; set; }

    public bool IsActive { get; set; } = true;

    /// <summary>Staff/admin flag. Grants access to admin-only endpoints.</summary>
    public bool IsStaff { get; set; }
    public bool IsSuperuser { get; set; }
    public bool IsCustomer { get; set; }
    public bool IsValidate { get; set; }

    /// <summary>Short-lived numeric code for the password-reset flow.</summary>
    public string? RestoreCode { get; set; }

    /// <summary>Relative path of the uploaded avatar (served from the media folder).</summary>
    public string? Avatar { get; set; }

    public bool ReceiveNews { get; set; }

    public DateTime? LastLogin { get; set; }

    public string FullName => string.Join(" ", new[] { FirstName, LastName }.Where(s => !string.IsNullOrWhiteSpace(s)));
}
