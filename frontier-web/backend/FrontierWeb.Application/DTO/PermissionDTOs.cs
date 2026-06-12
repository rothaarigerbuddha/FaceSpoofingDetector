using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Application.DTO
{
    public record PermissionCreateRequest([Required, StringLength(100)] string Name);

    public record PermissionResponse(int Id, string Name);
}
