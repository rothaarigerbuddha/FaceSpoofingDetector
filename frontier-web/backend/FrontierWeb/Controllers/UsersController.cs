using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace FrontierWeb.Api.Controllers
{
    [ApiController]
    [Route("users")]
    public class UsersController : ControllerBase
    {
        private readonly IUserService _users;

        public UsersController(IUserService users) => _users = users;

        [HttpGet]
        public async Task<IActionResult> List(CancellationToken ct)
            => Ok(await _users.ListAsync(ct));

        [HttpGet("{id:int}")]
        public async Task<IActionResult> Get(int id, CancellationToken ct)
        {
            var user = await _users.GetByIdAsync(id, ct);
            return user is null ? NotFound() : Ok(user);
        }

        [HttpGet("{id:int}/permissions")]
        public async Task<IActionResult> GetPermissions(int id, CancellationToken ct)
        {
            var permissions = await _users.GetPermissionsAsync(id, ct);
            return permissions is null ? NotFound() : Ok(permissions);
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] UserCreateRequest req, CancellationToken ct)
        {
            var (ok, error, user) = await _users.CreateAsync(req, ct);
            if (!ok) return Conflict(error);
            return CreatedAtAction(nameof(Get), new { id = user!.Id }, user);
        }

        [HttpPut("{id:int}/roles")]
        public async Task<IActionResult> AssignRoles(int id, [FromBody] AssignRolesRequest req, CancellationToken ct)
        {
            var (ok, error, user) = await _users.AssignRolesAsync(id, req, ct);
            if (!ok && error is null) return NotFound();
            if (!ok) return Conflict(error);
            return Ok(user);
        }

        [HttpDelete("{id:int}")]
        public async Task<IActionResult> Delete(int id, CancellationToken ct)
            => await _users.DeleteAsync(id, ct) ? NoContent() : NotFound();
    }
}
