from pathlib import Path

import psycopg

from . import config


def conectar() -> psycopg.Connection:
    return psycopg.connect(config.DB_URL, user=config.DB_USER, password=config.DB_PASSWORD, autocommit=True)


def migrar() -> None:
    """Aplica em ordem os arquivos de migrations/ ainda não executados."""
    pasta = Path(__file__).resolve().parent.parent / "migrations"
    with conectar() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS document.schema_migrations (
            arquivo VARCHAR(100) PRIMARY KEY, aplicado_em TIMESTAMPTZ NOT NULL DEFAULT now())""")
        feitos = {r[0] for r in c.execute("SELECT arquivo FROM document.schema_migrations")}
        for arq in sorted(pasta.glob("*.sql")):
            if arq.name in feitos:
                continue
            with c.transaction():
                c.execute(arq.read_text(encoding="utf-8"))
                c.execute("INSERT INTO document.schema_migrations (arquivo) VALUES (%s)", (arq.name,))
            print(f"migração aplicada: {arq.name}", flush=True)
