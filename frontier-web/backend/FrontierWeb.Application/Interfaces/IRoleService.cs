using FrontierWeb.Application.DTO;

namespace FrontierWeb.Application.Interfaces
{
    public interface IRoleService
    {
        Task<IEnumerable<RoleResponse>> ListAsync(CancellationToken ct = default);
        Task<RoleResponse?> GetByIdAsync(int id, CancellationToken ct = default);
        Task<(bool ok, string? error, RoleResponse? role)> CreateAsync(RoleCreateRequest req, CancellationToken ct = default);
        Task<(bool ok, string? error, RoleResponse? role)> AssignPermissionsAsync(int id, AssignPermissionsRequest req, CancellationToken ct = default);
        Task<bool> DeleteAsync(int id, CancellationToken ct = default);
    }
}
