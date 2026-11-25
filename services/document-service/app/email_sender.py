"""Adapter: o serviço conhece só a interface EmailSender; SMTP ou arquivo .eml por baixo."""
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol

from . import config


class EmailSender(Protocol):
    def enviar(self, msg: EmailMessage) -> None: ...


class SmtpEmailAdapter:
    def enviar(self, msg: EmailMessage) -> None:
        if config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=ssl.create_default_context(), timeout=20) as s:
                self._login_e_envio(s, msg)
        else:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
                s.starttls(context=ssl.create_default_context())
                self._login_e_envio(s, msg)

    @staticmethod
    def _login_e_envio(s: smtplib.SMTP, msg: EmailMessage) -> None:
        if config.SMTP_USER:
            s.login(config.SMTP_USER, config.SMTP_PASSWORD)
        s.send_message(msg)


class FileEmailAdapter:
    """Grava o e-mail como .eml (testes sem servidor SMTP)."""

    def enviar(self, msg: EmailMessage) -> None:
        pasta = Path(config.EMAIL_DIR)
        pasta.mkdir(parents=True, exist_ok=True)
        nome = datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".eml"
        (pasta / nome).write_bytes(bytes(msg))


def criar_sender() -> EmailSender:
    return FileEmailAdapter() if config.EMAIL_ADAPTER == "file" else SmtpEmailAdapter()


def montar_mensagem(destinatario: str, nome: str | None, assunto: str, corpo: str, pdf: bytes,
                    arquivo: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = f"{nome} <{destinatario}>" if nome else destinatario
    msg["Subject"] = assunto
    msg.set_content(corpo)
    msg.add_attachment(pdf, maintype="application", subtype="pdf", filename=arquivo)
    return msg
