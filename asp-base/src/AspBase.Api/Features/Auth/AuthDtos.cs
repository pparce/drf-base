using AspBase.Api.Features.Users;
using FluentValidation;

namespace AspBase.Api.Features.Auth;

public record LoginRequest(string Email, string Password);

public record RegisterRequest(
    string Email,
    string FirstName,
    string LastName,
    string Password,
    bool ReceiveNews = false);

public record SendRestoreCodeRequest(string Email);

public record RestorePasswordRequest(string Email, string Code, string NewPassword);

public record GoogleLoginRequest(string IdToken);

public record RefreshRequest(string RefreshToken);

/// <summary>Token bundle returned on login/register/google, matching the DRF <c>_token_response</c>.</summary>
public record TokenResponse(string Token, string TokenRefresh, UserDto User, bool? Created = null);

public class LoginRequestValidator : AbstractValidator<LoginRequest>
{
    public LoginRequestValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Password).NotEmpty();
    }
}

public class RegisterRequestValidator : AbstractValidator<RegisterRequest>
{
    public RegisterRequestValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.FirstName).NotEmpty().MaximumLength(255);
        RuleFor(x => x.LastName).NotEmpty().MaximumLength(255);
        RuleFor(x => x.Password).NotEmpty().MinimumLength(8);
    }
}

public class RestorePasswordRequestValidator : AbstractValidator<RestorePasswordRequest>
{
    public RestorePasswordRequestValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Code).NotEmpty().MaximumLength(8);
        RuleFor(x => x.NewPassword).NotEmpty().MinimumLength(8);
    }
}
