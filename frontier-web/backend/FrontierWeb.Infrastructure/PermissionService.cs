using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using FrontierWeb.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FrontierWeb.Infrastructure
{
    public class PermissionService : IPermissionService
    {
        private readonly BlogDbContext _db;

        public PermissionService(BlogDbContext db) => _db = db;

        public async Task<IEnumerable<PermissionResponse>> ListAsync(CancellationToken ct = default)
        {
            var permissions = await _db.Permissions.AsNoTracking()
                .OrderBy(p => p.Name)
                .ToListAsync(ct);

            return permissions.Select(p => p.ToResponse()).ToList();
        }

        public async Task<PermissionResponse?> GetByIdAsync(int id, CancellationToken ct = default)
        {
            var permission = await _db.Permissions.AsNoTracking()
                .FirstOrDefaultAsync(p => p.Id == id, ct);

            return permission?.ToResponse();
        }

        public async Task<(bool ok, string? error, PermissionResponse? permission)> CreateAsync(PermissionCreateRequest req, CancellationToken ct = default)
        {
            var name = req.Name.Trim();

            if (await _db.Permissions.AnyAsync(p => p.Name == name, ct))
                return (false, "Permission name must be unique.", null);

            var permission = new Permission { Name = name };
            _db.Permissions.Add(permission);
            await _db.SaveChangesAsync(ct);

            return (true, null, permission.ToResponse());
        }

        public async Task<bool> DeleteAsync(int id, CancellationToken ct = default)
        {
            var permission = await _db.Permissions.FirstOrDefaultAsync(p => p.Id == id, ct);
            if (permission is null) return false;

            _db.Permissions.Remove(permission);
            await _db.SaveChangesAsync(ct);
            return true;
        }
    }
}
