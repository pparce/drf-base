namespace AspBase.Api.Domain.Entities;

/// <summary>
/// Base entity carrying audit timestamps, mirroring the DRF <c>BaseModel</c>/<c>BaseDate</c>.
/// <see cref="CreatedAt"/> is set on insert and <see cref="UpdatedAt"/> on every save
/// (handled centrally in <c>AppDbContext.SaveChanges</c>).
/// </summary>
public abstract class BaseEntity
{
    public long Id { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
