using FrontierWeb.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;


//TESTING ONLY
//TODO: REMOVE

namespace FrontierWeb.Infrastructure
{
    public static class DataSeeder
    {
        public static async Task SeedAsync(IServiceProvider sp)
        {
            using var scope = sp.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<BlogDbContext>();
            await db.Database.EnsureCreatedAsync();

            var adminRole = await db.Roles
                .Include(r => r.RolePermissions)
                .ThenInclude(rp => rp.Permission)
                .FirstOrDefaultAsync(r => r.Name == "Admin");
            if (adminRole is null)
            {
                adminRole = new Role { Name = "Admin" };
                db.Roles.Add(adminRole);
            }

            foreach (var permissionName in new[] { "posts.read", "posts.write", "users.manage" })
            {
                var permission = await db.Permissions.FirstOrDefaultAsync(p => p.Name == permissionName);
                if (permission is null)
                {
                    permission = new Permission { Name = permissionName };
                    db.Permissions.Add(permission);
                }

                if (!adminRole.RolePermissions.Any(rp => rp.Permission == permission))
                    adminRole.RolePermissions.Add(new RolePermission { Role = adminRole, Permission = permission });
            }

            if (!await db.Users.AnyAsync())
            {
                db.Users.Add(new User
                {
                    Username = "admin",
                    PasswordHash = PasswordHash.Create("admin123"),
                    UserRoles = { new UserRole { Role = adminRole } }
                });
            }

            if (!await db.Posts.AnyAsync())
            {
                db.Posts.Add(new Post
                {
                    Title = "Hello, world!",
                    Slug = "hello-world",
                    Content = "This is your first post.",
                    Published = true,
                    CreatedAtUtc = DateTime.UtcNow,
                    UpdatedAtUtc = DateTime.UtcNow
                });
            }

            await db.SaveChangesAsync();
        }
    }
}
