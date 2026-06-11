using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Domain.Entities
{
    public class Role
    {
        public int Id { get; set; }

        [Required, StringLength(50)]
        public string Name { get; set; } = default!;

        public ICollection<UserRole> UserRoles { get; set; } = new List<UserRole>();
        public ICollection<RolePermission> RolePermissions { get; set; } = new List<RolePermission>();
    }
}
