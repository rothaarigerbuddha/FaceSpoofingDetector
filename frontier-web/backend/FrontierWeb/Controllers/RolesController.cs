using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace FrontierWeb.Api.Controllers
{
    [ApiController]
    [Route("roles")]
    public class RolesController : ControllerBase
    {
        private readonly IRoleService _roles;

        public RolesController(IRoleService roles) => _roles = roles;

        [HttpGet]
        public async Task<IActionResult> List(CancellationToken ct)
            => Ok(await _roles.ListAsync(ct));

        [HttpGet("{id:int}")]
        public async Task<IActionResult> Get(int id, CancellationToken ct)
        {
            var role = await _roles.GetByIdAsync(id, ct);
            return role is null ? NotFound() : Ok(role);
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] RoleCreateRequest req, CancellationToken ct)
        {
            var (ok, error, role) = await _roles.CreateAsync(req, ct);
            if (!ok) return Conflict(error);
            return CreatedAtAction(nameof(Get), new { id = role!.Id }, role);
        }

        [HttpPut("{id:int}/permissions")]
        public async Task<IActionResult> AssignPermissions(int id, [FromBody] AssignPermissionsRequest req, CancellationToken ct)
        {
            var (ok, error, role) = await _roles.AssignPermissionsAsync(id, req, ct);
            if (!ok && error is null) return NotFound();
            if (!ok) return Conflict(error);
            return Ok(role);
        }

        [HttpDelete("{id:int}")]
        public async Task<IActionResult> Delete(int id, CancellationToken ct)
            => await _roles.DeleteAsync(id, ct) ? NoContent() : NotFound();
    }
}
