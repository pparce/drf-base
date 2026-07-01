using AspBase.Api.Infrastructure.Options;
using Microsoft.Extensions.Options;

namespace AspBase.Api.Common;

/// <summary>
/// Saves uploaded files to the local media root and returns their relative path,
/// the equivalent of Django's <c>ImageField.upload_to</c> behaviour.
/// </summary>
public class FileStorage(IOptions<MediaOptions> options)
{
    private readonly MediaOptions _opt = options.Value;

    public async Task<string> SaveAsync(IFormFile file, string subFolder, CancellationToken ct = default)
    {
        var folder = Path.Combine(_opt.Root, subFolder);
        Directory.CreateDirectory(folder);

        var ext = Path.GetExtension(file.FileName);
        var name = $"{Guid.NewGuid():N}{ext}";
        var fullPath = Path.Combine(folder, name);

        await using var stream = File.Create(fullPath);
        await file.CopyToAsync(stream, ct);

        // Stored path is relative and URL-friendly (forward slashes).
        return Path.Combine(subFolder, name).Replace('\\', '/');
    }
}
