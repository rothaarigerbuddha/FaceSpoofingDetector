using FrontierWeb.Application.DTO;

namespace FrontierWeb.Application.Interfaces
{
    public interface IUserService
    {
        Task<IEnumerable<UserResponse>> ListAsync(CancellationToken ct = default);
        Task<UserResponse?> GetByIdAsync(int id, CancellationToken ct = default);
        Task<IEnumerable<PermissionResponse>?> GetPermissionsAsync(int id, CancellationToken ct = default);
        Task<(bool ok, string? error, UserResponse? user)> CreateAsync(UserCreateRequest req, CancellationToken ct = default);
        Task<(bool ok, string? error, UserResponse? user)> AssignRolesAsync(int id, AssignRolesRequest req, CancellationToken ct = default);
        Task<bool> DeleteAsync(int id, CancellationToken ct = default);
    }
}
