using FrontierWeb.Application.DTO;

namespace FrontierWeb.Application.Interfaces
{
    public interface IPermissionService
    {
        Task<IEnumerable<PermissionResponse>> ListAsync(CancellationToken ct = default);
        Task<PermissionResponse?> GetByIdAsync(int id, CancellationToken ct = default);
        Task<(bool ok, string? error, PermissionResponse? permission)> CreateAsync(PermissionCreateRequest req, CancellationToken ct = default);
        Task<bool> DeleteAsync(int id, CancellationToken ct = default);
    }
}
