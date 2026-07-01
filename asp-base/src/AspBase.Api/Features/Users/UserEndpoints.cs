using AspBase.Api.Common;
using AspBase.Api.Domain.Entities;
using AspBase.Api.Infrastructure.Auth;
using AspBase.Api.Infrastructure.Data;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace AspBase.Api.Features.Users;

/// <summary>
/// User management endpoints, the Minimal-API equivalent of the DRF <c>UserViewSet</c>.
/// List/create/delete require staff; a user may read or update only their own record.
/// </summary>
public static class UserEndpoints
{
    public static IEndpointRouteBuilder MapUserEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/users")
            .WithTags("Users")
            .RequireAuthorization()
            .RequireRateLimiting("user");

        group.MapGet("/", List).RequireAuthorization(Policies.StaffOnly);
        group.MapGet("/{id:long}", Get);
        group.MapPost("/", Create).RequireAuthorization(Policies.StaffOnly).WithValidation<CreateUserRequest>();
        group.MapPut("/{id:long}", Update);
        group.MapDelete("/{id:long}", Delete).RequireAuthorization(Policies.StaffOnly);
        group.MapPost("/admin_create", AdminCreate).RequireAuthorization(Policies.StaffOnly).WithValidation<CreateUserRequest>();
        group.MapPost("/change_password", ChangePassword).WithValidation<ChangePasswordRequest>();
        group.MapGet("/me", Me);

        return app;
    }

    private static async Task<Ok<PagedResult<UserDto>>> List(
        [AsParameters] PageQuery paging, HttpRequest request, AppDbContext db, CancellationToken ct)
    {
        var page = await db.Users.AsNoTracking().OrderBy(u => u.Email)
            .Select(u => new UserDto(
                u.Id, u.Email, u.FirstName, u.LastName, u.IsActive,
                u.IsStaff, u.IsCustomer, u.IsValidate, u.Avatar, u.ReceiveNews))
            .ToPagedResultAsync(paging, request, ct);
        return TypedResults.Ok(page);
    }

    private static async Task<Results<Ok<UserDto>, NotFound, ForbidHttpResult>> Get(
        long id, ClaimsPrincipalAccessor principal, AppDbContext db, CancellationToken ct)
    {
        if (!principal.IsStaff && principal.UserId != id)
            return TypedResults.Forbid();

        var user = await db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Id == id, ct);
        return user is null ? TypedResults.NotFound() : TypedResults.Ok(UserDto.From(user));
    }

    private static async Task<Ok<UserDto>> Me(ClaimsPrincipalAccessor principal, AppDbContext db, CancellationToken ct)
    {
        var user = await db.Users.AsNoTracking().FirstAsync(u => u.Id == principal.UserId, ct);
        return TypedResults.Ok(UserDto.From(user));
    }

    private static async Task<Results<Created<UserDto>, BadRequest<ErrorResponse>>> Create(
        CreateUserRequest req, AppDbContext db, PasswordHashingService hasher, CancellationToken ct)
    {
        if (await db.Users.AnyAsync(u => u.Email == req.Email, ct))
            return TypedResults.BadRequest(new ErrorResponse("This email is already in use"));

        var user = new User
        {
            Email = req.Email,
            FirstName = req.FirstName,
            LastName = req.LastName,
            IsCustomer = req.IsCustomer,
            ReceiveNews = req.ReceiveNews,
        };
        user.PasswordHash = hasher.Hash(user, req.Password);
        db.Users.Add(user);
        await db.SaveChangesAsync(ct);

        return TypedResults.Created($"/api/users/{user.Id}", UserDto.From(user));
    }

    private static async Task<Results<Ok<UserDto>, NotFound<ErrorResponse>, ForbidHttpResult>> Update(
        long id, UpdateUserRequest req, ClaimsPrincipalAccessor principal, AppDbContext db, CancellationToken ct)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Id == id, ct);
        if (user is null) return TypedResults.NotFound(new ErrorResponse("User not found"));

        if (!principal.IsStaff && principal.UserId != user.Id)
            return TypedResults.Forbid();

        if (req.Email is not null) user.Email = req.Email;
        if (req.FirstName is not null) user.FirstName = req.FirstName;
        if (req.LastName is not null) user.LastName = req.LastName;
        await db.SaveChangesAsync(ct);

        return TypedResults.Ok(UserDto.From(user));
    }

    private static async Task<Results<NoContent, NotFound>> Delete(long id, AppDbContext db, CancellationToken ct)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Id == id, ct);
        if (user is null) return TypedResults.NotFound();
        db.Users.Remove(user);
        await db.SaveChangesAsync(ct);
        return TypedResults.NoContent();
    }

    /// <summary>Creates a staff user, or promotes an existing account to staff (DRF <c>admin_create</c>).</summary>
    private static async Task<Results<Ok<UserDto>, Created<UserDto>, BadRequest<ErrorResponse>>> AdminCreate(
        CreateUserRequest req, AppDbContext db, PasswordHashingService hasher, CancellationToken ct)
    {
        var existing = await db.Users.FirstOrDefaultAsync(u => u.Email == req.Email, ct);
        if (existing is not null)
        {
            if (existing.IsStaff)
                return TypedResults.BadRequest(new ErrorResponse("This email is already in use by a staff member"));
            existing.IsStaff = true;
            await db.SaveChangesAsync(ct);
            return TypedResults.Ok(UserDto.From(existing));
        }

        var user = new User
        {
            Email = req.Email,
            FirstName = req.FirstName,
            LastName = req.LastName,
            ReceiveNews = req.ReceiveNews,
            IsStaff = true,
        };
        user.PasswordHash = hasher.Hash(user, req.Password);
        db.Users.Add(user);
        await db.SaveChangesAsync(ct);

        return TypedResults.Created($"/api/users/{user.Id}", UserDto.From(user));
    }

    private static async Task<Results<Ok<MessageResponse>, UnauthorizedHttpResult, BadRequest<ErrorResponse>>> ChangePassword(
        ChangePasswordRequest req, ClaimsPrincipalAccessor principal, AppDbContext db, PasswordHashingService hasher, CancellationToken ct)
    {
        var user = await db.Users.FirstAsync(u => u.Id == principal.UserId, ct);

        if (!hasher.Verify(user, req.CurrentPassword))
            return TypedResults.Unauthorized();

        user.PasswordHash = hasher.Hash(user, req.NewPassword);
        await db.SaveChangesAsync(ct);
        return TypedResults.Ok(new MessageResponse("Password changed successfully"));
    }
}
