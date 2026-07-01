using AspBase.Api.Infrastructure.Options;
using Google.Apis.Auth;
using Microsoft.Extensions.Options;

namespace AspBase.Api.Infrastructure.Auth;

public record GoogleUserInfo(string Email, bool EmailVerified, string? GivenName, string? FamilyName);

/// <summary>
/// Validates a Google ID token (client-side Sign-In flow) against the configured client id,
/// replacing the <c>google.oauth2.id_token.verify_oauth2_token</c> call in the DRF project.
/// </summary>
public class GoogleTokenValidator(IOptions<GoogleOptions> options)
{
    private readonly GoogleOptions _opt = options.Value;

    public async Task<GoogleUserInfo?> ValidateAsync(string idToken)
    {
        try
        {
            var settings = new GoogleJsonWebSignature.ValidationSettings
            {
                Audience = [_opt.ClientId],
            };
            var payload = await GoogleJsonWebSignature.ValidateAsync(idToken, settings);
            return new GoogleUserInfo(payload.Email, payload.EmailVerified, payload.GivenName, payload.FamilyName);
        }
        catch (InvalidJwtException)
        {
            return null;
        }
    }
}
