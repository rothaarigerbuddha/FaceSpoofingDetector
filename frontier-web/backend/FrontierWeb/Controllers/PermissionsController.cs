using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace FrontierWeb.Api.Controllers
{
    [ApiController]
    [Route("permissions")]
    public class PermissionsController : ControllerBase
    {
        private readonly IPermissionService _permissions;

        public PermissionsController(IPermissionService permissions) => _permissions = permissions;

        [HttpGet]
        public async Task<IActionResult> List(CancellationToken ct)
            => Ok(await _permissions.ListAsync(ct));

        [HttpGet("{id:int}")]
        public async Task<IActionResult> Get(int id, CancellationToken ct)
        {
            var permission = await _permissions.GetByIdAsync(id, ct);
            return permission is null ? NotFound() : Ok(permission);
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] PermissionCreateRequest req, CancellationToken ct)
        {
            var (ok, error, permission) = await _permissions.CreateAsync(req, ct);
            if (!ok) return Conflict(error);
            return CreatedAtAction(nameof(Get), new { id = permission!.Id }, permission);
        }

        [HttpDelete("{id:int}")]
        public async Task<IActionResult> Delete(int id, CancellationToken ct)
            => await _permissions.DeleteAsync(id, ct) ? NoContent() : NotFound();
    }
}
