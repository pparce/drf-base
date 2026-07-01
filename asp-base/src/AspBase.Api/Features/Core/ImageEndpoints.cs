using AspBase.Api.Common;
using AspBase.Api.Domain.Entities;
using AspBase.Api.Infrastructure.Data;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

namespace AspBase.Api.Features.Core;

public record ImageDto(long Id, string? Image, int Height, int Width, string ImageHash, DateTime CreatedAt)
{
    public static ImageDto From(Image i) => new(i.Id, i.ImagePath, i.Height, i.Width, i.ImageHash, i.CreatedAt);
}

/// <summary>
/// Image CRUD endpoints, the Minimal-API equivalent of the DRF <c>ImageViewSet</c>.
/// Uploads are stored on disk under the media root; dimensions/hash are placeholders
/// (the DRF project likewise had image processing commented out).
/// </summary>
public static class ImageEndpoints
{
    public static IEndpointRouteBuilder MapImageEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/core/image")
            .WithTags("Core")
            .RequireAuthorization()
            .RequireRateLimiting("user");

        group.MapGet("/", List);
        group.MapGet("/{id:long}", Get);
        group.MapPost("/", Upload).DisableAntiforgery();
        group.MapDelete("/{id:long}", Delete);

        return app;
    }

    private static async Task<Ok<PagedResult<ImageDto>>> List(
        [AsParameters] PageQuery paging, HttpRequest request, AppDbContext db, CancellationToken ct)
    {
        var page = await db.Images.AsNoTracking().OrderByDescending(i => i.CreatedAt)
            .Select(i => new ImageDto(i.Id, i.ImagePath, i.Height, i.Width, i.ImageHash, i.CreatedAt))
            .ToPagedResultAsync(paging, request, ct);
        return TypedResults.Ok(page);
    }

    private static async Task<Results<Ok<ImageDto>, NotFound>> Get(long id, AppDbContext db, CancellationToken ct)
    {
        var image = await db.Images.AsNoTracking().FirstOrDefaultAsync(i => i.Id == id, ct);
        return image is null ? TypedResults.NotFound() : TypedResults.Ok(ImageDto.From(image));
    }

    private static async Task<Results<Created<ImageDto>, BadRequest<ErrorResponse>>> Upload(
        IFormFile? file, AppDbContext db, FileStorage storage, CancellationToken ct)
    {
        if (file is null || file.Length == 0)
            return TypedResults.BadRequest(new ErrorResponse("An image file is required"));

        var path = await storage.SaveAsync(file, "images", ct);
        var image = new Image { ImagePath = path };
        db.Images.Add(image);
        await db.SaveChangesAsync(ct);

        return TypedResults.Created($"/api/core/image/{image.Id}", ImageDto.From(image));
    }

    private static async Task<Results<NoContent, NotFound>> Delete(long id, AppDbContext db, CancellationToken ct)
    {
        var image = await db.Images.FirstOrDefaultAsync(i => i.Id == id, ct);
        if (image is null) return TypedResults.NotFound();
        db.Images.Remove(image);
        await db.SaveChangesAsync(ct);
        return TypedResults.NoContent();
    }
}
