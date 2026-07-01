using System.Security.Cryptography;
using AspBase.Api.Common;
using AspBase.Api.Domain.Entities;
using AspBase.Api.Features.Users;
using AspBase.Api.Infrastructure.Auth;
using AspBase.Api.Infrastructure.Data;
using AspBase.Api.Infrastructure.Email;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

namespace AspBase.Api.Features.Auth;

/// <summary>
/// Authentication endpoints (login, register, password reset, Google Sign-In, token refresh),
/// the Minimal-API equivalent of the DRF <c>AuthViewSet</c>. All are anonymous and rate-limited
/// with the stricter <c>auth</c> policy.
/// </summary>
public static class AuthEndpoints
{
    private const string ResetGenericMessage = "If this email exists, a reset code has been sent";

    public static IEndpointRouteBuilder MapAuthEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/auth")
            .WithTags("Auth")
            .AllowAnonymous()
            .RequireRateLimiting("auth");

        group.MapPost("/login", Login).WithValidation<LoginRequest>();
        group.MapPost("/register", Register).WithValidation<RegisterRequest>();
        group.MapPost("/sending_restore_code", SendRestoreCode);
        group.MapPost("/restore_password", RestorePassword).WithValidation<RestorePasswordRequest>();
        group.MapPost("/google", GoogleLogin);
        group.MapPost("/token/refresh", RefreshToken);

        return app;
    }

    private static async Task<Results<Ok<TokenResponse>, UnauthorizedHttpResult>> Login(
        LoginRequest req, AppDbContext db, PasswordHashingService hasher, JwtTokenService jwt, CancellationToken ct)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == req.Email, ct);
        if (user is null || !hasher.Verify(user, req.Password) || !user.IsActive)
            return TypedResults.Unauthorized();

        user.RestoreCode = null;
        user.LastLogin = DateTime.UtcNow;
        await db.SaveChangesAsync(ct);

        return TypedResults.Ok(BuildTokenResponse(user, jwt));
    }

    private static async Task<Results<Created<TokenResponse>, BadRequest<ErrorResponse>>> Register(
        RegisterRequest req, AppDbContext db, PasswordHashingService hasher, JwtTokenService jwt,
        EmailQueue emailQueue, CancellationToken ct)
    {
        if (await db.Users.AnyAsync(u => u.Email == req.Email, ct))
            return TypedResults.BadRequest(new ErrorResponse("This email is already in use"));

        var user = new User
        {
            Email = req.Email,
            FirstName = req.FirstName,
            LastName = req.LastName,
            ReceiveNews = req.ReceiveNews,
        };
        user.PasswordHash = hasher.Hash(user, req.Password);
        db.Users.Add(user);
        await db.SaveChangesAsync(ct);

        await emailQueue.QueueWelcomeEmail(user.Email, user.FirstName ?? "User");

        return TypedResults.Created($"/api/users/{user.Id}", BuildTokenResponse(user, jwt));
    }

    private static async Task<Ok<MessageResponse>> SendRestoreCode(
        SendRestoreCodeRequest req, AppDbContext db, EmailQueue emailQueue, CancellationToken ct)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == req.Email, ct);
        // Always return the same generic message to avoid leaking which emails exist.
        if (user is null) return TypedResults.Ok(new MessageResponse(ResetGenericMessage));

        user.RestoreCode = GenerateCode();
        await db.SaveChangesAsync(ct);

        await emailQueue.QueuePasswordResetEmail(user.Email, user.FirstName ?? "User", user.RestoreCode);
        return TypedResults.Ok(new MessageResponse(ResetGenericMessage));
    }

    private static async Task<Results<Ok<MessageResponse>, BadRequest<ErrorResponse>>> RestorePassword(
        RestorePasswordRequest req, AppDbContext db, PasswordHashingService hasher, CancellationToken ct)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == req.Email, ct);
        if (user is null || string.IsNullOrEmpty(user.RestoreCode) || user.RestoreCode != req.Code)
            return TypedResults.BadRequest(new ErrorResponse("Invalid email or code"));

        user.PasswordHash = hasher.Hash(user, req.NewPassword);
        user.RestoreCode = null;
        await db.SaveChangesAsync(ct);
        return TypedResults.Ok(new MessageResponse("Password reset successfully"));
    }

    private static async Task<Results<Ok<TokenResponse>, Created<TokenResponse>, UnauthorizedHttpResult, ForbidHttpResult>> GoogleLogin(
        GoogleLoginRequest req, AppDbContext db, GoogleTokenValidator google, JwtTokenService jwt,
        EmailQueue emailQueue, CancellationToken ct)
    {
        var info = await google.ValidateAsync(req.IdToken);
        if (info is null) return TypedResults.Unauthorized();
        if (!info.EmailVerified || string.IsNullOrEmpty(info.Email)) return TypedResults.Unauthorized();

        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == info.Email, ct);
        var created = false;
        if (user is null)
        {
            user = new User
            {
                Email = info.Email,
                FirstName = info.GivenName ?? "",
                LastName = info.FamilyName ?? "",
                IsValidate = true,
                PasswordHash = null, // OAuth-only account, no usable password
            };
            db.Users.Add(user);
            await db.SaveChangesAsync(ct);
            created = true;
            await emailQueue.QueueWelcomeEmail(user.Email, user.FirstName ?? "User");
        }

        if (!user.IsActive) return TypedResults.Forbid();

        var response = BuildTokenResponse(user, jwt) with { Created = created ? true : null };
        return created
            ? TypedResults.Created($"/api/users/{user.Id}", response)
            : TypedResults.Ok(response);
    }

    private static async Task<Results<Ok<TokenResponse>, UnauthorizedHttpResult>> RefreshToken(
        RefreshRequest req, AppDbContext db, JwtTokenService jwt, CancellationToken ct)
    {
        var userId = jwt.ValidateRefreshToken(req.RefreshToken);
        if (userId is null) return TypedResults.Unauthorized();

        var user = await db.Users.FirstOrDefaultAsync(u => u.Id == userId, ct);
        if (user is null || !user.IsActive) return TypedResults.Unauthorized();

        return TypedResults.Ok(BuildTokenResponse(user, jwt));
    }

    private static TokenResponse BuildTokenResponse(User user, JwtTokenService jwt)
    {
        var pair = jwt.CreateTokenPair(user);
        return new TokenResponse(pair.Token, pair.RefreshToken, UserDto.From(user));
    }

    /// <summary>Cryptographically secure 6-digit reset code (matches <c>api.utils.generate_code</c>).</summary>
    private static string GenerateCode() => RandomNumberGenerator.GetInt32(100000, 1000000).ToString();
}
