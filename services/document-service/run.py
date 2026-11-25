"""Ponto de entrada: python run.py (usa PORT e BIND_ADDRESS)."""
import os

import uvicorn

from app import config  # noqa: F401  carrega .env antes de iniciar

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=os.environ.get("BIND_ADDRESS", "127.0.0.1"),
                port=int(os.environ.get("PORT", "8000")), proxy_headers=False)
