using System.ComponentModel.DataAnnotations;

namespace AspBase.Api.Infrastructure.Options;

/// <summary>JWT signing/lifetime settings. Bound from the <c>Jwt</c> config section.</summary>
public class JwtOptions
{
    public const string SectionName = "Jwt";

    [Required] public string SigningKey { get; set; } = string.Empty;
    public string Issuer { get; set; } = "asp-base";
    public string Audience { get; set; } = "asp-base";
    public int AccessTokenLifetimeMinutes { get; set; } = 60 * 24;      // 1 day, matches SIMPLE_JWT
    public int RefreshTokenLifetimeMinutes { get; set; } = 60 * 24 * 2; // 2 days
}

/// <summary>Google Sign-In settings. Bound from the <c>Google</c> config section.</summary>
public class GoogleOptions
{
    public const string SectionName = "Google";
    public string ClientId { get; set; } = string.Empty;
}

/// <summary>SMTP settings. Bound from the <c>Email</c> config section.</summary>
public class EmailOptions
{
    public const string SectionName = "Email";
    public string Host { get; set; } = "smtp.mailtrap.io";
    public int Port { get; set; } = 2525;
    public string User { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public bool UseTls { get; set; } = true;
    public string FromEmail { get; set; } = "noreply@example.com";
}

/// <summary>File-storage settings. Bound from the <c>Media</c> config section.</summary>
public class MediaOptions
{
    public const string SectionName = "Media";
    public string Root { get; set; } = "media";
    public string RequestPath { get; set; } = "/media";
}
