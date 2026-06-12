using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Application.DTO
{
    public record RoleCreateRequest([Required, StringLength(50)] string Name);

    public record AssignPermissionsRequest([Required] IEnumerable<int> PermissionIds);

    public record RoleResponse(int Id, string Name, IEnumerable<PermissionResponse> Permissions);
}
