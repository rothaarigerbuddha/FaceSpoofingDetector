using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FrontierWeb.Api.Controllers
{
    [ApiController]
    [Route("uploads")]
    //[Authorize(Policy = "AdminOnly")]
    public class UploadsController : ControllerBase
    {
        private readonly IWebHostEnvironment _env;

        public UploadsController(IWebHostEnvironment env) => _env = env;

        [HttpPost]
        public async Task<IActionResult> Upload(IFormFile file)
        {
            if (file == null || file.Length == 0) return BadRequest("No file uploaded.");

            // Create unique filename
            var fileName = $"{Guid.NewGuid()}{Path.GetExtension(file.FileName)}";
            var uploadsPath = Path.Combine(_env.WebRootPath, "images/posts");
            
            if (!Directory.Exists(uploadsPath)) Directory.CreateDirectory(uploadsPath);

            var filePath = Path.Combine(uploadsPath, fileName);

            using (var stream = new FileStream(filePath, FileMode.Create))
            {
                await file.CopyToAsync(stream);
            }

            // Return the relative URL to be saved in the Post entity
            return Ok(new { url = $"{fileName}" });
        }
    }
}