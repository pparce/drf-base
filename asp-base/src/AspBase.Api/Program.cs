using System.Threading.RateLimiting;
using AspBase.Api.Common;
using AspBase.Api.Features.Auth;
using AspBase.Api.Features.Core;
using AspBase.Api.Features.Health;
using AspBase.Api.Features.Users;
using AspBase.Api.Infrastructure.Auth;
using AspBase.Api.Infrastructure.Data;
using AspBase.Api.Infrastructure.Email;
using AspBase.Api.Infrastructure.Options;
using FluentValidation;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.FileProviders;
using Microsoft.OpenApi.Models;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// ── Logging (Serilog) ─────────────────────────────────────────────────────
builder.Host.UseSerilog((ctx, cfg) => cfg.ReadFrom.Configuration(ctx.Configuration).WriteTo.Console());

// ── Options (bound + validated on start) ──────────────────────────────────
builder.Services.AddOptions<JwtOptions>().Bind(builder.Configuration.GetSection(JwtOptions.SectionName))
    .ValidateDataAnnotations().ValidateOnStart();
builder.Services.Configure<GoogleOptions>(builder.Configuration.GetSection(GoogleOptions.SectionName));
builder.Services.Configure<EmailOptions>(builder.Configuration.GetSection(EmailOptions.SectionName));
builder.Services.Configure<MediaOptions>(builder.Configuration.GetSection(MediaOptions.SectionName));

// ── Database (PostgreSQL via EF Core) ─────────────────────────────────────
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseNpgsql(builder.Configuration.GetConnectionString("Default")));

// ── Application services ──────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ClaimsPrincipalAccessor>();
builder.Services.AddSingleton<JwtTokenService>();
builder.Services.AddSingleton<PasswordHashingService>();
builder.Services.AddSingleton<GoogleTokenValidator>();
builder.Services.AddSingleton<FileStorage>();
builder.Services.AddScoped<IEmailService, EmailService>();
builder.Services.AddSingleton<EmailQueue>();
builder.Services.AddHostedService<EmailBackgroundService>();
builder.Services.AddValidatorsFromAssembly(typeof(Program).Assembly);

// ── AuthN / AuthZ ─────────────────────────────────────────────────────────
var jwtOptions = builder.Configuration.GetSection(JwtOptions.SectionName).Get<JwtOptions>() ?? new JwtOptions();
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        var tokenService = new JwtTokenService(Microsoft.Extensions.Options.Options.Create(jwtOptions));
        options.TokenValidationParameters = tokenService.TokenValidationParameters;
        // Reject refresh tokens on protected endpoints — only "access" tokens are valid there.
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = ctx =>
            {
                if (ctx.Principal?.FindFirst("token_type")?.Value != "access")
                    ctx.Fail("Only access tokens are accepted.");
                return Task.CompletedTask;
            },
        };
    });

builder.Services.AddAuthorizationBuilder()
    .AddPolicy(Policies.StaffOnly, policy => policy.RequireRole(Roles.Staff, Roles.Superuser));

// ── CORS (restricted to configured origins, /api only) ────────────────────
const string CorsPolicy = "AppCors";
var corsOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>() ?? [];
builder.Services.AddCors(options => options.AddPolicy(CorsPolicy, policy =>
{
    if (corsOrigins.Length > 0)
        policy.WithOrigins(corsOrigins).AllowAnyHeader().AllowAnyMethod().AllowCredentials();
    else
        policy.AllowAnyHeader().AllowAnyMethod();
}));

// ── Rate limiting (anon / user / auth scopes, DRF throttling equivalent) ──
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    // Global limiter for anonymous traffic, partitioned by client IP.
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(ctx =>
        RateLimitPartition.GetFixedWindowLimiter(
            ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            _ => new FixedWindowRateLimiterOptions { PermitLimit = 100, Window = TimeSpan.FromDays(1) }));

    // Authenticated users: 1000/day, partitioned by user id (falls back to IP).
    options.AddPolicy("user", ctx => RateLimitPartition.GetFixedWindowLimiter(
        ctx.User.GetUserId()?.ToString() ?? ctx.Connection.RemoteIpAddress?.ToString() ?? "anon",
        _ => new FixedWindowRateLimiterOptions { PermitLimit = 1000, Window = TimeSpan.FromDays(1) }));

    // Auth endpoints: stricter 10/minute per IP.
    options.AddPolicy("auth", ctx => RateLimitPartition.GetFixedWindowLimiter(
        ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown",
        _ => new FixedWindowRateLimiterOptions { PermitLimit = 10, Window = TimeSpan.FromMinutes(1) }));
});

// ── OpenAPI / Swagger with JWT bearer support ─────────────────────────────
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "ASP Base API", Version = "1.0.0", Description = "ASP.NET Core port of the DRF base project." });
    var scheme = new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header,
        Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" },
    };
    c.AddSecurityDefinition("Bearer", scheme);
    c.AddSecurityRequirement(new OpenApiSecurityRequirement { [scheme] = Array.Empty<string>() });
});

var app = builder.Build();

// ── Middleware pipeline ───────────────────────────────────────────────────
app.UseSerilogRequestLogging();

// Security headers (DRF SECURE_* settings equivalent).
app.Use(async (ctx, next) =>
{
    ctx.Response.Headers["X-Content-Type-Options"] = "nosniff";
    ctx.Response.Headers["X-Frame-Options"] = "DENY";
    ctx.Response.Headers["X-XSS-Protection"] = "1; mode=block";
    await next();
});

if (!app.Environment.IsDevelopment())
{
    app.UseHsts();
    app.UseHttpsRedirection();
}

app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "ASP Base API v1");
    c.RoutePrefix = "swagger";
});

// Serve uploaded media files.
var mediaOptions = app.Services.GetRequiredService<Microsoft.Extensions.Options.IOptions<MediaOptions>>().Value;
var mediaRoot = Path.GetFullPath(mediaOptions.Root);
Directory.CreateDirectory(mediaRoot);
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(mediaRoot),
    RequestPath = mediaOptions.RequestPath,
});

app.UseCors(CorsPolicy);
app.UseAuthentication();
app.UseAuthorization();
// After authentication so the "user" policy can partition by the authenticated user id.
app.UseRateLimiter();

// ── Endpoints ─────────────────────────────────────────────────────────────
app.MapGet("/", () => Results.Redirect("/swagger")).ExcludeFromDescription();
app.MapHealthEndpoints();
app.MapAuthEndpoints();
app.MapUserEndpoints();
app.MapImageEndpoints();

// ── Apply migrations on startup (skips in test host) ──────────────────────
if (app.Configuration.GetValue("Database:AutoMigrate", true))
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.MigrateAsync();
}

app.Run();

// Exposed for integration tests (WebApplicationFactory<Program>).
public partial class Program;
