# CrystalPine DevOps Lab

Self-hosted DevOps lab project running on an Oracle Cloud AlwaysFree ARM server.

The goal of this lab is to demonstrate an end-to-end DevOps workflow:

- GitHub as the source of truth
- CI/CD with GitHub Actions
- Docker image build & push to GitHub Container Registry (GHCR)
- ARM-compatible images for an ARM-based server
- SSH-based deployment to a self-hosted server
- Runtime in Docker with Traefik as reverse-proxy
- Public HTTPS endpoint behind Cloudflare
- Simple HTML dashboard powered by a FastAPI backend

---

## Live demo

- **Lab dashboard:** `https://lab.crystalpine.dev/`
  - Shows live application status, version, commit SHA, environment, hostname and timestamp.
- **Health check:** `https://lab.crystalpine.dev/healthz`
- **Status API:** `https://lab.crystalpine.dev/status`

> The project is intentionally simple on the application side and focused on the DevOps pipeline and runtime setup.

---

## High-level architecture

**Components:**

- **GitHub repository**
  - Source code (FastAPI backend + HTML dashboard).
  - CI/CD configuration in `.github/workflows/ci-cd.yml`.

- **GitHub Actions**
  - `test` job:
    - Installs backend dependencies.
    - Runs a simple smoke test (Python import).
  - `build_and_push` job:
    - Builds a Docker image for `linux/arm64/v8` using `docker/build-push-action`.
    - Pushes the image to GitHub Container Registry (GHCR).
  - `deploy` job:
    - Connects to the self-hosted server via SSH.
    - Clones or updates the repo on the server.
    - Calls `deploy/apply.sh` with:
      - `IMAGE` (GHCR image tag).
      - `APP_VERSION` (e.g. `0.1.0`).
      - `GIT_COMMIT` (GitHub SHA).

- **Self-hosted server (Oracle Cloud AlwaysFree)**
  - ARM-based VM.
  - Docker engine.
  - Traefik reverse-proxy (HTTPS termination, routing).
  - CrystalPine backend container:
    - Image from GHCR.
    - Exposed internally on port `8000`.
    - Exposed on host as `18080` for local debugging.
    - Registered in Traefik via labels.

- **Cloudflare + DNS**
  - `lab.crystalpine.dev` (A record) → server IP.
  - Cloudflare proxy (orange cloud) for HTTPS and protection.

---

## Request flow

1. User opens `https://lab.crystalpine.dev/`.
2. Cloudflare routes the request to the Oracle AlwaysFree VM.
3. Traefik terminates TLS and matches router rule:
   - `Host("lab.crystalpine.dev")` → service `crystalpine-lab`.
4. Traefik forwards the request to the `crystalpine-backend` container:
   - `loadbalancer.server.port = 8000`.
5. FastAPI backend:
   - Serves HTML dashboard on `/`.
   - Exposes `/healthz`, `/version`, `/status` API endpoints.

---

## Repository structure (current snapshot)

```text
crystalpine-devops-lab/
├─ app/
│  └─ backend/
│     ├─ main.py              # FastAPI app with /, /healthz, /version, /status
│     ├─ requirements.txt     # Backend dependencies
│     ├─ Dockerfile           # Container image for the backend
│     └─ __init__.py
├─ deploy/
│  └─ apply.sh                # SSH-deployed script to run/refresh the container
├─ .github/
│  └─ workflows/
│     └─ ci-cd.yml            # CI/CD pipeline: test → build ARM image → deploy
└─ README.md                  # This file
```

## Planned future structure:
```text

├─ app/
│  ├─ backend/                # API and dashboard (FastAPI)
│  └─ frontend/               # Optional SPA for extended UI
├─ k8s/                       # K3s/Kubernetes manifests (future)
├─ infra/
│  ├─ ansible/                # Server bootstrap (future)
│  └─ terraform/              # Cloudflare DNS & infra as code (future)
├─ monitoring/                # Prometheus/Grafana/Loki setup (future)
```
## CI/CD pipeline details

### Triggers

The workflow is defined in `.github/workflows/ci-cd.yml` and runs on:

- `push` to `main` and `develop`
- `pull_request` targeting `main` or `develop`

### Jobs

#### 1. `test`

- Checks out the repository.
- Sets up Python 3.12.
- Installs backend dependencies from `app/backend/requirements.txt`.
- Runs a basic smoke-test by importing the `main` module.

#### 2. `build_and_push`

- Runs after `test` passes.
- Uses `docker/setup-qemu-action` and `docker/setup-buildx-action` to build a Docker image for `linux/arm64/v8`.
- Uses `docker/build-push-action` to:
  - Build the image from `app/backend/Dockerfile`.
  - Tag the image as `ghcr.io/<OWNER>/<REPO>:<GITHUB_SHA>`.
  - Push the image to GitHub Container Registry (GHCR).
- Exposes the full image reference as an output for the `deploy` job.

#### 3. `deploy` (only for `main`)

- Runs only when the reference is `refs/heads/main`.
- Connects to the self-hosted server via SSH using secrets:
  - `SSH_HOST`
  - `SSH_USER`
  - `SSH_PRIVATE_KEY`
- Clones or updates the repository in `~/crystalpine-devops-lab` on the server.
- Calls `deploy/apply.sh` with environment variables:
  - `IMAGE` – the GHCR image reference.
  - `APP_VERSION` – currently a global workflow variable (e.g. `0.1.0`).
  - `GIT_COMMIT` – the GitHub commit SHA (`github.sha`).

---

## Deployment script (`deploy/apply.sh`)

The script is idempotent and safe to run multiple times:

- Pulls the specified Docker image:

  ```bash
  sudo docker pull "${IMAGE}"
- Stops and removes any existing container named `crystalpine-backend`.
- Starts a new container with:
  - `--network proxy_net` (Traefik network)
  - `-p 18080:8000` for local debugging
  - `-e APP_ENV=prod`
  - `-e APP_VERSION` and `-e GIT_COMMIT` passed through from CI
  - Traefik labels:
    - `traefik.enable=true`
    - `traefik.http.routers.crystalpine-lab.entrypoints=websecure`
    - `traefik.http.routers.crystalpine-lab.rule=Host("lab.crystalpine.dev")`
    - `traefik.http.routers.crystalpine-lab.tls.certresolver=letsencrypt`
    - `traefik.http.services.crystalpine-lab.loadbalancer.server.port=8000`

---

## Backend API & dashboard

The backend is a simple FastAPI application:

### `/healthz`

Returns a minimal JSON health check:

```json
{
  "version": "0.1.0",
  "commit": "<commit-sha>",
  "env": "prod"
}
```
```json
{
  "status": "ok",
  "version": "0.1.0",
  "commit": "<commit-sha>",
  "env": "prod",
  "hostname": "<server-hostname>",
  "timestamp": "<ISO-8601-UTC>"
}
```