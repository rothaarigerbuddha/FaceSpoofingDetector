using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Application.DTO
{
    public record UserCreateRequest(
        [Required, StringLength(100)] string Username,
        [Required, StringLength(100, MinimumLength = 6)] string Password,
        IEnumerable<int>? RoleIds = null);

    public record AssignRolesRequest([Required] IEnumerable<int> RoleIds);

    public record UserResponse(int Id, string Username, IEnumerable<RoleResponse> Roles);
}
