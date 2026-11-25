"""As nove cenas do vídeo. Cada cena recebe o tempo local `t` (s) e `S`,
com os inícios (`S.c`) e fins (`S.e`) de cada frase da narração."""
import math

from draw import *  # noqa: F401,F403


# ================================================================ utilidades
def win(ctx, x, y, w, h, title, alpha=1.0, status=None, accent=CYAN):
    """Janela de aplicativo com barra de título e, opcionalmente, indicador de rede."""
    if alpha <= 0.001:
        return
    rrect(ctx, x, y, w, h, 16)
    ctx.set_source_rgba(0.05, 0.1, 0.2, 0.96 * alpha)
    ctx.fill_preserve()
    rgba(ctx, accent, 0.55 * alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.save()
    rrect(ctx, x, y, w, h, 16)
    ctx.clip()
    ctx.rectangle(x, y, w, 52)
    ctx.set_source_rgba(1, 1, 1, 0.06 * alpha)
    ctx.fill()
    ctx.restore()
    for i, c in enumerate((RED, AMBER, GREEN)):
        ctx.arc(x + 26 + i * 22, y + 26, 7, 0, 2 * math.pi)
        rgba(ctx, c, 0.8 * alpha)
        ctx.fill()
    text(ctx, title, x + 104, y + 26, 20, MUTED, alpha=alpha, middle=True)
    if status is not None:
        status_pill(ctx, x + w - 110, y + 26, status, alpha)


def status_pill(ctx, cx, cy, online_u, alpha=1.0, size=20):
    """online_u: 1 = ONLINE (verde), 0 = OFFLINE (vermelho)."""
    c = mix(RED, GREEN, online_u)
    label = "ONLINE" if online_u >= 0.5 else "OFFLINE"
    w = 150 * size / 20
    h = size * 1.7
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
    rgba(ctx, c, 0.16 * alpha)
    ctx.fill_preserve()
    rgba(ctx, c, alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.arc(cx - w / 2 + h * 0.55, cy, size * 0.28, 0, 2 * math.pi)
    rgba(ctx, c, alpha)
    ctx.fill()
    text(ctx, label, cx + h * 0.25, cy, size * 0.9, c, bold=True, align="center", alpha=alpha,
         middle=True)


def field(ctx, x, y, w, label, value, u=1.0, alpha=1.0, active=False, mono=False, h=54):
    if alpha <= 0.001:
        return
    text(ctx, label, x, y - 10, 18, MUTED, alpha=alpha)
    rrect(ctx, x, y, w, h, 10)
    ctx.set_source_rgba(1, 1, 1, 0.05 * alpha)
    ctx.fill_preserve()
    rgba(ctx, CYAN if active else DIM, alpha * (1 if active else 0.8))
    ctx.set_line_width(2 if active else 1.5)
    ctx.stroke()
    s = typed(value, u)
    wv = text(ctx, s, x + 16, y + h / 2, 23, WHITE, alpha=alpha, middle=True, mono=mono)
    if active and 0 < u < 1:
        ctx.rectangle(x + 18 + wv, y + 14, 2, h - 28)
        rgba(ctx, CYAN, alpha)
        ctx.fill()


def button(ctx, cx, cy, label, alpha=1.0, pressed=0.0, color=CYAN, w=None, size=22):
    if alpha <= 0.001:
        return
    w = w or text_w(ctx, label, size, True) + 60
    h = size * 2.3
    s = 1 - 0.06 * pressed
    with layer(ctx, 1.0, s, cx, cy):
        rrect(ctx, cx - w / 2, cy - h / 2, w, h, 12)
        rgba(ctx, mix(color, WHITE, 0.25 * pressed), alpha)
        ctx.fill()
        text(ctx, label, cx, cy, size, hexc("06101F"), bold=True, align="center", alpha=alpha,
             middle=True)
    if pressed > 0:
        ctx.arc(cx, cy, 30 + 60 * pressed, 0, 2 * math.pi)
        rgba(ctx, WHITE, 0.25 * (1 - pressed) * alpha)
        ctx.set_line_width(3)
        ctx.stroke()


def press(t, t0, d=0.5):
    """Pulso de clique: 0 → 1 → 0."""
    u = clamp((t - t0) / d)
    return math.sin(u * math.pi) if 0 < u < 1 else 0.0


def table(ctx, x, y, cols, header, rows, row_alpha=None, size=21, row_h=50, alpha=1.0,
          hl_col=None, hl_row=None, hl_u=0.0, mono_cols=()):
    """cols = larguras. Desenha cabeçalho + linhas; row_alpha controla a entrada de cada linha."""
    if alpha <= 0.001:
        return
    total = sum(cols)
    rrect(ctx, x, y, total, row_h, 10)
    ctx.set_source_rgba(1, 1, 1, 0.07 * alpha)
    ctx.fill()
    cx = x
    for i, (cw, hd) in enumerate(zip(cols, header)):
        hl = hl_u if hl_col == i else 0
        if hl > 0:
            rrect(ctx, cx + 4, y + 4, cw - 8, row_h - 8, 8)
            rgba(ctx, CYAN, 0.25 * hl * alpha)
            ctx.fill()
        text(ctx, hd, cx + 16, y + row_h / 2, size - 2, mix(MUTED, CYAN, hl), bold=True,
             alpha=alpha, middle=True, mono=True)
        cx += cw
    for r, row in enumerate(rows):
        ra = (row_alpha[r] if row_alpha else 1.0) * alpha
        if ra <= 0.001:
            continue
        ry = y + row_h * (r + 1) + (1 - ra) * 16
        if hl_row == r and hl_u > 0:
            rrect(ctx, x, ry + 3, total, row_h - 6, 8)
            rgba(ctx, CYAN, 0.16 * hl_u * ra)
            ctx.fill()
        ctx.move_to(x, ry + row_h)
        ctx.line_to(x + total, ry + row_h)
        ctx.set_source_rgba(1, 1, 1, 0.07 * ra)
        ctx.set_line_width(1)
        ctx.stroke()
        cx = x
        for i, (cw, cell) in enumerate(zip(cols, row)):
            col = WHITE
            if isinstance(cell, tuple):
                cell, col = cell
            text(ctx, cell, cx + 16, ry + row_h / 2, size, col, alpha=ra, middle=True,
                 mono=i in mono_cols)
            cx += cw


def chip_fly(ctx, a, b, u, label, color=CYAN, size=19, arc=-80):
    """Etiqueta voando de a para b com leve curva."""
    if u <= 0 or u >= 1:
        return
    e = ease_in_out(u)
    x = lerp(a[0], b[0], e)
    y = lerp(a[1], b[1], e) + arc * math.sin(math.pi * e)
    al = min(1, u * 6, (1 - u) * 6)
    glow(ctx, x, y, 50, color, 0.3 * al)
    pill(ctx, x, y, label, color, size=size, filled=True, alpha=al)


def svc_icon(color):
    def f(ctx, cx, cy):
        icon_server(ctx, cx, cy, 64, 60, color)
    return f


# ================================================================ cena 1
def scene1(ctx, t, S):
    c, e = S.c, S.e
    # --- ambulância na estrada (frases 0–1)
    a_road = 1 - prog(t, c[2] - 0.2, 0.7)
    if a_road > 0:
        with layer(ctx, a_road * prog(t, 0, 0.8), 1.0, 960, 540, dy=40 * (1 - a_road)):
            ctx.rectangle(0, 735, W, 120)
            ctx.set_source_rgba(1, 1, 1, 0.04)
            ctx.fill()
            off = (t * 520) % 160
            for k in range(-1, 14):
                ctx.rectangle(k * 160 - off, 792, 80, 6)
                ctx.set_source_rgba(1, 1, 1, 0.25)
                ctx.fill()
            bob = 3 * math.sin(t * 11)
            icon_ambulance(ctx, 960, 650 + bob, 440, t)
            ecg(ctx, 260, 300, 1400, 90, t, GREEN, 0.9)
            u1 = prog(t, c[1] + 0.3, 2.6, lambda x: x)
            if t > c[1]:
                lvl = 3 * (1 - u1)
                icon_wifi(ctx, 960, 420, 120, CYAN, lvl, prog(t, c[1] + 2.9, 0.5),
                          prog(t, c[1], 0.5))
                text(ctx, "sem sinal", 1050, 450, 30, RED, bold=True,
                     alpha=prog(t, c[1] + 3.1, 0.5))
    # --- quatro informações clínicas (frase 2) que convergem (frase 3)
    labels = ["Sinais vitais", "Glasgow", "Triagem", "Medicamentos"]
    if c[2] - 0.2 < t < c[4] + 0.6:
        conv = prog(t, c[3], 1.2, ease_in_out)
        out = 1 - prog(t, c[4] - 0.2, 0.6)
        for i in range(4):
            al, sc = appear(t, c[2] + 0.2 + 0.45 * i)
            x0, y0 = 960 + (i - 1.5) * 330, 470
            x = lerp(x0, 960, conv)
            y = lerp(y0, 470, conv)
            al *= (1 - conv * 0.9) * out
            if al <= 0.001:
                continue
            with layer(ctx, al, sc * lerp(1, 0.4, conv), x, y):
                rrect(ctx, x - 130, y - 130, 260, 260, 28)
                ctx.set_source_rgba(1, 1, 1, 0.05)
                ctx.fill_preserve()
                rgba(ctx, CYAN, 0.4)
                ctx.set_line_width(2)
                ctx.stroke()
                if i == 0:
                    icon_heart(ctx, x, y - 30, 90)
                    ecg(ctx, x - 100, y + 50, 200, 26, t, GREEN, 1, speed=180, period=120)
                elif i == 1:
                    icon_gcs(ctx, x, y - 10, 150)
                elif i == 2:
                    icon_triage(ctx, x, y - 10, 170)
                else:
                    icon_pill(ctx, x, y - 10, 140)
                text(ctx, labels[i], x, y + 175, 28, WHITE, bold=True, align="center")
        # prontuário que continua sendo preenchido mesmo sem conexão
        if t > c[3]:
            a = prog(t, c[3] + 0.6, 0.6) * out
            with layer(ctx, a, 1, 960, 470):
                icon_doc(ctx, 960, 470, 220, 290, CYAN, lines_u=prog(t, c[3] + 0.8, 1.2, lambda x: x),
                         badge=None)
                ctx.arc(1095, 330, 62, 0, 2 * math.pi)
                ctx.set_source_rgba(0.06, 0.12, 0.24, 1)
                ctx.fill()
                icon_wifi(ctx, 1095, 322, 80, CYAN, 0, 1)
                icon_check(ctx, 960, 470 + 205, 42, GREEN, prog(t, c[3] + 1.8, 0.7))
    # --- marca (frase 4) e proposta (frase 5)
    if t > c[4] - 0.3:
        a = prog(t, c[4], 0.9)
        up = prog(t, c[5], 1.0, ease_in_out)
        ly = lerp(500, 300, up)
        with layer(ctx, a, lerp(0.92, 1, a) * lerp(1, 0.8, up), 960, ly):
            logo(ctx, 960, ly, 110, t)
            text(ctx, "Prontuário eletrônico de emergência · offline-first", 960, ly + 125, 38,
                 MUTED, align="center", alpha=prog(t, c[4] + 1.0, 0.8) * (1 - up))
    if t > c[5]:
        a = prog(t, c[5] + 0.5, 0.7)
        with layer(ctx, a):
            icon_laptop(ctx, 560, 580, 260)
            text(ctx, "Dispositivo", 560, 720, 26, WHITE, bold=True, align="center")
            icon_db(ctx, 560, 830, 130, 100, SQLITE, sub=None, hl=0.5)
            text(ctx, "SQLite", 560, 836, 22, WHITE, bold=True, align="center", middle=True)
            icon_server(ctx, 1360, 590, 220, 170, PG, t)
            text(ctx, "Servidor central", 1360, 720, 26, WHITE, bold=True, align="center")
            back = prog(t, c[5] + 3.6, 0.6)
            loop_packets(ctx, [(560, 680), (560, 772)], t, c[5] + 0.9, 1.1, SQLITE, r=7)
            pts = [(700, 580), (1240, 580)]
            arrow(ctx, pts, mix(RED, GREEN, back), 1, 3, 0.6, head=False, dash=None if back > 0.5 else [12, 10])
            icon_wifi(ctx, 960, 520, 90, GREEN, 3 * back, 1 - back)
            loop_packets(ctx, pts, t, c[5] + 4.0, 1.0, GREEN, n=3, r=8)


# ================================================================ cena 2
def scene2(ctx, t, S):
    c, e = S.c, S.e
    dev_a = prog(t, c[0] + 0.2, 0.7)
    vm_a = prog(t, c[0] + 0.7, 0.7)
    vm_hl = window(t, c[3], e[3], 0.4)
    final_hl = window(t, c[11], S.T, 0.4)
    panel(ctx, 60, 130, 600, 640, CYAN, dev_a, "Dispositivo da ambulância")
    panel(ctx, 720, 330, 900, 560, BLUE, vm_a * (1 + 0.6 * vm_hl), "VM da Univates",
          fill=0.025 + 0.05 * vm_hl)
    if dev_a > 0:
        icon_ambulance(ctx, 560, 182, 130, t, dev_a * 0.95)

    # cliente desktop + SQLite
    a, s = appear(t, c[1] + 0.3)
    with layer(ctx, a, s, 360, 305):
        card(ctx, 100, 235, 520, 140, CYAN, "Cliente desktop", "Electron · React · TypeScript",
             hl=window(t, c[1], e[1]),
             icon=lambda _c, cx_, cy_: icon_laptop(ctx, cx_, cy_ - 6, 76))
    a2, s2 = appear(t, c[2] + 0.3)
    arrow(ctx, [(360, 378), (360, 470)], SQLITE, prog(t, c[2] + 0.2, 0.5), 3, a2)
    with layer(ctx, a2, s2, 360, 580):
        icon_db(ctx, 360, 570, 210, 160, SQLITE, "SQLite", "banco local embarcado",
                hl=max(window(t, c[2], e[2]), final_hl * (0.6 + 0.4 * math.sin(t * 5))))
    loop_packets(ctx, [(360, 378), (360, 470)], t, c[2] + 0.9, 1.6, SQLITE, a2, r=6)

    # Nginx
    a3, s3 = appear(t, c[4] + 0.2)
    client_path = [(620, 305), (1000, 305), (1000, 370)]
    arrow(ctx, client_path, CYAN, prog(t, c[4] + 0.1, 0.7), 3, 0.9)
    text(ctx, "HTTP + JWT · quando online", 640, 290, 19, MUTED, alpha=a3)
    with layer(ctx, a3, s3, 1170, 410):
        card(ctx, 760, 372, 820, 76, CYAN, "Nginx", None, hl=window(t, c[4], e[4]), title_size=28)
        text(ctx, "API Gateway · porta 80", 900, 412, 21, MUTED, alpha=1, middle=True)
    loop_packets(ctx, client_path, t, c[4] + 1.0, 2.0, CYAN, a3, r=7)

    svcs = [
        (760, NODE, "auth-service", "Node.js · Express", "login · JWT", 5),
        (1050, JAVA, "clinical-service", "Java · Spring Boot", "fichas · sync · logs", 6),
        (1340, PY, "document-service", "Python · FastAPI", "PDF · e-mail", 7),
    ]
    for (x, col, name, tech, role, k) in svcs:
        a4, s4 = appear(t, c[k] + 0.2)
        cxs = x + 120
        arrow(ctx, [(cxs, 450), (cxs, 518)], col, prog(t, c[k], 0.5), 3, a4)
        with layer(ctx, a4, s4, cxs, 595):
            card(ctx, x, 520, 240, 150, col, name, tech, hl=window(t, c[k], e[k]), title_size=22,
                 sub_size=19, top=True)
            text(ctx, role, x + 28, 640, 19, col)
        loop_packets(ctx, [(cxs, 450), (cxs, 518)], t, c[k] + 0.8, 2.6, col, a4, r=6)
    # REST document -> clinical
    a5 = prog(t, c[7] + 1.2, 0.6)
    arrow(ctx, [(1338, 600), (1292, 600)], PY, a5, 3, a5)
    text(ctx, "REST", 1315, 585, 17, MUTED, align="center", alpha=a5)

    # PostgreSQL
    a6, s6 = appear(t, c[8] + 0.2)
    for (x, col, *_r) in svcs:
        arrow(ctx, [(x + 120, 672), (x + 120, 732)], col, prog(t, c[8] + 0.1, 0.5), 3, a6)
        loop_packets(ctx, [(x + 120, 672), (x + 120, 732)], t, c[8] + 0.9 + (x % 7) * 0.1, 2.2, col,
                     a6, r=6)
    with layer(ctx, a6, s6, 1170, 800):
        hl = max(window(t, c[8], e[8]), final_hl * (0.6 + 0.4 * math.sin(t * 5)))
        if hl > 0:
            glow(ctx, 1170, 800, 520, PG, 0.2 * hl)
        rrect(ctx, 760, 735, 820, 130, 18)
        ctx.set_source_rgba(0.06, 0.13, 0.25, 0.95)
        ctx.fill_preserve()
        rgba(ctx, PG, 0.8 + 0.2 * hl)
        ctx.set_line_width(2 + 1.5 * hl)
        ctx.stroke()
        icon_db(ctx, 840, 800, 90, 92, PG)
        text(ctx, "PostgreSQL", 910, 785, 30, WHITE, bold=True)
        text(ctx, "banco central", 910, 822, 20, MUTED)
        for i, sch in enumerate(("auth", "clinical", "audit", "document")):
            pill(ctx, 1200 + i * 98, 800, sch, PG, size=17, filled=False,
                 alpha=prog(t, c[8] + 1.0 + 0.3 * i, 0.4), mono=True)

    # SMTP
    a7, s7 = appear(t, c[9] + 0.2)
    arrow(ctx, [(1582, 595), (1676, 595)], PY, prog(t, c[9] + 0.1, 0.5), 3, a7)
    with layer(ctx, a7, s7, 1780, 595):
        card(ctx, 1680, 520, 200, 150, AMBER, "SMTP", "e-mail", hl=window(t, c[9], e[9]),
             title_size=24, sub_size=19, top=True)
        icon_envelope(ctx, 1830, 635, 50, AMBER)
    loop_packets(ctx, [(1582, 595), (1676, 595)], t, c[9] + 0.8, 2.4, AMBER, a7, r=6)

    # Portal
    a8, s8 = appear(t, c[10] + 0.2)
    arrow(ctx, [(1365, 282), (1365, 370)], CYAN, prog(t, c[10] + 0.2, 0.5), 3, a8)
    with layer(ctx, a8, s8, 1365, 215):
        card(ctx, 1130, 150, 470, 130, CYAN, "Portal administrativo", "React · Vite · TypeScript",
             hl=window(t, c[10], e[10]), title_size=26,
             icon=lambda _c, cx_, cy_: icon_browser(ctx, cx_, cy_, 70))
    loop_packets(ctx, [(1365, 282), (1365, 370)], t, c[10] + 0.9, 2.2, CYAN, a8, r=6)

    # resumo final
    if final_hl > 0:
        pill(ctx, 360, 720, "cliente", SQLITE, size=22, alpha=final_hl)
        pill(ctx, 1170, 900, "servidor", PG, size=22, alpha=final_hl)


# ================================================================ cena 3
def scene3(ctx, t, S):
    c, e = S.c, S.e
    pA = window(t, 0, c[4] - 0.3)
    pB = window(t, c[4], c[6] - 0.3)
    pC = window(t, c[6], c[7] - 0.3)
    pD = window(t, c[7], S.T + 5)

    # ---------- fase A: login online
    if pA > 0:
        with layer(ctx, pA):
            wa, ws = appear(t, c[0] + 0.2)
            with layer(ctx, wa, ws, 460, 420):
                win(ctx, 140, 190, 640, 460, "MedicalField · Cliente")
                text(ctx, "Entrar", 180, 290, 36, WHITE, bold=True)
                opts = ["CRM", "COREN", "ID Socorrista"]
                cyc = 0
                if t > c[1]:
                    k = int((t - c[1]) / 1.1)
                    cyc = [0, 1, 2, 0][min(k, 3)]
                x = 200
                for i, o in enumerate(opts):
                    wpx = text_w(ctx, o, 20, True) + 36
                    pill(ctx, x + wpx / 2, 340, o, CYAN, 20, filled=(i == cyc), alpha=1)
                    x += wpx + 14
                field(ctx, 180, 400, 560, "Registro", "CRM-RS 12345",
                      prog(t, c[1] + 1.0, 1.8, lambda x: x), active=c[1] + 1 < t < c[1] + 3)
                field(ctx, 180, 495, 560, "Senha", "••••••••",
                      prog(t, c[1] + 3.2, 0.9, lambda x: x), active=c[1] + 3.2 < t < c[1] + 4.3)
                button(ctx, 460, 600, "Entrar", w=560, pressed=press(t, c[2] - 0.1))
            # auth-service
            aa, sa = appear(t, c[0] + 0.6)
            with layer(ctx, aa, sa, 1290, 325):
                card(ctx, 1120, 250, 360, 150, NODE, "auth-service", "Node.js · bcrypt · JWT",
                     icon=svc_icon(NODE), title_size=26, hl=window(t, c[2], e[2]))
            req = [(740, 600), (950, 600), (950, 325), (1118, 325)]
            u = prog(t, c[2] + 0.2, 1.4, lambda x: x)
            packet(ctx, req, u, CYAN, "POST /auth/login", label_dy=-34)
            icon_check(ctx, 1520, 325, 22, GREEN, prog(t, c[2] + 1.6, 0.5))
            text(ctx, "senha conferida", 1552, 325, 21, GREEN, bold=True, middle=True,
                 alpha=prog(t, c[2] + 1.6, 0.5))
            # token volta
            back = [(1118, 360), (960, 360), (960, 640), (782, 640)]
            ub = prog(t, c[2] + 2.3, 1.4, ease_in_out)
            if 0 < ub < 1:
                (bx, by), _ = path_at(back, ub)
                icon_jwt(ctx, bx, by, 110)
            ta, ts = appear(t, c[2] + 2.6)
            with layer(ctx, ta, ts, 1300, 540):
                rrect(ctx, 1120, 455, 560, 170, 18)
                ctx.set_source_rgba(0.06, 0.12, 0.24, 0.95)
                ctx.fill_preserve()
                rgba(ctx, PURPLE, 0.8)
                ctx.set_line_width(2)
                ctx.stroke()
                icon_jwt(ctx, 1210, 540, 120)
                font(ctx, 22, mono=True)
                x0 = 1290
                for part, col in (("eyJhbGci", RED), (".eyJzdWIi", PURPLE), (".SflKxw", CYAN)):
                    x0 += text(ctx, part, x0, 520, 22, col, mono=True)
                text(ctx, "válido por 12 h · um plantão", 1290, 565, 22, WHITE)
            # gravação local
            da, ds = appear(t, c[3])
            with layer(ctx, da, ds, 460, 800):
                icon_db(ctx, 330, 800, 150, 120, SQLITE, "SQLite", hl=window(t, c[3], e[3]))
                text(ctx, "tabela sessao", 430, 770, 20, MUTED, mono=True)
                icon_check(ctx, 450, 812, 13, GREEN, prog(t, c[3] + 1.4, 0.4))
                text(ctx, "token", 472, 819, 21, WHITE, alpha=prog(t, c[3] + 1.4, 0.4))
                icon_check(ctx, 570, 812, 13, GREEN, prog(t, c[3] + 1.9, 0.4))
                text(ctx, "hash da senha", 592, 819, 21, WHITE, alpha=prog(t, c[3] + 1.9, 0.4))
            chip_fly(ctx, (460, 650), (340, 760), prog(t, c[3] + 0.3, 1.1, lambda x: x), "JWT",
                     PURPLE, arc=-40)
            chip_fly(ctx, (560, 650), (360, 760), prog(t, c[3] + 0.8, 1.1, lambda x: x), "hash",
                     SQLITE, arc=-40)

    # ---------- fase B: outros serviços validam o token
    if pB > 0:
        with layer(ctx, pB):
            icon_laptop(ctx, 330, 470, 260)
            text(ctx, "Cliente", 330, 610, 26, WHITE, bold=True, align="center")
            icon_jwt(ctx, 330, 460, 120)
            with layer(ctx, 0.45):
                card(ctx, 620, 150, 340, 120, NODE, "auth-service", "não é consultado",
                     icon=svc_icon(NODE), title_size=24)
            targets = [(1180, 250, JAVA, "clinical-service"), (1180, 560, PY, "document-service")]
            for i, (x, y, col, name) in enumerate(targets):
                card(ctx, x, y, 420, 140, col, name, "valida a assinatura do JWT",
                     icon=lambda _c, cx_, cy_: icon_lock(ctx, cx_, cy_, 60, col), title_size=26)
                path = [(470, 470), (900, 470), (900, y + 70), (x - 4, y + 70)]
                u = prog(t, c[4] + 0.6 + i * 0.9, 1.6, lambda x: x)
                if 0 < u < 1:
                    (px, py), _ = path_at(path, ease_in_out(u))
                    glow(ctx, px, py, 60, PURPLE, 0.4)
                    icon_jwt(ctx, px, py, 80)
                icon_check(ctx, x + 380, y + 30, 22, GREEN, prog(t, c[4] + 2.3 + i * 0.9, 0.5))
            # 401
            if t > c[5]:
                bad = [(160, 860), (900, 860), (900, 320), (1176, 320)]
                u = prog(t, c[5] + 0.2, 1.6, lambda x: x)
                packet(ctx, bad, ease_in_out(u), RED, "sem token", label_dy=-32)
                st = prog(t, c[5] + 1.8, 0.4, back_out)
                if st > 0:
                    with layer(ctx, clamp(st), lerp(1.6, 1, clamp(st)), 1390, 450):
                        rrect(ctx, 1270, 400, 240, 100, 16)
                        rgba(ctx, RED, 0.18)
                        ctx.fill_preserve()
                        rgba(ctx, RED, 1)
                        ctx.set_line_width(4)
                        ctx.stroke()
                        text(ctx, "401", 1390, 442, 46, RED, bold=True, align="center", middle=True)
                        text(ctx, "acesso negado", 1390, 482, 20, RED, align="center")

    # ---------- fase C: login local offline
    if pC > 0:
        with layer(ctx, pC):
            d = S.e[6] - c[6]
            on = prog(t, c[6] + d * 0.72, 0.6)
            win(ctx, 300, 180, 640, 420, "MedicalField · Cliente", status=on)
            text(ctx, "Entrar", 340, 280, 34, WHITE, bold=True)
            field(ctx, 340, 340, 560, "Registro", "CRM-RS 12345", 1)
            field(ctx, 340, 435, 560, "Senha", "••••••••", 1)
            button(ctx, 620, 540, "Entrar", w=560, pressed=press(t, c[6] + 1.0))
            icon_wifi(ctx, 1160, 260, 120, GREEN, 3 * on, 1 - on)
            icon_db(ctx, 1220, 640, 200, 160, SQLITE, "SQLite", "hash guardado na sessao",
                    hl=window(t, c[6] + 1.2, c[6] + d * 0.7))
            path = [(900, 540), (1010, 540), (1010, 640), (1112, 640)]
            arrow(ctx, path, SQLITE, prog(t, c[6] + 1.2, 0.7), 3, 0.9)
            text(ctx, "compara o hash", 1020, 525, 20, MUTED, alpha=prog(t, c[6] + 1.4, 0.5))
            icon_check(ctx, 620, 700, 36, GREEN, prog(t, c[6] + 2.4, 0.6))
            text(ctx, "login local", 620, 770, 26, GREEN, bold=True, align="center",
                 alpha=prog(t, c[6] + 2.4, 0.6))
            ra = prog(t, c[6] + d * 0.78, 0.6)
            if ra > 0:
                icon_jwt(ctx, 1500, 260, 130, ra, "JWT")
                text(ctx, "token renovado", 1500, 345, 22, PURPLE, bold=True, align="center",
                     alpha=ra)

    # ---------- fase D: middleware de auditoria
    if pD > 0:
        with layer(ctx, pD):
            svcs = [(200, NODE, "auth-service"), (760, JAVA, "clinical-service"),
                    (1320, PY, "document-service")]
            for i, (x, col, name) in enumerate(svcs):
                a, s = appear(t, c[7] + 0.2 + 0.25 * i)
                with layer(ctx, a, s, x + 200, 205):
                    card(ctx, x, 150, 400, 110, col, name, None, icon=svc_icon(col), title_size=26)
            ba = prog(t, c[7] + 1.2, 0.7)
            with layer(ctx, ba):
                rrect(ctx, 200, 300, 1520, 70, 35)
                rgba(ctx, CYAN, 0.14)
                ctx.fill_preserve()
                rgba(ctx, CYAN, 0.9)
                ctx.set_line_width(2)
                ctx.stroke()
                icon_shield(ctx, 250, 335, 44, CYAN)
                text(ctx, "middleware de log de acesso", 290, 335, 26, WHITE, bold=True, middle=True)
                text(ctx, "em todos os serviços", 1690, 335, 22, MUTED, align="right", middle=True)
            for i, (x, col, _) in enumerate(svcs):
                loop_packets(ctx, [(x + 200, 262), (x + 200, 300)], t, c[7] + 1.6 + i * 0.3, 1.4,
                             col, ba, r=6)
            cols = [250, 200, 220, 140, 360, 190, 160]
            hdr = ["data_hora", "ip_cliente", "profissional_id", "metodo", "rota", "status_code",
                   "tempo_ms"]
            rows = [
                ["14:02:11", "10.0.0.23", "7", "POST", "/auth/login", "200", "84"],
                ["14:02:15", "10.0.0.23", "7", "GET", "/sync/pull", "200", "132"],
                ["14:31:40", "10.0.0.23", "7", "POST", "/sync/push", "200", "241"],
                ["14:31:41", "10.0.0.23", "7", "POST", "/log", "201", "38"],
                ["14:35:02", "10.0.0.51", "—", "GET", "/atendimento", ("401", RED), "3"],
                ["14:36:10", "10.0.0.51", "2", "GET", "/documento/ficha/…", "200", "410"],
            ]
            ta = prog(t, c[7] + 1.8, 0.6)
            text(ctx, "audit.access_log", 200, 440, 24, CYAN, bold=True, alpha=ta, mono=True)
            ra = [prog(t, c[8] + 0.3 + 0.8 * i, 0.5) for i in range(len(rows))]
            d8 = S.e[8] - c[8]
            hc = int(clamp((t - c[8]) / d8) * 8.5) if t > c[8] else None
            table(ctx, 200, 462, cols, hdr, rows, ra, size=21, row_h=52, alpha=ta,
                  hl_col=hc if hc is not None and hc < 7 else None, hl_u=1.0,
                  mono_cols=(0, 1, 2, 3, 4, 5, 6))


# ================================================================ cena 4
STEPS = ["Pessoa", "Prontuário", "Atendimento", "Sinais vitais", "Glasgow", "Triagem", "Medicação"]


def scene4(ctx, t, S):
    c, e = S.c, S.e
    wa, ws = appear(t, c[0] + 0.2, 0.7)
    d8 = e[8] - c[8]
    online = 1.0
    if t > c[8]:
        online = 1 - prog(t, c[8] + 1.0, 0.4) + prog(t, c[8] + d8 * 0.62, 0.4)
    with layer(ctx, wa, ws, 830, 515):
        win(ctx, 100, 130, 1460, 770, "MedicalField · Cliente desktop", status=clamp(online))
        # chave de simulação
        tx, ty = 1180, 156
        text(ctx, "Simular conectividade", tx - 20, ty, 18, MUTED, align="right", middle=True)
        rrect(ctx, tx, ty - 15, 56, 30, 15)
        rgba(ctx, mix(RED, GREEN, clamp(online)), 0.9)
        ctx.fill()
        ctx.arc(tx + 15 + 26 * clamp(online), ty, 11, 0, 2 * math.pi)
        rgba(ctx, WHITE)
        ctx.fill()
        # etapas
        cur = -1
        for i in range(7):
            if t >= c[i + 1] - 0.2:
                cur = i
        if t > e[7] + 0.3:
            cur = 7
        for i, name in enumerate(STEPS):
            y = 230 + i * 88
            done = i < cur
            active = i == cur
            if active:
                rrect(ctx, 120, y - 34, 320, 68, 14)
                rgba(ctx, CYAN, 0.15)
                ctx.fill()
            ctx.arc(160, y, 20, 0, 2 * math.pi)
            rgba(ctx, GREEN if done else (CYAN if active else DIM), 1 if (done or active) else 0.6)
            ctx.fill()
            text(ctx, "✓" if done else str(i + 1), 160, y, 20, hexc("06101F"), bold=True,
                 align="center", middle=True)
            text(ctx, name, 196, y, 24, WHITE if (active or done) else MUTED, bold=active,
                 middle=True)
            if i < 6:
                ctx.rectangle(159, y + 22, 2, 44)
                rgba(ctx, GREEN if done else DIM, 0.6)
                ctx.fill()
        ctx.rectangle(460, 182, 1.5, 700)
        ctx.set_source_rgba(1, 1, 1, 0.08)
        ctx.fill()
        # conteúdo de cada etapa
        for i in range(7):
            t0 = c[i + 1]
            t1 = c[i + 2] if i < 6 else c[8]
            a = window(t, t0 - 0.1, t1 - 0.45, 0.35)
            if a > 0:
                with layer(ctx, a, 1, 1000, 520, dx=30 * (1 - a)):
                    STEP_DRAW[i](ctx, t - t0, t1 - t0, t)
        if t > c[8] - 0.1:
            a = prog(t, c[8] - 0.1, 0.5)
            with layer(ctx, a):
                text(ctx, "Atendimento registrado", 1010, 470, 40, WHITE, bold=True, align="center")
                text(ctx, "João Lima · BR-386, km 340 · Laranja", 1010, 520, 26, MUTED,
                     align="center")
                icon_check(ctx, 1010, 640, 60, GREEN, prog(t, c[8] + 0.1, 0.7))

    # SQLite fora da janela
    da, ds = appear(t, c[0] + 0.8)
    with layer(ctx, da, ds, 1745, 520):
        text(ctx, "grava primeiro aqui", 1745, 360, 22, SQLITE, bold=True, align="center")
        n = 0
        for i in range(7):
            if t > e[i + 1] - 0.4:
                n += 1
        hl = 0.0
        for i in range(7):
            hl = max(hl, window(t, e[i + 1] - 0.3, e[i + 1] + 0.2, 0.25))
        icon_db(ctx, 1745, 500, 230, 180, SQLITE, "SQLite", None, hl=hl)
        text(ctx, f"{n} gravações", 1745, 640, 22, MUTED, align="center")
    for i in range(7):
        u = prog(t, e[i + 1] - 1.1, 0.8, lambda x: x)
        chip_fly(ctx, (1480, 820), (1745, 470), u, "salvar", SQLITE, arc=-120)
    if t > c[8]:
        for k in range(3):
            u = prog(t, c[8] + 1.8 + k * d8 * 0.3, 0.9, lambda x: x)
            chip_fly(ctx, (1480, 820), (1745, 470), u, "salvar", SQLITE, arc=-120)


def _hdr(ctx, title, sub=None):
    text(ctx, title, 520, 240, 34, WHITE, bold=True)
    if sub:
        text(ctx, sub, 520, 280, 21, MUTED)


def step_pessoa(ctx, lt, d, t):
    _hdr(ctx, "Identificar paciente")
    field(ctx, 520, 330, 980, "Buscar pessoa", "João Lima", prog(lt, 0.3, 1.0, lambda x: x),
          active=lt < 1.6)
    na = prog(lt, 1.5, 0.4)
    text(ctx, "Nenhum resultado", 520, 430, 21, MUTED, alpha=na * (1 - prog(lt, 2.3, 0.3)))
    button(ctx, 1380, 430, "+ Nova pessoa", alpha=na, pressed=press(lt, 2.0), size=20)
    fa = prog(lt, 2.4, 0.5)
    vals = [("Nome", "João Lima"), ("Nascimento", "12/03/1984"), ("Sexo", "Masculino"),
            ("Tipo sanguíneo", "O+"), ("Alergias", "Dipirona"), ("Contato", "Maria Lima")]
    for k, (lb, vl) in enumerate(vals):
        x = 520 + (k % 2) * 500
        y = 520 + (k // 2) * 105
        field(ctx, x, y, 470, lb, vl, prog(lt, 2.6 + 0.35 * k, 0.6, lambda x: x), alpha=fa)


def step_prontuario(ctx, lt, d, t):
    _hdr(ctx, "Prontuário · João Lima", "nenhum prontuário encontrado → novo prontuário")
    pill(ctx, 1400, 240, "novo", CYAN, 20, filled=False, alpha=prog(lt, 0.4, 0.4))
    vals = [("Comorbidades", "Hipertensão"), ("Uso contínuo", "Losartana 50 mg"),
            ("Observações", "Sem cirurgias prévias")]
    for k, (lb, vl) in enumerate(vals):
        field(ctx, 520, 360 + k * 115, 980, lb, vl, prog(lt, 0.6 + 0.6 * k, 0.8, lambda x: x))


def step_atendimento(ctx, lt, d, t):
    _hdr(ctx, "Novo atendimento")
    vals = [("Início", "11/11/2026 14:02"), ("Local", "BR-386, km 340"),
            ("Queixa principal", "Trauma por colisão"), ("Profissional", "Ana Souza · CRM-RS 12345")]
    for k, (lb, vl) in enumerate(vals):
        x = 520 + (k % 2) * 500
        y = 360 + (k // 2) * 130
        field(ctx, x, y, 470, lb, vl, prog(lt, 0.3 + 0.35 * k, 0.6, lambda x: x))


def step_sinais(ctx, lt, d, t):
    _hdr(ctx, "Sinais vitais", "aferição 14:05")
    tiles = [("PA", "100/60", "mmHg"), ("FC", "118", "bpm"), ("FR", "24", "irpm"),
             ("SpO₂", "93", "%"), ("Temp.", "36,4", "°C"), ("Glicemia", "110", "mg/dL")]
    for k, (lb, vl, un) in enumerate(tiles):
        x = 520 + (k % 3) * 330
        y = 320 + (k // 3) * 250
        a, s = appear(lt, 0.4 + k * min(0.9, d / 8))
        with layer(ctx, a, s, x + 150, y + 105):
            rrect(ctx, x, y, 300, 210, 18)
            ctx.set_source_rgba(1, 1, 1, 0.05)
            ctx.fill_preserve()
            rgba(ctx, GREEN if k == 1 else CYAN, 0.5)
            ctx.set_line_width(2)
            ctx.stroke()
            text(ctx, lb, x + 24, y + 44, 24, MUTED, bold=True)
            vw = text(ctx, vl, x + 24, y + 122, 60, WHITE, bold=True)
            text(ctx, un, x + 34 + vw, y + 122, 24, MUTED)
            if k == 1:
                ecg(ctx, x + 14, y + 172, 272, 22, t, GREEN, 1, speed=200, period=110, width=2.5)


def step_glasgow(ctx, lt, d, t):
    _hdr(ctx, "Escala de Glasgow", "soma de 3 a 15")
    rows = [("Abertura ocular", 3, 4), ("Resposta verbal", 4, 5), ("Resposta motora", 6, 6)]
    total = 0
    for k, (lb, v, mx) in enumerate(rows):
        y = 370 + k * 120
        text(ctx, lb, 520, y, 26, WHITE, bold=True)
        u = prog(lt, 0.8 + k * min(1.3, d / 5), 0.8)
        for j in range(6):
            x = 520 + j * 92
            if j >= mx:
                continue
            on = (j < v) and u * v > j
            rrect(ctx, x, y + 18, 80, 44, 10)
            rgba(ctx, PURPLE if on else DIM, 0.9 if on else 0.35)
            ctx.fill()
            text(ctx, str(j + 1), x + 40, y + 40, 22, WHITE, bold=True, align="center", middle=True)
        total += v * u
    rrect(ctx, 1170, 330, 330, 330, 30)
    rgba(ctx, PURPLE, 0.15)
    ctx.fill_preserve()
    rgba(ctx, PURPLE, 0.9)
    ctx.set_line_width(3)
    ctx.stroke()
    text(ctx, "Total", 1335, 400, 28, MUTED, align="center")
    text(ctx, str(int(round(total))), 1335, 530, 130, WHITE, bold=True, align="center")
    text(ctx, "/ 15", 1335, 610, 26, MUTED, align="center")


def step_triagem(ctx, lt, d, t):
    _hdr(ctx, "Triagem")
    text(ctx, "Protocolo de Manchester", 520, 360, 26, WHITE, bold=True)
    man = [("Vermelho", RED), ("Laranja", ORANGE), ("Amarelo", hexc("FACC15")), ("Verde", GREEN),
           ("Azul", BLUE)]
    sel1 = prog(lt, 1.2, 0.4)
    for k, (n, col) in enumerate(man):
        x = 520 + k * 196
        a = prog(lt, 0.2 + 0.12 * k, 0.4)
        chosen = k == 1
        rrect(ctx, x, 390, 180, 76, 14)
        rgba(ctx, col, a * (0.95 if chosen and sel1 > 0 else 0.35))
        ctx.fill()
        if chosen and sel1 > 0:
            rrect(ctx, x - 6, 384, 192, 88, 18)
            rgba(ctx, WHITE, sel1)
            ctx.set_line_width(4)
            ctx.stroke()
        text(ctx, n, x + 90, 428, 22, WHITE, bold=True, align="center", middle=True, alpha=a)
    text(ctx, "START", 520, 560, 26, WHITE, bold=True)
    st = [("Vermelho", RED), ("Amarelo", hexc("FACC15")), ("Verde", GREEN), ("Preto", hexc("1F2937"))]
    sel2 = prog(lt, 2.6, 0.4)
    for k, (n, col) in enumerate(st):
        x = 520 + k * 245
        a = prog(lt, 1.6 + 0.12 * k, 0.4)
        chosen = k == 1
        rrect(ctx, x, 590, 225, 76, 14)
        rgba(ctx, col, a * (0.95 if chosen and sel2 > 0 else 0.45))
        ctx.fill()
        if chosen and sel2 > 0:
            rrect(ctx, x - 6, 584, 237, 88, 18)
            rgba(ctx, WHITE, sel2)
            ctx.set_line_width(4)
            ctx.stroke()
        text(ctx, n, x + 112, 628, 22, WHITE if k != 1 else hexc("06101F"), bold=True,
             align="center", middle=True, alpha=a)


def step_medicacao(ctx, lt, d, t):
    _hdr(ctx, "Conduta e medicação")
    field(ctx, 520, 340, 980, "Conduta", "Imobilização e acesso venoso",
          prog(lt, 0.3, 1.2, lambda x: x))
    cols = [380, 180, 120, 160, 140]
    hdr = ["medicamento", "dose", "via", "horário", ""]
    ra = prog(lt, 1.8, 0.5)
    table(ctx, 520, 450, cols, hdr, [["Soro fisiológico 0,9%", "1000 mL", "EV", "14:10", ""]],
          [ra], size=23, row_h=60)
    ok = prog(lt, 3.0, 0.5)
    icon_check(ctx, 1420, 540, 22, GREEN, ok)
    pill(ctx, 1010, 680, "dose dentro do máximo cadastrado", GREEN, 22, filled=False, alpha=ok)


STEP_DRAW = [step_pessoa, step_prontuario, step_atendimento, step_sinais, step_glasgow,
             step_triagem, step_medicacao]


# ================================================================ cena 5
REC = [("pessoa", "João Lima"), ("prontuario", "João Lima"), ("atendimento", "BR-386, km 340")]


def scene5(ctx, t, S):
    c, e = S.c, S.e
    base = prog(t, c[0] + 0.1, 0.8)
    signal = 1 - prog(t, c[1] + 0.5, 2.0, lambda x: x) + prog(t, c[7] + 0.8, 1.8, lambda x: x)
    signal = clamp(signal)
    online = clamp(1 - prog(t, c[2], 0.4) + prog(t, c[8], 0.4))
    rec_t = [c[3] + 0.6 + 1.6 * i for i in range(3)]
    push_t = [c[9] + 1.0 + 1.5 * i for i in range(3)]
    ack_t = [c[10] + 0.2 + 0.9 * i for i in range(3)]
    sync_t = c[11] + 0.3
    n_pend = sum(1 for x in rec_t if t > x + 0.9) - sum(1 for k in range(3) if t > sync_t + 0.5 * k)
    n_pend = max(0, n_pend)

    with layer(ctx, base):
        # cliente
        icon_laptop(ctx, 300, 230, 280)
        text(ctx, "Cliente desktop", 300, 362, 24, WHITE, bold=True, align="center")
        status_pill(ctx, 300, 415, online, size=22)
        # contador
        rrect(ctx, 520, 300, 230, 160, 20)
        cc = AMBER if n_pend else GREEN
        rgba(ctx, cc, 0.12)
        ctx.fill_preserve()
        rgba(ctx, cc, 0.8 + 0.2 * window(t, c[5], e[5]))
        ctx.set_line_width(2 + 2 * window(t, c[5], e[5]))
        ctx.stroke()
        text(ctx, "pendências", 635, 338, 22, MUTED, align="center")
        text(ctx, str(n_pend), 635, 430, 84, cc, bold=True, align="center")
        # SQLite
        card(ctx, 60, 520, 400, 360, SQLITE, "SQLite", None, title_size=26, top=True)
        icon_db(ctx, 390, 568, 70, 62, SQLITE)
        for i, (ent, desc) in enumerate(REC):
            a = prog(t, rec_t[i] + 0.8, 0.4)
            if a <= 0:
                continue
            y = 640 + i * 70
            synced = prog(t, sync_t + 0.5 * i, 0.4)
            text(ctx, ent, 90, y, 21, WHITE, bold=True, alpha=a, mono=True)
            pill(ctx, 340, y - 7, "SINCRONIZADO" if synced > 0.5 else "PENDENTE",
                 mix(AMBER, GREEN, synced), 15, filled=False, alpha=a, pad=10)
        pa = prog(t, c[13] + 2.2, 0.5)
        if pa > 0:
            text(ctx, "medicamento", 90, 850, 21, WHITE, bold=True, alpha=pa, mono=True)
            pill(ctx, 340, 843, "ATUALIZADO", CYAN, 15, filled=False, alpha=pa, pad=10)
        # Outbox
        card(ctx, 490, 520, 300, 360, AMBER, "Outbox", None, title_size=26, top=True)
        for i, (ent, _) in enumerate(REC):
            a = prog(t, rec_t[i] + 0.8, 0.4)
            gone = prog(t, push_t[i], 0.3)
            if a <= 0 or gone >= 1:
                continue
            y = 610 + i * 74
            with layer(ctx, a * (1 - gone)):
                rrect(ctx, 515, y, 250, 58, 12)
                rgba(ctx, AMBER, 0.16)
                ctx.fill_preserve()
                rgba(ctx, AMBER, 0.8)
                ctx.set_line_width(1.5)
                ctx.stroke()
                text(ctx, f"#{41 + i} {ent}", 532, y + 29, 19, WHITE, middle=True, mono=True)
        # local_log
        card(ctx, 820, 520, 330, 360, PURPLE, "local_log", None, title_size=26, top=True)
        logs = ["14:31 criar pessoa", "14:32 criar prontuário", "14:33 abrir atendimento"]
        for i, s in enumerate(logs):
            a = prog(t, c[4] + 0.3 + 0.6 * i, 0.4)
            sent = prog(t, c[12] + 0.5 + 0.3 * i, 0.4)
            y = 625 + i * 56
            text(ctx, s, 848, y, 19, mix(WHITE, MUTED, sent), alpha=a, mono=True)
            icon_check(ctx, 1120, y - 7, 11, GREEN, sent)

        # servidor
        panel(ctx, 1260, 130, 600, 750, BLUE, 1, "VM da Univates")
        card(ctx, 1300, 200, 520, 140, JAVA, "clinical-service", "/sync/push · /sync/pull · /log",
             icon=svc_icon(JAVA), title_size=26)
        spin = window(t, c[10] - 0.2, e[10])
        if spin > 0:
            icon_gear(ctx, 1770, 230, 22, t * 3, JAVA, spin)
        icon_db(ctx, 1560, 620, 260, 220, PG, "PostgreSQL", "banco central",
                hl=window(t, c[10], e[11]))
        arrow(ctx, [(1560, 342), (1560, 505)], JAVA, 1, 3, 0.7)

        # conexão
        line = [(470, 230), (1296, 230)]
        broken = 1 - online
        arrow(ctx, line, mix(GREEN, RED, broken), 1, 4, 0.55, head=False,
              dash=[14, 12] if broken > 0.5 else None)
        icon_wifi(ctx, 930, 140, 100, GREEN, 3 * signal, prog(t, c[1] + 2.4, 0.4) * (1 - prog(t, c[7] + 0.6, 0.4)))
        if broken > 0.5:
            icon_x(ctx, 930, 230, 24, RED, broken)

    # ambulância chegando ao hospital
    amb_a = window(t, c[1], e[1] + 0.3) + window(t, c[7], e[7])
    if amb_a > 0:
        x = 900 + 40 * math.sin(t * 0.8)
        icon_ambulance(ctx, x, 340, 150, t, clamp(amb_a))

    # registros indo para SQLite e Outbox
    for i, (ent, _) in enumerate(REC):
        u = prog(t, rec_t[i], 0.9, lambda x: x)
        chip_fly(ctx, (300, 260), (230, 640 + i * 70), u, ent, SQLITE, arc=-60)
        chip_fly(ctx, (300, 260), (640, 640 + i * 74), u, ent, AMBER, arc=-120)

    # salvo localmente
    sa = window(t, c[6], e[6] + 0.3)
    if sa > 0:
        with layer(ctx, sa, lerp(0.9, 1, sa), 930, 420):
            pill(ctx, 930, 420, "✓ salvo localmente", GREEN, 30, filled=True)

    # Observer
    oa = window(t, c[8] + 0.6, e[9])
    if oa > 0:
        with layer(ctx, oa):
            card(ctx, 800, 290, 300, 66, CYAN, "ConnectivityMonitor", None, title_size=21)
            card(ctx, 800, 392, 300, 66, CYAN, "SyncService", None, title_size=21)
            arrow(ctx, [(950, 358), (950, 388)], CYAN, prog(t, c[8] + 1.2, 0.5), 3)
            text(ctx, "padrão Observer", 950, 484, 18, MUTED, align="center", alpha=prog(t, c[8] + 1.4, 0.4))
            packet(ctx, [(950, 358), (950, 390)], prog(t, c[8] + 1.6, 0.7, lambda x: x), CYAN)

    # push
    route = [(640, 640), (640, 490), (1230, 490), (1230, 262), (1296, 262)]
    for i, (ent, _) in enumerate(REC):
        u = prog(t, push_t[i], 1.8, lambda x: x)
        if i == 0 and 0 < u < 1:
            pass
        packet(ctx, [(640, 640 + i * 74)] + route[1:], ease_in_out(u), AMBER,
               ent if i else f"POST /sync/push · {ent}", label_dy=-30)
    # acks
    ack_route = [(1298, 300), (1250, 300), (1250, 505), (420, 505), (420, 600)]
    for i in range(3):
        u = prog(t, ack_t[i], 1.6, lambda x: x)
        packet(ctx, ack_route, ease_in_out(u), GREEN, "APLICADO", label_dy=-30)
    # logs
    for i in range(3):
        u = prog(t, c[12] + 0.3 + 0.3 * i, 1.6, lambda x: x)
        packet(ctx, [(985, 600), (985, 500), (1240, 500), (1240, 300), (1296, 300)],
               ease_in_out(u), PURPLE, "POST /log" if i == 0 else None, label_dy=-30)
    # pull
    pulls = ["medicamentos", "pessoas", "prontuários"]
    for i, s in enumerate(pulls):
        u = prog(t, c[13] + 0.6 + 0.6 * i, 1.8, lambda x: x)
        packet(ctx, [(1296, 230), (470, 230)], ease_in_out(u), CYAN, s, label_dy=34)
    qa = window(t, c[13] + 0.2, e[13] - 0.2)
    pill(ctx, 1110, 185, "GET /sync/pull?since=…", CYAN, 20, filled=False, alpha=qa, mono=True)

    # comparação final push × pull
    fa = prog(t, c[14] - 0.2, 0.6)
    if fa > 0:
        with layer(ctx, fa):
            rrect(ctx, 460, 340, 1000, 360, 26)
            ctx.set_source_rgba(0.04, 0.09, 0.18, 0.95)
            ctx.fill_preserve()
            rgba(ctx, CYAN, 0.6)
            ctx.set_line_width(2)
            ctx.stroke()
            arrow(ctx, [(560, 450), (1360, 450)], AMBER, prog(t, c[14], 0.8), 8)
            text(ctx, "PUSH", 960, 420, 34, AMBER, bold=True, align="center")
            text(ctx, "dispositivo → servidor: envia a Outbox", 960, 500, 24, WHITE, align="center")
            arrow(ctx, [(1360, 590), (560, 590)], CYAN, prog(t, c[14] + 1.6, 0.8), 8)
            text(ctx, "PULL", 960, 560, 34, CYAN, bold=True, align="center")
            text(ctx, "servidor → dispositivo: traz as novidades", 960, 640, 24, WHITE, align="center")


# ================================================================ cena 6
UUID = "0b6f9c1e-4a2d-4c7b-9f4e-1d2a3b4c5d6e"


def scene6(ctx, t, S):
    c, e = S.c, S.e
    pA = window(t, 0, c[4] - 0.3)
    pB = window(t, c[4], c[8] - 0.3)
    pC = window(t, c[8], S.T + 5)
    if pA > 0:
        with layer(ctx, pA):
            icon_laptop(ctx, 300, 300, 240)
            text(ctx, "Cliente · amb-03", 300, 420, 24, WHITE, bold=True, align="center")
            icon_server(ctx, 1620, 300, 200, 170, JAVA, t)
            text(ctx, "clinical-service", 1620, 420, 24, WHITE, bold=True, align="center")
            path = [(440, 300), (1500, 300)]
            arrow(ctx, path, DIM, 1, 3, 0.8, head=False, dash=[10, 10])
            # envio interrompido
            u = prog(t, c[0] + 0.3, 2.0, lambda x: x)
            if u < 0.55:
                packet(ctx, path, u, AMBER, "atendimento")
            cut = prog(t, c[0] + 1.4, 0.3)
            if cut > 0 and t < c[1] + 0.5:
                a = clamp(cut) * (1 - prog(t, c[1], 0.5))
                ctx.move_to(990, 230)
                ctx.line_to(950, 290)
                ctx.line_to(985, 300)
                ctx.line_to(945, 370)
                rgba(ctx, RED, a)
                ctx.set_line_width(6)
                ctx.stroke()
                text(ctx, "conexão caiu", 960, 420, 24, RED, bold=True, align="center", alpha=a)
            # UUID dos dois lados
            ua = prog(t, c[1] + 0.3, 0.6)
            for x, who in ((160, "no dispositivo"), (1160, "no servidor")):
                with layer(ctx, ua):
                    rrect(ctx, x, 500, 600, 120, 16)
                    ctx.set_source_rgba(0.06, 0.12, 0.24, 0.95)
                    ctx.fill_preserve()
                    rgba(ctx, CYAN, 0.8)
                    ctx.set_line_width(2)
                    ctx.stroke()
                    text(ctx, f"atendimento · {who}", x + 24, 538, 20, MUTED)
                    text(ctx, "id: " + UUID, x + 24, 585, 20, CYAN, mono=True)
            if ua > 0:
                text(ctx, "=", 960, 562, 60, CYAN, bold=True, align="center", alpha=ua, middle=True)
            # chave de idempotência
            ka = prog(t, c[2] + 0.3, 0.6)
            with layer(ctx, ka):
                rrect(ctx, 160, 660, 600, 110, 16)
                rgba(ctx, AMBER, 0.12)
                ctx.fill_preserve()
                rgba(ctx, AMBER, 0.9)
                ctx.set_line_width(2)
                ctx.stroke()
                text(ctx, "Idempotency-Key", 184, 700, 22, AMBER, bold=True, mono=True)
                text(ctx, "outboxId 43 + deviceId amb-03", 184, 745, 21, WHITE, mono=True)
            # dois envios
            sends = [c[3] + 0.3, c[3] + 2.6]
            for i, t0 in enumerate(sends):
                u = prog(t, t0, 1.3, lambda x: x)
                packet(ctx, [(460, 715), (1150, 715)], ease_in_out(u), AMBER,
                       "1º envio" if i == 0 else "2º envio (repetido)", label_dy=-32, mono=False)
            ta = prog(t, sends[0] + 1.3, 0.4)
            with layer(ctx, ta):
                text(ctx, "clinical.idempotencia", 1160, 680, 21, MUTED, mono=True)
                table(ctx, 1160, 695, [330, 270], ["chave", "resultado"],
                      [["amb-03:43", ("APLICADO", GREEN)]], [1], size=20, row_h=46,
                      hl_row=0, hl_u=window(t, sends[1] + 1.2, sends[1] + 2.4), mono_cols=(0, 1))
            da = prog(t, sends[1] + 1.4, 0.4, back_out)
            if da > 0:
                with layer(ctx, clamp(da), lerp(1.4, 1, clamp(da)), 1460, 860):
                    pill(ctx, 1460, 840, "DUPLICADO · nada é gravado", AMBER, 24, filled=True)

    if pB > 0:
        with layer(ctx, pB):
            card(ctx, 760, 150, 400, 80, PURPLE, "MergeStrategy", None, title_size=26)
            text(ctx, "padrão Strategy", 960, 262, 20, MUTED, align="center")
            strat = [
                (110, "LastWriteWinsStrategy", "pessoa · prontuário", 5),
                (700, "AppendOnlyMergeStrategy", "sinais vitais · medicações", 6),
                (1290, "ServerWinsStrategy", "medicamentos", 7),
            ]
            for (x, name, use, k) in strat:
                hl = window(t, c[k], e[k])
                dimmed = 0.55 + 0.45 * max(hl, 1 - prog(t, c[5] - 0.3, 0.5))
                arrow(ctx, [(960, 232), (960, 280), (x + 260, 280), (x + 260, 318)], PURPLE, 1, 2,
                      0.6, head=True)
                with layer(ctx, dimmed):
                    rrect(ctx, x, 320, 520, 520, 20)
                    ctx.set_source_rgba(0.06, 0.12, 0.24, 0.95)
                    ctx.fill_preserve()
                    rgba(ctx, PURPLE, 0.5 + 0.5 * hl)
                    ctx.set_line_width(2 + 2 * hl)
                    ctx.stroke()
                    text(ctx, name, x + 260, 370, 24, WHITE, bold=True, align="center")
                    pill(ctx, x + 260, 415, use, CYAN, 18, filled=False)
                    STRAT_DRAW[k - 5](ctx, x, t - c[k], hl, t > c[k])

    if pC > 0:
        with layer(ctx, pC):
            text(ctx, "audit.sync_evento", 260, 230, 30, CYAN, bold=True, mono=True)
            rrect(ctx, 240, 260, 1440, 560, 22)
            ctx.set_source_rgba(0.06, 0.12, 0.24, 0.95)
            ctx.fill_preserve()
            rgba(ctx, CYAN, 0.6)
            ctx.set_line_width(2)
            ctx.stroke()
            kv = [("device_id", "amb-03"), ("entidade", "PESSOA"), ("status", "CONFLITO_RESOLVIDO"),
                  ("estrategia", "LastWriteWins"), ("versao_cliente", "3"), ("versao_servidor", "2")]
            for i, (k, v) in enumerate(kv):
                a = prog(t, c[8] + 0.3 + 0.25 * i, 0.4)
                x = 290 + (i % 3) * 460
                y = 320 + (i // 3) * 80
                text(ctx, k, x, y, 19, MUTED, alpha=a, mono=True)
                text(ctx, v, x, y + 34, 24, WHITE, bold=True, alpha=a, mono=True)
            ja = prog(t, c[8] + 2.2, 0.5)
            for x, title, body, col in ((290, "antes", '{ "telefone": "51 3333-0000",\n  "version": 2 }', DIM),
                                        (1010, "depois", '{ "telefone": "51 9999-0000",\n  "version": 3 }', GREEN)):
                with layer(ctx, ja):
                    rrect(ctx, x, 520, 620, 230, 16)
                    rgba(ctx, col, 0.12)
                    ctx.fill_preserve()
                    rgba(ctx, col, 0.8)
                    ctx.set_line_width(2)
                    ctx.stroke()
                    text(ctx, title, x + 24, 560, 22, col if col != DIM else MUTED, bold=True)
                    for j, ln in enumerate(body.split("\n")):
                        text(ctx, ln, x + 24, 615 + j * 40, 22, WHITE, mono=True)
            arrow(ctx, [(918, 635), (1002, 635)], GREEN, prog(t, c[8] + 2.6, 0.5), 4)
            pill(ctx, 960, 870, "toda decisão de merge é auditável", CYAN, 24, filled=False,
                 alpha=prog(t, c[8] + 3.2, 0.5))


def strat_lww(ctx, x, lt, hl, on):
    win_u = prog(lt, 2.6, 0.5) if on else 0
    for i, (who, ts, newer) in enumerate((("cliente", "14:12", True), ("servidor", "13:50", False))):
        y = 470 + i * 150
        a = 1 - 0.65 * win_u * (0 if newer else 1)
        col = GREEN if (newer and win_u > 0) else MUTED
        with layer(ctx, a):
            rrect(ctx, x + 40, y, 440, 120, 14)
            rgba(ctx, col, 0.12)
            ctx.fill_preserve()
            rgba(ctx, col, 0.9)
            ctx.set_line_width(2 + 2 * win_u * newer)
            ctx.stroke()
            text(ctx, who, x + 64, y + 44, 22, WHITE, bold=True)
            text(ctx, f"updated_at {ts}", x + 64, y + 88, 20, MUTED, mono=True)
        if newer:
            icon_check(ctx, x + 440, y + 60, 24, GREEN, win_u)


def strat_append(ctx, x, lt, hl, on):
    m = prog(lt, 2.4, 1.2, ease_in_out) if on else 0
    left = ["SV 14:05", "SV 14:20"]
    right = ["SV 14:05", "SV 14:15"]
    merged = ["SV 14:05", "SV 14:15", "SV 14:20"]
    a1 = 1 - m
    for j, s in enumerate(left):
        text(ctx, s, x + 70, 500 + j * 48, 22, WHITE, alpha=a1, mono=True)
    for j, s in enumerate(right):
        text(ctx, s, x + 300, 500 + j * 48, 22, WHITE, alpha=a1, mono=True)
    text(ctx, "cliente", x + 70, 465, 18, MUTED, alpha=a1)
    text(ctx, "servidor", x + 300, 465, 18, MUTED, alpha=a1)
    for j, s in enumerate(merged):
        aj = prog(lt, 2.8 + 0.3 * j, 0.4) if on else 0
        y = 620 + j * 52
        rrect(ctx, x + 140, y - 30, 240, 44, 10)
        rgba(ctx, GREEN, 0.15 * aj)
        ctx.fill()
        text(ctx, s, x + 260, y - 8, 22, WHITE, align="center", alpha=aj, mono=True, middle=True)
    text(ctx, "união pelo id · nada é apagado", x + 260, 800, 19, GREEN, align="center",
         alpha=prog(lt, 3.8, 0.5) if on else 0)


def strat_server(ctx, x, lt, hl, on):
    win_u = prog(lt, 2.4, 0.5) if on else 0
    for i, (who, val, srv) in enumerate((("cliente", "cópia local", False),
                                         ("servidor", "cadastro oficial", True))):
        y = 470 + i * 150
        a = 1 - 0.65 * win_u * (0 if srv else 1)
        col = GREEN if (srv and win_u > 0) else MUTED
        with layer(ctx, a):
            rrect(ctx, x + 40, y, 440, 120, 14)
            rgba(ctx, col, 0.12)
            ctx.fill_preserve()
            rgba(ctx, col, 0.9)
            ctx.set_line_width(2 + 2 * win_u * srv)
            ctx.stroke()
            text(ctx, who, x + 64, y + 44, 22, WHITE, bold=True)
            text(ctx, f"medicamento · {val}", x + 64, y + 88, 20, MUTED)
        if srv:
            icon_check(ctx, x + 440, y + 60, 24, GREEN, win_u)


STRAT_DRAW = [strat_lww, strat_append, strat_server]


# ================================================================ cena 7
PORTAL_TABS = ["Profissionais", "Pessoas", "Prontuários", "Atendimentos", "Auditoria"]
PORTAL_DATA = {
    0: ([330, 300, 200, 300], ["Nome", "Registro", "Tipo", "Perfil"],
        [["Ana Souza", "CRM-RS 12345", "CRM", "SOCORRISTA"],
         ["Bruno Alves", "COREN-RS 5521", "COREN", "SOCORRISTA"],
         ["Carla Dias", "SOC-0042", "SOCORRISTA", "SOCORRISTA"],
         ["Admin", "ADM-001", "CRM", "ADMIN"]]),
    1: ([330, 260, 240, 300], ["Nome", "Nascimento", "Tipo sang.", "Alergias"],
        [["Maria Santos", "02/05/1975", "A+", "—"],
         ["Carlos Pereira", "19/09/1990", "O-", "Penicilina"],
         ["Lúcia Rocha", "30/01/1962", "B+", "—"]]),
    2: ([330, 380, 400], ["Pessoa", "Comorbidades", "Atualizado em"],
        [["Maria Santos", "Diabetes tipo 2", "08/11/2026 09:12"],
         ["Carlos Pereira", "—", "09/11/2026 17:40"],
         ["Lúcia Rocha", "Hipertensão", "10/11/2026 08:05"]]),
    3: ([210, 260, 300, 190, 250], ["Início", "Pessoa", "Local", "Triagem", "Origem"],
        [["10/11 08:05", "Lúcia Rocha", "Av. Benjamin, 120", ("Amarelo", hexc("FACC15")), "online"],
         ["09/11 17:40", "Carlos Pereira", "RS-130, km 12", ("Verde", GREEN), "online"],
         ["08/11 09:12", "Maria Santos", "Centro, Lajeado", ("Laranja", ORANGE), "online"]]),
    4: ([230, 360, 180, 180, 220], ["data_hora", "rota", "status", "tempo_ms", "serviço"],
        [["14:31:40", "/sync/push", "200", "241", "clinical"],
         ["14:31:41", "/log", "201", "38", "clinical"],
         ["14:35:02", "/atendimento", ("401", RED), "3", "clinical"],
         ["14:36:10", "/documento/ficha/…", "200", "410", "document"]]),
}


def scene7(ctx, t, S):
    c, e = S.c, S.e
    wa, ws = appear(t, c[0] + 0.1, 0.6)
    login_out = prog(t, c[0] + 2.6, 0.5)
    with layer(ctx, wa, ws, 960, 510):
        win(ctx, 140, 120, 1640, 780, "Portal administrativo · http://vm-univates/", accent=BLUE)
        if login_out < 1:
            with layer(ctx, 1 - login_out):
                rrect(ctx, 660, 250, 600, 520, 22)
                ctx.set_source_rgba(1, 1, 1, 0.04)
                ctx.fill()
                logo(ctx, 960, 320, 40, t)
                field(ctx, 720, 420, 480, "Registro", "CRM-RS 12345", prog(t, c[0] + 0.5, 0.9, lambda x: x))
                field(ctx, 720, 525, 480, "Senha", "••••••••", prog(t, c[0] + 1.4, 0.5, lambda x: x))
                button(ctx, 960, 650, "Entrar", w=480, pressed=press(t, c[0] + 2.1))
        if login_out > 0:
            with layer(ctx, login_out):
                ctx.rectangle(142, 174, 300, 724)
                ctx.set_source_rgba(1, 1, 1, 0.035)
                ctx.fill()
                logo(ctx, 292, 220, 22, t)
                # aba ativa
                if t < c[1]:
                    active = 0
                elif t < c[2] - 0.2:
                    active = min(4, int((t - c[1]) / ((e[1] - c[1]) / 5)))
                else:
                    active = 3
                for i, name in enumerate(PORTAL_TABS):
                    y = 300 + i * 70
                    if i == active:
                        rrect(ctx, 160, y - 28, 264, 56, 12)
                        rgba(ctx, CYAN, 0.18)
                        ctx.fill()
                    text(ctx, name, 190, y, 23, WHITE if i == active else MUTED, bold=i == active,
                         middle=True)
                text(ctx, PORTAL_TABS[active], 490, 245, 34, WHITE, bold=True)
                cols, hdr, rows = PORTAL_DATA[active]
                rows = list(rows)
                ra = [1.0] * len(rows)
                hl_row = None
                hl_u = 0.0
                if active == 3:
                    new = prog(t, c[3] + 1.4, 0.7)
                    if new > 0:
                        rows = [["11/11 14:02", "João Lima", "BR-386, km 340", ("Laranja", ORANGE),
                                 ("criado offline", AMBER)]] + rows
                        ra = [new] + ra
                        hl_row, hl_u = 0, window(t, c[3] + 1.4, S.T)
                table(ctx, 490, 290, cols, hdr, rows, ra, size=21, row_h=56,
                      hl_row=hl_row, hl_u=hl_u)
                if active == 3 and t > c[2] - 0.2 and t < c[3] + 1.4:
                    a = window(t, c[2], c[3] + 1.0)
                    text(ctx, "João Lima ainda não aparece", 490, 560, 24, MUTED, alpha=a)
    # cliente em miniatura
    ia = window(t, c[2], S.T + 5)
    if ia > 0:
        with layer(ctx, ia):
            on = prog(t, c[3] + 0.2, 0.4)
            rrect(ctx, 1320, 690, 420, 170, 18)
            ctx.set_source_rgba(0.04, 0.09, 0.18, 0.97)
            ctx.fill_preserve()
            rgba(ctx, mix(RED, GREEN, on), 0.9)
            ctx.set_line_width(2)
            ctx.stroke()
            text(ctx, "Cliente desktop", 1350, 735, 22, WHITE, bold=True)
            status_pill(ctx, 1640, 728, on, size=18)
            n = 3 - int(3 * prog(t, c[3] + 0.6, 0.7, lambda x: x))
            text(ctx, f"{n} pendências", 1350, 800, 26, AMBER if n else GREEN, bold=True)
            if 0 < prog(t, c[3] + 0.3, 1.0) < 1:
                icon_sync(ctx, 1690, 805, 18, t * 4, CYAN)
            elif on > 0.5:
                icon_check(ctx, 1690, 805, 18, GREEN, prog(t, c[3] + 1.3, 0.4))


# ================================================================ cena 8
def scene8(ctx, t, S):
    c, e = S.c, S.e
    wa, ws = appear(t, c[0] + 0.1)
    with layer(ctx, wa, ws, 390, 360):
        win(ctx, 80, 150, 620, 420, "Portal · Atendimentos", accent=BLUE)
        rrect(ctx, 100, 230, 580, 90, 12)
        rgba(ctx, CYAN, 0.14 * prog(t, c[0] + 0.6, 0.4))
        ctx.fill()
        text(ctx, "11/11 14:02 · João Lima", 124, 265, 24, WHITE, bold=True)
        text(ctx, "BR-386, km 340 · Laranja", 124, 300, 20, MUTED)
        button(ctx, 250, 400, "Gerar ficha (PDF)", w=300, size=20, pressed=press(t, c[1] + 0.8))
        button(ctx, 250, 480, "Enviar por e-mail", w=300, size=20, color=AMBER,
               pressed=press(t, c[5] + 0.5))
    da, ds = appear(t, c[1] + 0.6)
    with layer(ctx, da, ds, 990, 265):
        card(ctx, 820, 200, 360, 130, PY, "document-service", "Python · FastAPI · ReportLab",
             title_size=24, hl=window(t, c[2], e[3]))
    ca, cs = appear(t, c[2] + 0.4)
    with layer(ctx, ca, cs, 990, 545):
        card(ctx, 820, 480, 360, 130, JAVA, "clinical-service", "dados do atendimento",
             title_size=24, hl=window(t, c[2] + 1, e[2]))
    packet(ctx, [(402, 400), (600, 400), (600, 265), (818, 265)],
           prog(t, c[1] + 1.0, 1.4, ease_in_out), CYAN, "GET /documento/ficha/{id}", label_dy=-32)
    u = prog(t, c[2] + 1.0, 1.2, ease_in_out)
    if 0 < u < 1:
        (px, py), _ = path_at([(960, 332), (960, 478)], u)
        icon_jwt(ctx, px, py, 80)
    packet(ctx, [(1040, 478), (1040, 332)], prog(t, c[2] + 2.6, 1.2, ease_in_out), JAVA,
           "atendimento", label_dy=0)
    # PDF
    pa = prog(t, c[3] + 0.2, 0.6)
    if pa > 0:
        with layer(ctx, pa, lerp(0.9, 1, pa), 1520, 420):
            rrect(ctx, 1300, 130, 440, 580, 14)
            ctx.set_source_rgba(0.97, 0.98, 1, 1)
            ctx.fill()
            ink = hexc("0F172A")
            u3 = prog(t, c[3] + 0.4, (e[3] - c[3]) * 0.9, lambda x: x)
            rows = [("Ficha de Atendimento", 26, True, ink), ("MedicalField · 11/11/2026 14:02", 15, False, hexc("64748B")),
                    ("Paciente", 18, True, hexc("1D4ED8")), ("João Lima · O+ · alergia: dipirona", 17, False, ink),
                    ("Sinais vitais", 18, True, hexc("1D4ED8")), ("PA 100/60 · FC 118 · FR 24 · SpO₂ 93%", 17, False, ink),
                    ("Glasgow", 18, True, hexc("1D4ED8")), ("Total 13 (O3 V4 M6)", 17, False, ink),
                    ("Triagem", 18, True, hexc("1D4ED8")), ("Manchester Laranja · START Amarelo", 17, False, ink),
                    ("Medicações", 18, True, hexc("1D4ED8")), ("Soro fisiológico 0,9% · 1000 mL · EV", 17, False, ink)]
            y = 185
            for i, (s, sz, b, col) in enumerate(rows):
                a = clamp(u3 * len(rows) - i)
                text(ctx, s, 1330, y, sz, col, bold=b, alpha=a)
                y += 34 if b else 44
            rrect(ctx, 1640, 650, 80, 40, 6)
            rgba(ctx, RED)
            ctx.fill()
            text(ctx, "PDF", 1680, 670, 18, WHITE, bold=True, align="center", middle=True)
    # download
    dl = prog(t, c[4] + 0.2, 1.2, ease_in_out)
    if 0 < dl < 1:
        (px, py), _ = path_at([(1300, 600), (900, 690), (390, 600)], dl)
        icon_doc(ctx, px, py, 60, 78, CYAN)
    dla = prog(t, c[4] + 1.4, 0.4)
    if dla > 0:
        pill(ctx, 390, 620, "⬇ ficha_atendimento.pdf", GREEN, 20, filled=False, alpha=dla * wa)
    # e-mail
    ea = prog(t, c[5] + 0.6, 0.5)
    if ea > 0:
        with layer(ctx, ea):
            card(ctx, 900, 760, 260, 110, AMBER, "SMTP", None, title_size=26)
            icon_envelope(ctx, 1090, 815, 64, AMBER)
            icon_person(ctx, 1560, 790, 70, CYAN)
            text(ctx, "Maria Lima · familiar", 1560, 865, 22, WHITE, bold=True, align="center")
    eu = prog(t, c[5] + 1.0, 3.0, lambda x: x)
    if 0 < eu < 1:
        (px, py), _ = path_at([(1000, 335), (1000, 400), (760, 400), (760, 815), (900, 815),
                               (1160, 815), (1480, 815)], ease_in_out(eu))
        icon_envelope(ctx, px, py, 70, AMBER)
        icon_doc(ctx, px + 26, py - 22, 26, 34, CYAN, badge=None)
    ok = prog(t, c[5] + 4.1, 0.5)
    icon_check(ctx, 1640, 760, 26, GREEN, ok)
    pill(ctx, 1000, 700, "document.envio_email · ENVIADO", GREEN, 20, filled=False,
         alpha=prog(t, c[5] + 4.6, 0.5), mono=True)


# ================================================================ cena 9
BENEFITS = [
    ("Atendimento mesmo sem internet", "wifi"),
    ("Armazenamento local e sincronização automática", "sync"),
    ("Informações clínicas organizadas", "doc"),
    ("Segurança e rastreabilidade", "shield"),
    ("Microsserviços em três linguagens", "svc"),
    ("Ficha em PDF e envio por e-mail", "mail"),
]


def _benefit_icon(ctx, kind, cx, cy, t):
    if kind == "wifi":
        icon_wifi(ctx, cx, cy - 6, 70, CYAN, 0, 1)
        icon_check(ctx, cx + 30, cy + 22, 16, GREEN)
    elif kind == "sync":
        icon_sync(ctx, cx, cy, 30, t * 1.5, CYAN)
    elif kind == "doc":
        icon_doc(ctx, cx, cy, 52, 66, CYAN, badge=None)
    elif kind == "shield":
        icon_shield(ctx, cx, cy, 70, CYAN)
        icon_lock(ctx, cx, cy + 2, 30, CYAN)
    elif kind == "svc":
        for i, col in enumerate((NODE, JAVA, PY)):
            ctx.arc(cx - 26 + i * 26, cy + (8 if i % 2 == 0 else -14), 13, 0, 2 * math.pi)
            rgba(ctx, col)
            ctx.fill()
    else:
        icon_envelope(ctx, cx, cy, 64, CYAN)


def scene9(ctx, t, S):
    c, e = S.c, S.e
    show = [1, 2, 3, 3, 4, 5]
    grid_out = prog(t, c[6] - 0.4, 0.6)
    up = prog(t, c[1] - 0.2, 0.9, ease_in_out) * (1 - grid_out)
    a0 = prog(t, c[0], 0.9)
    ly = lerp(lerp(520, 230, up), 470, grid_out)
    with layer(ctx, a0, lerp(0.92, 1, a0), 960, ly):
        logo(ctx, 960, ly, lerp(120, 80, up) if grid_out < 0.5 else 110, t)
    for i, (label, kind) in enumerate(BENEFITS):
        a, s = appear(t, c[show[i]] + 0.2 + (0.6 if i == 3 else 0))
        a *= 1 - grid_out
        if a <= 0:
            continue
        x = 180 + (i % 3) * 540
        y = 380 + (i // 3) * 230
        with layer(ctx, a, s, x + 240, y + 90):
            rrect(ctx, x, y, 480, 180, 22)
            ctx.set_source_rgba(1, 1, 1, 0.05)
            ctx.fill_preserve()
            rgba(ctx, CYAN, 0.45)
            ctx.set_line_width(2)
            ctx.stroke()
            _benefit_icon(ctx, kind, x + 80, y + 90, t)
            lines = wrap(ctx, label, 26, 320, True)
            y0 = y + 90 - (len(lines) - 1) * 18
            for j, ln in enumerate(lines):
                text(ctx, ln, x + 145, y0 + j * 36, 26, WHITE, bold=True, middle=True)
    if t > c[6] - 0.2:
        a = prog(t, c[6] + 0.3, 0.9)
        text(ctx, "Tecnologia, confiabilidade e continuidade no atendimento de emergência,",
             960, 610, 36, WHITE, align="center", alpha=a)
        text(ctx, "mesmo onde a conexão não chega.", 960, 662, 36, CYAN, bold=True, align="center",
             alpha=prog(t, c[6] + 1.2, 0.9))
        ecg(ctx, 560, 760, 800, 40, t, CYAN, 0.7 * a, width=2.5)


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9]
