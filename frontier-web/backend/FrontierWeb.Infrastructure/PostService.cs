using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using FrontierWeb.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FrontierWeb.Infrastructure
{
    public class PostService : IPostService
    {
        private readonly BlogDbContext _db;

        public PostService(BlogDbContext db) => _db = db;

        public async Task<Paged<Post>> ListAsync(string? q, int page, int pageSize, bool? published, CancellationToken ct = default)
        {
            page = Math.Max(1, page);
            pageSize = Math.Clamp(pageSize, 1, 100);

            var query = _db.Posts.AsNoTracking().AsQueryable();

            if (published is not null) query = query.Where(p => p.Published == published);
            if (!string.IsNullOrWhiteSpace(q))
                query = query.Where(p => p.Title.Contains(q) || p.Content.Contains(q) || p.Slug.Contains(q));

            var total = await query.CountAsync(ct);
            var items = await query.OrderByDescending(p => p.CreatedAtUtc)
                                   .Skip((page - 1) * pageSize)
                                   .Take(pageSize)
                                   .ToListAsync(ct);

            return new Paged<Post>(items, total, page, pageSize);
        }

        public async Task<Post?> GetByIdOrSlugAsync(string idOrSlug, CancellationToken ct = default)
        {
            if (int.TryParse(idOrSlug, out var id))
                return await _db.Posts.AsNoTracking().FirstOrDefaultAsync(p => p.Id == id, ct);

            return await _db.Posts.AsNoTracking().FirstOrDefaultAsync(p => p.Slug == idOrSlug, ct);
        }

        public async Task<(bool ok, string? error, Post? post)> CreateAsync(PostCreateRequest req, CancellationToken ct = default)
        {
            if (await _db.Posts.AnyAsync(p => p.Slug == req.Slug, ct))
                return (false, "Slug must be unique.", null);

            var post = new Post
            {
                Title = req.Title.Trim(),
                Slug = req.Slug.Trim(),
                Content = req.Content,
                Notes = req.Notes,
                Author = req.Author,
                Image = req.Image,
                Published = req.Published,
                CreatedAtUtc = DateTime.UtcNow,
                UpdatedAtUtc = DateTime.UtcNow
            };

            _db.Posts.Add(post);
            await _db.SaveChangesAsync(ct);
            return (true, null, post);
        }

        public async Task<(bool ok, string? error, Post? post)> UpdateAsync(int id, PostUpdateRequest req, CancellationToken ct = default)
        {
            var post = await _db.Posts
                .FirstOrDefaultAsync(p => p.Id == id, ct);

            if (post is null)
                return (false, null, null);

            if (!string.IsNullOrWhiteSpace(req.Slug))
            {
                var slug = req.Slug.Trim();

                var slugExists = await _db.Posts
                    .AnyAsync(p => p.Id != id && p.Slug == slug, ct);

                if (slugExists)
                    return (false, "Slug must be unique.", null);

                post.Slug = slug;
            }

            if (!string.IsNullOrWhiteSpace(req.Title))
                post.Title = req.Title.Trim();
            else 
                post.Title = post.Title;

            if (req.Content is not null)
                post.Content = req.Content;
            else 
                post.Content = post.Content;

            if (req.Notes is not null)
                post.Notes = req.Notes;
            else 
                post.Notes = post.Notes;

            if (req.Author is not null)
                post.Author = req.Author;
            else 
                post.Author = post.Author;

            if (req.Image is not null)
                post.Image = req.Image;
            else 
                post.Image = post.Image;

            if (req.Published.HasValue)
                post.Published = req.Published.Value;
            else 
                post.Published = post.Published;

            post.UpdatedAtUtc = DateTime.UtcNow;

            await _db.SaveChangesAsync(ct);

            return (true, null, post);
        }

        public async Task<bool> DeleteAsync(int id, CancellationToken ct = default)
        {
            var post = await _db.Posts.FirstOrDefaultAsync(p => p.Id == id, ct);
            if (post is null) return false;
            _db.Posts.Remove(post);
            await _db.SaveChangesAsync(ct);
            return true;
        }
    }
}
