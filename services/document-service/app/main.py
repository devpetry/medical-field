"""document-service: Ficha de Atendimento em PDF e envio por e-mail."""
import time
from uuid import UUID
from datetime import datetime, timezone
from typing import Literal

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from . import config, db
from .email_sender import criar_sender, montar_mensagem
from .pdf import gerar_ficha

app = FastAPI(title="document-service", docs_url=None, redoc_url=None, openapi_url=None)
sender = criar_sender()


@app.on_event("startup")
def _startup() -> None:
    db.migrar()


def _ip(req: Request) -> str | None:
    xff = req.headers.get("x-forwarded-for")
    return xff.split(",")[0].strip() if xff else (req.client.host if req.client else None)


@app.middleware("http")
async def seguranca_e_auditoria(req: Request, call_next):
    """Valida o JWT (todas as rotas são autenticadas) e grava o log de acesso."""
    inicio = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    prof = None
    auth = req.headers.get("authorization", "")
    try:
        if not auth.startswith("Bearer "):
            raise jwt.InvalidTokenError()
        claims = jwt.decode(auth[7:], config.JWT_SECRET, algorithms=["HS256"])
        prof = int(claims["sub"])
        req.state.claims = claims
        resp = await call_next(req)
    except jwt.InvalidTokenError:
        resp = JSONResponse({"erro": "Token ausente, inválido ou expirado"}, status_code=401)
    ms = int((time.perf_counter() - t0) * 1000)
    ip = _ip(req)
    print(f"{req.method} {req.url.path} {resp.status_code} {ms}ms prof={prof or '-'} ip={ip}", flush=True)
    try:
        with db.conectar() as c:
            c.execute("""INSERT INTO audit.access_log (data_hora, servico, ip_cliente, profissional_id, metodo, rota,
                         status_code, tempo_ms, origem, device_id) VALUES (%s, 'document', %s, %s, %s, %s, %s, %s, 'ONLINE', %s)""",
                      (inicio, ip, prof, req.method, req.url.path, resp.status_code, ms, req.headers.get("x-device-id")))
    except Exception as e:  # o log não pode derrubar a requisição
        print(f"falha ao gravar access_log: {e}", flush=True)
    return resp


def _buscar_atendimento(req: Request, atendimento_id: str) -> dict:
    """Busca o atendimento completo no clinical-service repassando o token do usuário."""
    try:
        r = httpx.get(f"{config.CLINICAL_URL}/atendimento/detalhe/{atendimento_id}",
                      headers={"Authorization": req.headers["authorization"],
                               "X-Forwarded-For": _ip(req) or ""}, timeout=10)
    except httpx.HTTPError:
        raise HTTPException(502, "clinical-service indisponível")
    if r.status_code == 404:
        raise HTTPException(404, "Atendimento não encontrado")
    if r.status_code != 200:
        raise HTTPException(502, f"clinical-service respondeu {r.status_code}")
    return r.json()


def _emitente(req: Request) -> str:
    c = req.state.claims
    return f"{c.get('nome', 'profissional')} ({c.get('registro', '')})"


@app.exception_handler(HTTPException)
async def _erro(_req: Request, e: HTTPException):
    return JSONResponse({"erro": e.detail}, status_code=e.status_code)


@app.get("/documento/ficha/{atendimento_id}")
def ficha_pdf(atendimento_id: UUID, req: Request):
    atendimento_id = str(atendimento_id)
    dados = _buscar_atendimento(req, atendimento_id)
    pdf = gerar_ficha(dados, _emitente(req))
    nome = f"ficha_atendimento_{atendimento_id[:8]}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{nome}"'})


class EnvioEmail(BaseModel):
    destinatario: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nomeDestinatario: str | None = None
    relacao: Literal["PACIENTE", "FAMILIAR"]


@app.post("/documento/ficha/{atendimento_id}/email", status_code=202)
def ficha_email(atendimento_id: UUID, corpo: EnvioEmail, req: Request):
    atendimento_id = str(atendimento_id)
    dados = _buscar_atendimento(req, atendimento_id)
    pdf = gerar_ficha(dados, _emitente(req))
    paciente = dados["pessoa"]["nome"]
    saudacao = f"Olá, {corpo.nomeDestinatario}." if corpo.nomeDestinatario else "Olá."
    msg = montar_mensagem(
        corpo.destinatario, corpo.nomeDestinatario, f"Ficha de Atendimento — {paciente}",
        f"{saudacao}\n\nSegue em anexo a Ficha de Atendimento de {paciente}, registrada pela equipe de "
        f"atendimento pré-hospitalar.\n\nMensagem automática do MedicalField.",
        pdf, f"ficha_atendimento_{atendimento_id[:8]}.pdf")
    status, erro = "ENVIADO", None
    try:
        sender.enviar(msg)
    except Exception as e:
        status, erro = "ERRO", str(e)
    with db.conectar() as c:
        envio_id = c.execute("""INSERT INTO document.envio_email (atendimento_id, destinatario, nome_destinatario, relacao,
                                status, erro, profissional_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                             (atendimento_id, corpo.destinatario, corpo.nomeDestinatario, corpo.relacao, status, erro,
                              int(req.state.claims["sub"]))).fetchone()[0]
    if status == "ERRO":
        raise HTTPException(502, f"Falha no envio do e-mail: {erro}")
    return {"envioId": envio_id, "status": status}


@app.get("/documento/envio")
def envios(req: Request):
    if req.state.claims.get("perfil") != "ADMIN":
        raise HTTPException(403, "Acesso restrito a administradores")
    with db.conectar() as c:
        cur = c.execute("""SELECT id, atendimento_id, destinatario, nome_destinatario, relacao, status, erro,
                           enviado_em, profissional_id FROM document.envio_email ORDER BY enviado_em DESC LIMIT 200""")
        cols = ["id", "atendimentoId", "destinatario", "nomeDestinatario", "relacao", "status", "erro", "enviadoEm",
                "profissionalId"]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
