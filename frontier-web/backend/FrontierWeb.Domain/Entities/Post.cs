using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Domain.Entities
{
    public class Post
    {
        public int Id { get; set; }

        [Required, StringLength(200)]
        public string Title { get; set; } = default!;

        [Required, StringLength(200)]
        public string Slug { get; set; } = default!;

        [Required]
        public string Content { get; set; } = default!;

        [Required]
        public string Notes { get; set; } = "1. Placeholder";

        [Required, StringLength(200)]
        public string Author { get; set; } = "Frontier";

        [Required]
        public string Image { get; set; } = "placeholder.png";

        public bool Published { get; set; } = true;

        public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
        public DateTime UpdatedAtUtc { get; set; } = DateTime.UtcNow;
    }
}
