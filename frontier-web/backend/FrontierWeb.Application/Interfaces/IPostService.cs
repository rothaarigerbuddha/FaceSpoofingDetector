using FrontierWeb.Application.DTO;
using FrontierWeb.Domain.Entities;

namespace FrontierWeb.Application.Interfaces
{
    public interface IPostService
    {
        Task<Paged<Post>> ListAsync(string? q, int page, int pageSize, bool? published, CancellationToken ct = default);
        Task<Post?> GetByIdOrSlugAsync(string idOrSlug, CancellationToken ct = default);
        Task<(bool ok, string? error, Post? post)> CreateAsync(PostCreateRequest req, CancellationToken ct = default);
        Task<(bool ok, string? error, Post? post)> UpdateAsync(int id, PostUpdateRequest req, CancellationToken ct = default);
        Task<bool> DeleteAsync(int id, CancellationToken ct = default);
    }
}
