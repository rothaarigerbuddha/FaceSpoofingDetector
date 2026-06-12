#!/usr/bin/env bash
#
# run.sh — bring up the whole Frontier stack (frontend + backend) with Docker
# Compose, then open a public Cloudflare quick tunnel to the frontend so you can
# view/share it from any device — no domain or hosting required.
#
# Usage:
#   ./run.sh              # build, start, and open a public tunnel
#   ./run.sh --no-tunnel  # build and start only (view locally at http://localhost:3000)
#   ./run.sh down         # stop and remove the stack
#
set -euo pipefail
cd "$(dirname "$0")"

FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:5160"

# Pick "docker compose" (v2) or fall back to "docker-compose" (v1).
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "ERROR: Docker Compose not found. Install Docker Desktop / Docker Engine first." >&2
  exit 1
fi

# Handle "down".
if [[ "${1:-}" == "down" ]]; then
  echo "==> Stopping the stack..."
  $DC down
  exit 0
fi

TUNNEL=1
[[ "${1:-}" == "--no-tunnel" ]] && TUNNEL=0

echo "==> Building and starting containers (this can take a few minutes the first time)..."
$DC up -d --build

echo "==> Waiting for the frontend to become ready at ${FRONTEND_URL} ..."
for _ in $(seq 1 90); do
  if curl -sf "${FRONTEND_URL}" >/dev/null 2>&1; then
    echo "    Frontend is up."
    break
  fi
  sleep 2
done

echo ""
echo "==================================================================="
echo "  Stack is running:"
echo "    Frontend : ${FRONTEND_URL}"
echo "    Backend  : ${BACKEND_URL}        (Swagger: ${BACKEND_URL}/swagger)"
echo "    Login    : admin / admin123"
echo "  Stop with:  ./run.sh down"
echo "==================================================================="
echo ""

if [[ "$TUNNEL" -eq 0 ]]; then
  echo "Started without a tunnel (--no-tunnel). Open ${FRONTEND_URL} in your browser."
  exit 0
fi

# --- ensure cloudflared is available ---
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "==> cloudflared not found — downloading a local copy..."
  OS="$(uname -s)"; ARCH="$(uname -m)"
  case "$OS" in
    Linux)  PLAT="linux" ;;
    Darwin) PLAT="darwin" ;;
    *) echo "Unsupported OS '$OS'. Install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" >&2; exit 1 ;;
  esac
  case "$ARCH" in
    x86_64|amd64) CARCH="amd64" ;;
    arm64|aarch64) CARCH="arm64" ;;
    *) echo "Unsupported arch '$ARCH'. Install cloudflared manually." >&2; exit 1 ;;
  esac
  URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-${PLAT}-${CARCH}"
  curl -fsSL "$URL" -o ./cloudflared
  chmod +x ./cloudflared
  CLOUDFLARED="./cloudflared"
else
  CLOUDFLARED="cloudflared"
fi

echo "==> Opening a public Cloudflare tunnel to ${FRONTEND_URL}"
echo "    Look for the https://<random>.trycloudflare.com URL below."
echo "    Press Ctrl+C to close the tunnel (the containers keep running)."
echo ""
exec "$CLOUDFLARED" tunnel --no-autoupdate --url "${FRONTEND_URL}"
