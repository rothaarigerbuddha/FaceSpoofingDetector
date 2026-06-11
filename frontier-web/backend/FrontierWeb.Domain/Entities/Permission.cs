using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Domain.Entities
{
    public class Permission
    {
        public int Id { get; set; }

        [Required, StringLength(100)]
        public string Name { get; set; } = default!;

        public ICollection<RolePermission> RolePermissions { get; set; } = new List<RolePermission>();
    }
}
