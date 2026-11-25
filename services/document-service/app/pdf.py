"""Geração da Ficha de Atendimento em PDF (ReportLab)."""
import io
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TZ = ZoneInfo("America/Sao_Paulo")
AZUL = colors.HexColor("#1D4ED8")
CINZA = colors.HexColor("#64748B")
CORES_TRIAGEM = {"VERMELHO": "#DC2626", "LARANJA": "#EA580C", "AMARELO": "#CA8A04", "VERDE": "#16A34A",
                 "AZUL": "#2563EB", "PRETO": "#111827"}


def _dt(v: str | None, so_hora=False) -> str:
    if not v:
        return "—"
    d = datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(TZ)
    return d.strftime("%H:%M") if so_hora else d.strftime("%d/%m/%Y %H:%M")


def _txt(v) -> str:
    return "—" if v in (None, "") else str(v)


def _num(v) -> str:
    if v is None:
        return "—"
    f = float(v)
    return (f"{f:.0f}" if f.is_integer() else f"{f:.1f}").replace(".", ",")


def gerar_ficha(dados: dict, emitido_por: str) -> bytes:
    a, p, pr = dados["atendimento"], dados["pessoa"], dados["prontuario"]
    meds = {m["id"]: m for m in dados.get("medicamentos", [])}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title="Ficha de Atendimento", author="MedicalField")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], alignment=0, fontSize=20, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=AZUL, fontSize=13, spaceBefore=10, spaceAfter=4)
    pq = ParagraphStyle("pq", parent=ss["Normal"], textColor=CINZA, fontSize=9)
    nor = ss["Normal"]

    def grade(linhas, larguras, cabecalho=False):
        t = Table(linhas, colWidths=larguras)
        estilo = [("FONTSIZE", (0, 0), (-1, -1), 9.5), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0"))]
        if cabecalho:
            estilo += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
                       ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
        else:
            estilo += [("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold")]
        t.setStyle(TableStyle(estilo))
        return t

    w = doc.width
    el = [Paragraph("Ficha de Atendimento", h1),
          Paragraph(f"MedicalField · atendimento {a['id']}", pq), Spacer(1, 6)]

    el += [Paragraph("Paciente", h2), grade([
        ["Nome", _txt(p.get("nome")), "Nascimento", _txt(p.get("dataNascimento"))],
        ["CPF", _txt(p.get("cpf")), "Tipo sanguíneo", _txt(p.get("tipoSanguineo"))],
        ["Alergias", _txt(p.get("alergias")), "Contato", _txt(p.get("contatoEmergencia") or p.get("telefone"))],
        ["Comorbidades", _txt(pr.get("comorbidades")), "Uso contínuo", _txt(pr.get("usoContinuo"))],
    ], [w * 0.17, w * 0.33, w * 0.17, w * 0.33])]

    g = a.get("glasgow") or {}
    tri_m, tri_s = a.get("triagemManchester"), a.get("triagemStart")

    def tri(v):
        return f'<font color="{CORES_TRIAGEM.get(v or "", "#111827")}"><b>{_txt(v).capitalize()}</b></font>'

    el += [Paragraph("Atendimento", h2), grade([
        ["Início", _dt(a.get("inicio")), "Fim", _dt(a.get("fim"))],
        ["Local", _txt(a.get("local")), "Origem", "criado offline" if a.get("criadoOffline") else "online"],
        ["Queixa", Paragraph(_txt(a.get("queixaPrincipal")), nor), "Profissional", f"ID {_txt(a.get('profissionalId'))}"],
        ["Glasgow", f"{_txt(g.get('total'))} (O{_txt(g.get('ocular'))} V{_txt(g.get('verbal'))} M{_txt(g.get('motora'))})",
         "Triagem", Paragraph(f"Manchester {tri(tri_m)} · START {tri(tri_s)}", nor)],
        ["Conduta", Paragraph(_txt(a.get("conduta")), nor), "Destino", _txt(a.get("destino"))],
    ], [w * 0.17, w * 0.33, w * 0.17, w * 0.33])]

    sv = a.get("sinaisVitais") or []
    el.append(Paragraph("Sinais vitais", h2))
    if sv:
        linhas = [["Hora", "PA (mmHg)", "FC", "FR", "SpO2 (%)", "Temp. (°C)", "Glicemia"]]
        for s in sv:
            pa = f"{_txt(s.get('paSistolica'))}/{_txt(s.get('paDiastolica'))}" if s.get("paSistolica") else "—"
            linhas.append([_dt(s.get("aferidoEm"), True), pa, _num(s.get("fc")), _num(s.get("fr")),
                           _num(s.get("spo2")), _num(s.get("temperatura")), _num(s.get("glicemia"))])
        el.append(grade(linhas, [w / 7] * 7, cabecalho=True))
    else:
        el.append(Paragraph("Nenhuma aferição registrada.", pq))

    md = a.get("medicacoes") or []
    el.append(Paragraph("Medicações administradas", h2))
    if md:
        linhas = [["Hora", "Medicamento", "Dose", "Via", "Alerta confirmado"]]
        for m in md:
            nome = meds.get(m.get("medicamentoId"), {}).get("nome", f"#{m.get('medicamentoId')}")
            linhas.append([_dt(m.get("administradoEm"), True), nome, f"{_num(m.get('dose'))} {_txt(m.get('unidade'))}",
                           _txt(m.get("via")), "sim" if m.get("alertaConfirmado") else "—"])
        el.append(grade(linhas, [w * 0.12, w * 0.4, w * 0.18, w * 0.1, w * 0.2], cabecalho=True))
    else:
        el.append(Paragraph("Nenhuma medicação registrada.", pq))

    agora = datetime.now(timezone.utc).astimezone(TZ).strftime("%d/%m/%Y %H:%M")
    el += [Spacer(1, 14), Paragraph(f"Documento gerado em {agora} por {emitido_por}.", pq)]
    doc.build(el)
    return buf.getvalue()
