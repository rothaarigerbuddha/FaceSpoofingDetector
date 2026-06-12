using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Application.DTO
{
    public record PostCreateRequest(
    [Required, StringLength(200)] string Title,
    [Required, StringLength(200)] string Slug,
    [Required] string Content,
    [Required] string Notes,
    [Required, StringLength(200)] string Author,
    [Required] string Image,
    bool Published = true);

    public record PostUpdateRequest(
        [StringLength(200)] string? Title,
        [StringLength(200)] string? Slug,
        string? Content,
        string? Notes,
        [StringLength(200)] string? Author,
        string? Image,
        bool? Published = true);

    public record Paged<T>(IEnumerable<T> Items, int Total, int Page, int PageSize);
}
