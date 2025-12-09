#!/usr/bin/env bash
set -euo pipefail

# Ожидаем, что IMAGE придёт из GitHub Actions как переменная окружения
: "${IMAGE:?IMAGE environment variable must be set, e.g. ghcr.io/OWNER/REPO:tag}"

APP_NAME="crystalpine-backend"
APP_PORT="18080"

echo "[deploy] Using image: ${IMAGE}"

echo "[deploy] Pulling latest image..."
sudo docker pull "${IMAGE}"

echo "[deploy] Stopping existing container (if any)..."
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${APP_NAME}$"; then
  sudo docker stop "${APP_NAME}" || true
  sudo docker rm "${APP_NAME}" || true
fi

echo "[deploy] Starting new container on port ${APP_PORT}..."
sudo docker run -d \
  --name "${APP_NAME}" \
  -p ${APP_PORT}:8000 \
  --restart unless-stopped \
  -e APP_ENV=prod \
  "${IMAGE}"

echo "[deploy] Deployment finished. Current containers:"
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
