using AspBase.Api.Infrastructure.Data;
using Microsoft.AspNetCore.Http.HttpResults;

namespace AspBase.Api.Features.Health;

public record HealthResponse(string Status, string Database);

/// <summary>Anonymous health probe reporting database connectivity, mirroring the DRF <c>health_check</c>.</summary>
public static class HealthEndpoints
{
    public static IEndpointRouteBuilder MapHealthEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapGet("/api/health", async (AppDbContext db, CancellationToken ct) =>
            {
                var canConnect = await db.Database.CanConnectAsync(ct);
                var dbStatus = canConnect ? "ok" : "unavailable";
                return TypedResults.Ok(new HealthResponse(canConnect ? "ok" : "degraded", dbStatus));
            })
            .WithTags("Health")
            .AllowAnonymous()
            .WithName("HealthCheck");

        return app;
    }
}
