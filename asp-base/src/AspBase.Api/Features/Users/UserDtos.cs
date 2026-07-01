using AspBase.Api.Domain.Entities;
using FluentValidation;

namespace AspBase.Api.Features.Users;

public record UserDto(
    long Id,
    string Email,
    string? FirstName,
    string? LastName,
    bool IsActive,
    bool IsStaff,
    bool IsCustomer,
    bool IsValidate,
    string? Avatar,
    bool ReceiveNews)
{
    public static UserDto From(User u) => new(
        u.Id, u.Email, u.FirstName, u.LastName, u.IsActive,
        u.IsStaff, u.IsCustomer, u.IsValidate, u.Avatar, u.ReceiveNews);
}

public record CreateUserRequest(
    string Email,
    string FirstName,
    string LastName,
    string Password,
    bool IsCustomer = false,
    bool ReceiveNews = false);

public record UpdateUserRequest(string? Email, string? FirstName, string? LastName);

public record ChangePasswordRequest(string CurrentPassword, string NewPassword);

public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.FirstName).NotEmpty().MaximumLength(255);
        RuleFor(x => x.LastName).NotEmpty().MaximumLength(255);
        RuleFor(x => x.Password).NotEmpty().MinimumLength(8);
    }
}

public class ChangePasswordRequestValidator : AbstractValidator<ChangePasswordRequest>
{
    public ChangePasswordRequestValidator()
    {
        RuleFor(x => x.CurrentPassword).NotEmpty();
        RuleFor(x => x.NewPassword).NotEmpty().MinimumLength(8);
    }
}
