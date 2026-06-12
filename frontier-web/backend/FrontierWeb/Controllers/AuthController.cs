using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace FrontierWeb.Api.Controllers
{
    [ApiController]
    [Route("auth")]
    public class AuthController : ControllerBase
    {
        private readonly IAuthService _auth;

        public AuthController(IAuthService auth) => _auth = auth;

        [HttpPost("login")]
        [ProducesResponseType(typeof(TokenResponse), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status401Unauthorized)]
        public async Task<IActionResult> Login([FromBody] LoginRequest request, CancellationToken ct)
        {
            var token = await _auth.LoginAsync(request, ct);
            return token is null ? Unauthorized() : Ok(token);
        }
    }
}
