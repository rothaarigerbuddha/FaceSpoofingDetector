using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using FrontierWeb.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FrontierWeb.Infrastructure
{
    public class UserService : IUserService
    {
        private readonly BlogDbContext _db;

        public UserService(BlogDbContext db) => _db = db;

        private IQueryable<User> UsersWithRoles(bool tracking)
        {
            var query = tracking ? _db.Users : _db.Users.AsNoTracking();
            return query
                .Include(u => u.UserRoles)
                .ThenInclude(ur => ur.Role)
                .ThenInclude(r => r.RolePermissions)
                .ThenInclude(rp => rp.Permission);
        }

        public async Task<IEnumerable<UserResponse>> ListAsync(CancellationToken ct = default)
        {
            var users = await UsersWithRoles(tracking: false)
                .OrderBy(u => u.Username)
                .ToListAsync(ct);

            return users.Select(u => u.ToResponse()).ToList();
        }

        public async Task<UserResponse?> GetByIdAsync(int id, CancellationToken ct = default)
        {
            var user = await UsersWithRoles(tracking: false)
                .FirstOrDefaultAsync(u => u.Id == id, ct);

            return user?.ToResponse();
        }

        public async Task<IEnumerable<PermissionResponse>?> GetPermissionsAsync(int id, CancellationToken ct = default)
        {
            var user = await UsersWithRoles(tracking: false)
                .FirstOrDefaultAsync(u => u.Id == id, ct);

            if (user is null)
                return null;

            return user.UserRoles
                .SelectMany(ur => ur.Role.RolePermissions)
                .Select(rp => rp.Permission)
                .DistinctBy(p => p.Id)
                .OrderBy(p => p.Name)
                .Select(p => p.ToResponse())
                .ToList();
        }

        public async Task<(bool ok, string? error, UserResponse? user)> CreateAsync(UserCreateRequest req, CancellationToken ct = default)
        {
            var username = req.Username.Trim();

            if (await _db.Users.AnyAsync(u => u.Username == username, ct))
                return (false, "Username must be unique.", null);

            var roleIds = (req.RoleIds ?? Enumerable.Empty<int>()).Distinct().ToList();
            var error = await ValidateRoleIdsAsync(roleIds, ct);
            if (error is not null)
                return (false, error, null);

            var user = new User
            {
                Username = username,
                PasswordHash = PasswordHash.Create(req.Password),
                UserRoles = roleIds.Select(rid => new UserRole { RoleId = rid }).ToList()
            };

            _db.Users.Add(user);
            await _db.SaveChangesAsync(ct);

            var saved = await UsersWithRoles(tracking: false).FirstAsync(u => u.Id == user.Id, ct);
            return (true, null, saved.ToResponse());
        }

        public async Task<(bool ok, string? error, UserResponse? user)> AssignRolesAsync(int id, AssignRolesRequest req, CancellationToken ct = default)
        {
            var user = await _db.Users
                .Include(u => u.UserRoles)
                .FirstOrDefaultAsync(u => u.Id == id, ct);

            if (user is null)
                return (false, null, null);

            var roleIds = req.RoleIds.Distinct().ToList();
            var error = await ValidateRoleIdsAsync(roleIds, ct);
            if (error is not null)
                return (false, error, null);

            user.UserRoles.Clear();
            foreach (var roleId in roleIds)
                user.UserRoles.Add(new UserRole { UserId = user.Id, RoleId = roleId });

            await _db.SaveChangesAsync(ct);

            var saved = await UsersWithRoles(tracking: false).FirstAsync(u => u.Id == id, ct);
            return (true, null, saved.ToResponse());
        }

        public async Task<bool> DeleteAsync(int id, CancellationToken ct = default)
        {
            var user = await _db.Users.FirstOrDefaultAsync(u => u.Id == id, ct);
            if (user is null) return false;

            _db.Users.Remove(user);
            await _db.SaveChangesAsync(ct);
            return true;
        }

        private async Task<string?> ValidateRoleIdsAsync(IReadOnlyCollection<int> roleIds, CancellationToken ct)
        {
            if (roleIds.Count == 0) return null;

            var existingIds = await _db.Roles
                .Where(r => roleIds.Contains(r.Id))
                .Select(r => r.Id)
                .ToListAsync(ct);

            var missing = roleIds.Except(existingIds).ToList();
            return missing.Count > 0 ? $"Unknown role ids: {string.Join(", ", missing)}." : null;
        }
    }
}
