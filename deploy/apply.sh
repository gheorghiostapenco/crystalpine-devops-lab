#!/usr/bin/env bash
set -euo pipefail

# Ожидаем, что IMAGE придёт из GitHub Actions как переменная окружения
: "${IMAGE:?IMAGE environment variable must be set, e.g. ghcr.io/OWNER/REPO:tag}"

APP_NAME="crystalpine-backend"
APP_PORT="18080"
TRAEFIK_NETWORK="proxy_net"
ROUTER_NAME="crystalpine-lab"
SERVICE_NAME="crystalpine-lab"

echo "[deploy] Using image: ${IMAGE}"

echo "[deploy] Pulling latest image..."
sudo docker pull "${IMAGE}"

echo "[deploy] Stopping existing container (if any)..."
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${APP_NAME}$"; then
  sudo docker stop "${APP_NAME}" || true
  sudo docker rm "${APP_NAME}" || true
fi

echo "[deploy] Starting new container on port ${APP_PORT} and attaching to ${TRAEFIK_NETWORK}..."
sudo docker run -d \
  --name "${APP_NAME}" \
  --network "${TRAEFIK_NETWORK}" \
  -p ${APP_PORT}:8000 \
  --restart unless-stopped \
  -e APP_ENV=prod \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.${ROUTER_NAME}.entrypoints=websecure" \
  --label "traefik.http.routers.${ROUTER_NAME}.rule=Host(\"lab.crystalpine.dev\")" \
  --label "traefik.http.routers.${ROUTER_NAME}.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.${SERVICE_NAME}.loadbalancer.server.port=8000" \
  "${IMAGE}"

echo "[deploy] Deployment finished. Current containers:"
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
