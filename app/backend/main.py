from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="CrystalPine DevOps Lab API")


class Version(BaseModel):
    version: str
    commit: Optional[str] = None
    env: str = "local"


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


@app.get("/")
def root():
    return {"message": "CrystalPine DevOps Lab backend is up"}
