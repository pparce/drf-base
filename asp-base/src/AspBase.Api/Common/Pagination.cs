using Microsoft.EntityFrameworkCore;

namespace AspBase.Api.Common;

/// <summary>Query-string paging parameters (page number + size), DRF <c>PageNumberPagination</c> style.</summary>
public record PageQuery(int Page = 1, int PageSize = 20)
{
    public const int DefaultPageSize = 20;
    public const int MaxPageSize = 100;

    public int NormalizedPage => Page < 1 ? 1 : Page;
    public int NormalizedPageSize => PageSize is < 1 or > MaxPageSize ? DefaultPageSize : PageSize;
}

/// <summary>Paged envelope matching DRF's <c>{ count, next, previous, results }</c> shape.</summary>
public record PagedResult<T>(int Count, string? Next, string? Previous, IReadOnlyList<T> Results);

public static class PaginationExtensions
{
    public static async Task<PagedResult<T>> ToPagedResultAsync<T>(
        this IQueryable<T> query, PageQuery paging, HttpRequest request, CancellationToken ct = default)
    {
        var page = paging.NormalizedPage;
        var size = paging.NormalizedPageSize;

        var count = await query.CountAsync(ct);
        var items = await query.Skip((page - 1) * size).Take(size).ToListAsync(ct);

        var hasNext = page * size < count;
        var hasPrevious = page > 1;

        return new PagedResult<T>(
            count,
            hasNext ? BuildPageUrl(request, page + 1, size) : null,
            hasPrevious ? BuildPageUrl(request, page - 1, size) : null,
            items);
    }

    private static string BuildPageUrl(HttpRequest request, int page, int size)
    {
        var baseUrl = $"{request.Scheme}://{request.Host}{request.Path}";
        return $"{baseUrl}?page={page}&pageSize={size}";
    }
}
