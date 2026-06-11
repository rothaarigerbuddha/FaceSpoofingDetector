using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FrontierWeb.Api.Controllers
{
    [ApiController]
    [Route("posts")]
    public class PostsController : ControllerBase
    {
        private readonly IPostService _posts;

        public PostsController(IPostService posts) => _posts = posts;

        [HttpGet]
        public async Task<IActionResult> List([FromQuery] string? q, [FromQuery] int page = 1, [FromQuery] int pageSize = 10, [FromQuery] bool? published = true, CancellationToken ct = default)
            => Ok(await _posts.ListAsync(q, page, pageSize, published, ct));

        [HttpGet("{idOrSlug}")]
        public async Task<IActionResult> Get(string idOrSlug, CancellationToken ct = default)
        {
            var post = await _posts.GetByIdOrSlugAsync(idOrSlug, ct);
            return post is null ? NotFound() : Ok(post);
        }

        //[Authorize(Policy = "AdminOnly")]
        [HttpPost]
        public async Task<IActionResult> Create([FromBody] PostCreateRequest req, CancellationToken ct)
        {
            var (ok, error, post) = await _posts.CreateAsync(req, ct);
            if (!ok) return Conflict(error);
            return CreatedAtAction(nameof(Get), new { idOrSlug = post!.Id }, post);
        }

        //[Authorize(Policy = "AdminOnly")]
        [HttpPut("{id:int}")]
        public async Task<IActionResult> Update(int id, [FromBody] PostUpdateRequest req, CancellationToken ct)
        {
            var (ok, error, post) = await _posts.UpdateAsync(id, req, ct);
            if (!ok && error is null) return NotFound();
            if (!ok) return Conflict(error);
            return Ok(post);
        }

        //[Authorize(Policy = "AdminOnly")]
        [HttpDelete("{id:int}")]
        public async Task<IActionResult> Delete(int id, CancellationToken ct)
            => await _posts.DeleteAsync(id, ct) ? NoContent() : NotFound();
    }
}
