using FrontierWeb.Application.DTO;

namespace FrontierWeb.Application.Interfaces
{
    public interface IAuthService
    {
        Task<TokenResponse?> LoginAsync(LoginRequest request, CancellationToken ct = default);
    }
}
