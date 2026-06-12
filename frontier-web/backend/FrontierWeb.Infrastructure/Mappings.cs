using FrontierWeb.Application.DTO;
using FrontierWeb.Domain.Entities;

namespace FrontierWeb.Infrastructure
{
    internal static class Mappings
    {
        public static PermissionResponse ToResponse(this Permission permission)
            => new(permission.Id, permission.Name);

        public static RoleResponse ToResponse(this Role role)
            => new(role.Id, role.Name,
                role.RolePermissions.Select(rp => rp.Permission.ToResponse()).ToList());

        public static UserResponse ToResponse(this User user)
            => new(user.Id, user.Username,
                user.UserRoles.Select(ur => ur.Role.ToResponse()).ToList());
    }
}
