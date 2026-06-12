# syntax=docker/dockerfile:1

# ---- build stage ----
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Restore first (better layer caching): copy only project files.
COPY FrontierWeb/FrontierWeb.Api.csproj FrontierWeb/
COPY FrontierWeb.Application/FrontierWeb.Application.csproj FrontierWeb.Application/
COPY FrontierWeb.Domain/FrontierWeb.Domain.csproj FrontierWeb.Domain/
COPY FrontierWeb.Infrastructure/FrontierWeb.Infrastructure.csproj FrontierWeb.Infrastructure/
RUN dotnet restore FrontierWeb/FrontierWeb.Api.csproj

# Copy the rest and publish.
COPY . .
RUN dotnet publish FrontierWeb/FrontierWeb.Api.csproj -c Release -o /app /p:UseAppHost=false

# ---- runtime stage ----
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app

# curl is only needed for the compose healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /app ./

# Persisted SQLite database lives in a mounted volume (see docker-compose.yml).
RUN mkdir -p /app/data
ENV ASPNETCORE_URLS=http://0.0.0.0:5160
EXPOSE 5160

ENTRYPOINT ["dotnet", "FrontierWeb.Api.dll"]
