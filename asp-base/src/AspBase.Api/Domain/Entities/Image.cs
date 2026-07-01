namespace AspBase.Api.Domain.Entities;

/// <summary>
/// Uploaded image with cached dimensions and a perceptual hash placeholder,
/// mirroring the DRF <c>core.Image</c> model.
/// </summary>
public class Image : BaseEntity
{
    /// <summary>Relative path of the stored file under the media root.</summary>
    public string? ImagePath { get; set; }
    public int Height { get; set; }
    public int Width { get; set; }
    public string ImageHash { get; set; } = string.Empty;
}
