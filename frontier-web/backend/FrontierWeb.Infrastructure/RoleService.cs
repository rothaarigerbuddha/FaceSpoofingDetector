using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using FrontierWeb.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FrontierWeb.Infrastructure
{
    public class RoleService : IRoleService
    {
        private readonly BlogDbContext _db;

        public RoleService(BlogDbContext db) => _db = db;

        private IQueryable<Role> RolesWithPermissions(bool tracking)
        {
            var query = tracking ? _db.Roles : _db.Roles.AsNoTracking();
            return query
                .Include(r => r.RolePermissions)
                .ThenInclude(rp => rp.Permission);
        }

        public async Task<IEnumerable<RoleResponse>> ListAsync(CancellationToken ct = default)
        {
            var roles = await RolesWithPermissions(tracking: false)
                .OrderBy(r => r.Name)
                .ToListAsync(ct);

            return roles.Select(r => r.ToResponse()).ToList();
        }

        public async Task<RoleResponse?> GetByIdAsync(int id, CancellationToken ct = default)
        {
            var role = await RolesWithPermissions(tracking: false)
                .FirstOrDefaultAsync(r => r.Id == id, ct);

            return role?.ToResponse();
        }

        public async Task<(bool ok, string? error, RoleResponse? role)> CreateAsync(RoleCreateRequest req, CancellationToken ct = default)
        {
            var name = req.Name.Trim();

            if (await _db.Roles.AnyAsync(r => r.Name == name, ct))
                return (false, "Role name must be unique.", null);

            var role = new Role { Name = name };
            _db.Roles.Add(role);
            await _db.SaveChangesAsync(ct);

            return (true, null, role.ToResponse());
        }

        public async Task<(bool ok, string? error, RoleResponse? role)> AssignPermissionsAsync(int id, AssignPermissionsRequest req, CancellationToken ct = default)
        {
            var role = await RolesWithPermissions(tracking: true)
                .FirstOrDefaultAsync(r => r.Id == id, ct);

            if (role is null)
                return (false, null, null);

            var permissionIds = req.PermissionIds.Distinct().ToList();

            var existingIds = await _db.Permissions
                .Where(p => permissionIds.Contains(p.Id))
                .Select(p => p.Id)
                .ToListAsync(ct);

            var missing = permissionIds.Except(existingIds).ToList();
            if (missing.Count > 0)
                return (false, $"Unknown permission ids: {string.Join(", ", missing)}.", null);

            role.RolePermissions.Clear();
            foreach (var permissionId in permissionIds)
                role.RolePermissions.Add(new RolePermission { RoleId = role.Id, PermissionId = permissionId });

            await _db.SaveChangesAsync(ct);

            var saved = await RolesWithPermissions(tracking: false)
                .FirstAsync(r => r.Id == id, ct);

            return (true, null, saved.ToResponse());
        }

        public async Task<bool> DeleteAsync(int id, CancellationToken ct = default)
        {
            var role = await _db.Roles.FirstOrDefaultAsync(r => r.Id == id, ct);
            if (role is null) return false;

            _db.Roles.Remove(role);
            await _db.SaveChangesAsync(ct);
            return true;
        }
    }
}
