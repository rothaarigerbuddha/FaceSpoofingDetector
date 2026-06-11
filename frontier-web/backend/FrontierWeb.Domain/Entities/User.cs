using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Domain.Entities
{
    public class User
    {
        public int Id { get; set; }

        [Required, StringLength(100)]
        public string Username { get; set; } = default!;

        [Required]
        public string PasswordHash { get; set; } = default!;

        public ICollection<UserRole> UserRoles { get; set; } = new List<UserRole>();
    }
}
