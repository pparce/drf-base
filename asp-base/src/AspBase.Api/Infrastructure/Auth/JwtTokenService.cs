using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using AspBase.Api.Domain.Entities;
using AspBase.Api.Infrastructure.Options;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

namespace AspBase.Api.Infrastructure.Auth;

public record TokenPair(string Token, string RefreshToken);

/// <summary>
/// Issues and validates JWT access/refresh tokens, replacing djangorestframework-simplejwt.
/// Access and refresh tokens are distinguished by the <c>token_type</c> claim.
/// </summary>
public class JwtTokenService(IOptions<JwtOptions> options)
{
    private readonly JwtOptions _opt = options.Value;

    public TokenPair CreateTokenPair(User user)
    {
        var access = CreateToken(user, "access", TimeSpan.FromMinutes(_opt.AccessTokenLifetimeMinutes));
        var refresh = CreateToken(user, "refresh", TimeSpan.FromMinutes(_opt.RefreshTokenLifetimeMinutes));
        return new TokenPair(access, refresh);
    }

    private string CreateToken(User user, string tokenType, TimeSpan lifetime)
    {
        var claims = new List<Claim>
        {
            new("user_id", user.Id.ToString()),
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email, user.Email),
            new("token_type", tokenType),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };
        if (user.IsStaff) claims.Add(new Claim(ClaimTypes.Role, Roles.Staff));
        if (user.IsSuperuser) claims.Add(new Claim(ClaimTypes.Role, Roles.Superuser));

        var creds = new SigningCredentials(SigningKey, SecurityAlgorithms.HmacSha256);
        var token = new JwtSecurityToken(
            issuer: _opt.Issuer,
            audience: _opt.Audience,
            claims: claims,
            expires: DateTime.UtcNow.Add(lifetime),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    /// <summary>Validates a refresh token and returns its <c>user_id</c> claim, or null when invalid.</summary>
    public long? ValidateRefreshToken(string refreshToken)
    {
        var handler = new JwtSecurityTokenHandler();
        try
        {
            var principal = handler.ValidateToken(refreshToken, TokenValidationParameters, out _);
            if (principal.FindFirstValue("token_type") != "refresh") return null;
            var id = principal.FindFirstValue("user_id");
            return long.TryParse(id, out var userId) ? userId : null;
        }
        catch
        {
            return null;
        }
    }

    public SymmetricSecurityKey SigningKey => new(Encoding.UTF8.GetBytes(_opt.SigningKey));

    public TokenValidationParameters TokenValidationParameters => new()
    {
        ValidateIssuer = true,
        ValidIssuer = _opt.Issuer,
        ValidateAudience = true,
        ValidAudience = _opt.Audience,
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = SigningKey,
        ValidateLifetime = true,
        ClockSkew = TimeSpan.FromSeconds(30),
    };
}

public static class Roles
{
    public const string Staff = "Staff";
    public const string Superuser = "Superuser";
}
