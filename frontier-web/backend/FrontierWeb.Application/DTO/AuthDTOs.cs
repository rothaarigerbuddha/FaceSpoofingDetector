using System.ComponentModel.DataAnnotations;

namespace FrontierWeb.Application.DTO
{
    public record LoginRequest([Required] string Username, [Required] string Password);
    public record TokenResponse(string access_token, string token_type, int expires_in);
}
