using FrontierWeb.Application.DTO;
using FrontierWeb.Application.Interfaces;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;

namespace FrontierWeb.Infrastructure
{
    public class AuthService : IAuthService
    {
        private readonly BlogDbContext _db;
        private readonly IConfiguration _cfg;

        public AuthService(BlogDbContext db, IConfiguration cfg)
        {
            _db = db; _cfg = cfg;
        }

        public async Task<TokenResponse?> LoginAsync(LoginRequest request, CancellationToken ct = default)
        {
            var user = await _db.Users
                .Include(u => u.UserRoles)
                .ThenInclude(ur => ur.Role)
                .FirstOrDefaultAsync(u => u.Username == request.Username, ct);
            if (user is null) return null;
            if (!PasswordHash.Verify(user.PasswordHash, request.Password)) return null;

            var key = _cfg["Auth:Key"] ?? "CHANGE_ME_TO_A_LONG_RANDOM_SECRET";
            var issuer = _cfg["Auth:Issuer"] ?? "BlogApi";
            var audience = _cfg["Auth:Audience"] ?? "BlogApiClients";
            var creds = new SigningCredentials(new SymmetricSecurityKey(Encoding.UTF8.GetBytes(key)), SecurityAlgorithms.HmacSha256);

            var claims = new List<Claim> { new(ClaimTypes.Name, user.Username) };
            claims.AddRange(user.UserRoles.Select(ur => new Claim(ClaimTypes.Role, ur.Role.Name)));

            var expires = DateTime.UtcNow.AddHours(8);
            var token = new JwtSecurityToken(issuer, audience, claims, expires: expires, signingCredentials: creds);
            var jwt = new JwtSecurityTokenHandler().WriteToken(token);

            return new TokenResponse(jwt, "Bearer", (int)(expires - DateTime.UtcNow).TotalSeconds);
        }
    }
}
