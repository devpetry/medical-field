"""Configuração por variáveis de ambiente (lê .env do diretório do serviço, se existir)."""
import os
from pathlib import Path

_ENV = Path(__file__).resolve().parent.parent / ".env"
if _ENV.exists():
    for linha in _ENV.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _obrigatoria(nome: str) -> str:
    v = os.environ.get(nome)
    if not v:
        raise RuntimeError(f"Variável de ambiente {nome} não definida")
    return v


JWT_SECRET = _obrigatoria("JWT_SECRET")
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET deve ter pelo menos 32 caracteres")
DB_URL = _obrigatoria("DB_URL")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
CLINICAL_URL = os.environ.get("CLINICAL_URL", "http://127.0.0.1:8080").rstrip("/")
EMAIL_ADAPTER = os.environ.get("EMAIL_ADAPTER", "smtp")
EMAIL_DIR = os.environ.get("EMAIL_DIR", "./emails")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "MedicalField <nao-responda@medicalfield.local>")
