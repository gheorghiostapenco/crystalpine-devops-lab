from fastapi import FastAPI
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


@app.get("/")
def root():
    return {"message": "CrystalPine DevOps Lab backend is up - CI/CD test 1"}
