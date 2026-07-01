using AspBase.Api.Domain.Entities;
using Microsoft.AspNetCore.Identity;

namespace AspBase.Api.Infrastructure.Auth;

/// <summary>
/// Thin wrapper over ASP.NET Core Identity's <see cref="PasswordHasher{TUser}"/> (PBKDF2),
/// replacing Django's <c>set_password</c>/<c>check_password</c>.
/// </summary>
public class PasswordHashingService
{
    private readonly PasswordHasher<User> _hasher = new();

    public string Hash(User user, string password) => _hasher.HashPassword(user, password);

    public bool Verify(User user, string password)
    {
        if (string.IsNullOrEmpty(user.PasswordHash)) return false;
        var result = _hasher.VerifyHashedPassword(user, user.PasswordHash, password);
        return result is PasswordVerificationResult.Success or PasswordVerificationResult.SuccessRehashNeeded;
    }
}
