from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os
import socket
import datetime

app = FastAPI(title="CrystalPine DevOps Lab API")


class Version(BaseModel):
    version: str
    commit: Optional[str] = None
    env: str = "local"


class Status(BaseModel):
    status: str
    version: str
    commit: Optional[str]
    env: str
    hostname: str
    timestamp: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/version", response_model=Version)
def version():
    return Version(
        version=os.getenv("APP_VERSION", "0.1.0"),
        commit=os.getenv("GIT_COMMIT"),
        env=os.getenv("APP_ENV", "local"),
    )


@app.get("/status", response_model=Status)
def status():
    """
    Aggregated status endpoint for the lab dashboard.
    """
    ver = version()
    return Status(
        status="ok",
        version=ver.version,
        commit=ver.commit,
        env=ver.env,
        hostname=socket.gethostname(),
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
    )


@app.get("/", response_class=HTMLResponse)
def root():
    # Очень простой HTML+JS дашборд, который дергает /status
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>CrystalPine DevOps Lab</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #0f172a;
          color: #e5e7eb;
          margin: 0;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
        }
        .card {
          background: #020617;
          border-radius: 16px;
          padding: 24px 28px;
          max-width: 480px;
          width: 100%;
          box-shadow: 0 20px 40px rgba(0,0,0,0.6);
          border: 1px solid #1e293b;
        }
        h1 {
          margin: 0 0 8px;
          font-size: 24px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .subtitle {
          margin: 0 0 16px;
          font-size: 14px;
          color: #9ca3af;
        }
        .status-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
        }
        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #22c55e;
          box-shadow: 0 0 8px rgba(34,197,94,0.8);
        }
        .status-badge {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 999px;
          background: #022c22;
          color: #6ee7b7;
          border: 1px solid #059669;
        }
        dl {
          margin: 0 0 16px;
          font-size: 13px;
        }
        dt {
          color: #9ca3af;
        }
        dd {
          margin: 0 0 8px;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
          color: #e5e7eb;
        }
        .controls {
          display: flex;
          justify-content: flex-end;
          gap: 8px;
        }
        button {
          background: #1d4ed8;
          color: white;
          border: none;
          border-radius: 999px;
          padding: 6px 14px;
          font-size: 13px;
          cursor: pointer;
        }
        button:hover {
          background: #2563eb;
        }
        .error {
          color: #f97373;
          font-size: 12px;
          margin-top: 8px;
        }
      </style>
    </head>
    <body>
      <div class="card">
        <h1>
          <span>CrystalPine DevOps Lab</span>
        </h1>
        <p class="subtitle">Self-hosted CI/CD demo on AlwaysFree server</p>

        <div class="status-row">
          <div id="status-dot" class="status-dot"></div>
          <span id="status-text" class="status-badge">Loading...</span>
        </div>

        <dl>
          <dt>Version</dt>
          <dd id="field-version">—</dd>

          <dt>Commit</dt>
          <dd id="field-commit">—</dd>

          <dt>Environment</dt>
          <dd id="field-env">—</dd>

          <dt>Hostname</dt>
          <dd id="field-hostname">—</dd>

          <dt>Timestamp (UTC)</dt>
          <dd id="field-timestamp">—</dd>
        </dl>

        <div class="controls">
          <button id="refresh-btn">Refresh</button>
        </div>
        <div id="error" class="error"></div>
      </div>

      <script>
        async function loadStatus() {
          const statusText = document.getElementById('status-text');
          const dot = document.getElementById('status-dot');
          const errorEl = document.getElementById('error');

          statusText.textContent = 'Loading...';
          errorEl.textContent = '';

          try {
            const res = await fetch('/status');
            if (!res.ok) {
              throw new Error('HTTP ' + res.status);
            }
            const data = await res.json();

            // Status
            if (data.status === 'ok') {
              dot.style.background = '#22c55e';
              dot.style.boxShadow = '0 0 8px rgba(34,197,94,0.8)';
              statusText.textContent = 'Healthy';
            } else {
              dot.style.background = '#ef4444';
              dot.style.boxShadow = '0 0 8px rgba(239,68,68,0.8)';
              statusText.textContent = 'Degraded';
            }

            document.getElementById('field-version').textContent = data.version || '—';
            document.getElementById('field-commit').textContent = data.commit || '—';
            document.getElementById('field-env').textContent = data.env || '—';
            document.getElementById('field-hostname').textContent = data.hostname || '—';
            document.getElementById('field-timestamp').textContent = data.timestamp || '—';
          } catch (err) {
            dot.style.background = '#f97316';
            dot.style.boxShadow = '0 0 8px rgba(249,115,22,0.8)';
            statusText.textContent = 'Unknown';
            errorEl.textContent = 'Failed to load status: ' + err.message;
          }
        }

        document.getElementById('refresh-btn').addEventListener('click', loadStatus);

        // Auto-load on page open
        loadStatus();
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
