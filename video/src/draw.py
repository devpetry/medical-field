"""Primitivas de desenho (pycairo) para o vídeo do MedicalField."""
import math
import random
from contextlib import contextmanager

import cairo

W, H = 1920, 1080


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


BG_TOP = hexc("06101F")
BG_BOT = hexc("0B1D3A")
WHITE = hexc("F1F5FB")
MUTED = hexc("94A3B8")
DIM = hexc("475569")
CYAN = hexc("38BDF8")
BLUE = hexc("3B82F6")
GREEN = hexc("22C55E")
RED = hexc("EF4444")
AMBER = hexc("F59E0B")
ORANGE = hexc("F97316")
PURPLE = hexc("A78BFA")
NODE = hexc("8CC84B")
JAVA = hexc("F89820")
PY = hexc("FFD43B")
PG = hexc("6CA0DC")
SQLITE = hexc("5EB8E8")
PANEL = hexc("0F2747")
CARD_FILL = (1, 1, 1, 0.045)


def rgba(ctx, c, alpha=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], (c[3] if len(c) > 3 else 1) * alpha)


# ---------------------------------------------------------------- tempo
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def back_out(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def prog(t, a, d=0.6, fn=ease_out):
    return fn(clamp((t - a) / d)) if d > 0 else (1.0 if t >= a else 0.0)


def window(t, a, b, fade=0.45):
    """1 entre a e b, com rampas de entrada e saída."""
    if t < a or t > b + fade:
        return 0.0
    return min(prog(t, a, fade), 1 - prog(t, b, fade, ease_in_out))


def lerp(a, b, u):
    return a + (b - a) * u


def mix(c1, c2, u):
    return tuple(lerp(c1[i], c2[i], u) for i in range(4))


# ---------------------------------------------------------------- texto
_faces = {}


SYMBOLS = set("✓↓→←⬇")


def font(ctx, size, bold=False, mono=False, sym=False):
    key = (bold, mono, sym)
    if key not in _faces:
        fam = "DejaVu Sans Mono" if mono else ("DejaVu Sans" if sym else "Noto Sans")
        _faces[key] = cairo.ToyFontFace(fam, cairo.FONT_SLANT_NORMAL,
                                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_face(_faces[key])
    ctx.set_font_size(size)


def text_w(ctx, s, size, bold=False, mono=False):
    font(ctx, size, bold, mono, any(ch in SYMBOLS for ch in s))
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size=28, color=WHITE, bold=False, align="left", alpha=1.0,
         mono=False, middle=False):
    if alpha <= 0.001 or not s:
        return 0
    font(ctx, size, bold, mono, any(ch in SYMBOLS for ch in s))
    w = ctx.text_extents(s).x_advance
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if middle:
        y += size * 0.36
    rgba(ctx, color, alpha)
    ctx.move_to(x, y)
    ctx.show_text(s)
    ctx.new_path()
    return w


def typed(s, u):
    n = int(round(len(s) * clamp(u)))
    return s[:n]


def wrap(ctx, s, size, maxw, bold=False):
    font(ctx, size, bold)
    words, lines, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if ctx.text_extents(trial).x_advance <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- camadas
@contextmanager
def layer(ctx, alpha=1.0, scale=1.0, cx=0.0, cy=0.0, dx=0.0, dy=0.0):
    ctx.save()
    group = alpha < 0.999
    if group:
        ctx.push_group()
    ctx.translate(cx + dx, cy + dy)
    ctx.scale(scale, scale)
    ctx.translate(-cx, -cy)
    try:
        yield
    finally:
        if group:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(clamp(alpha))
        ctx.restore()


def appear(t, t0, d=0.55):
    """(alpha, escala) para um elemento que surge em t0."""
    u = clamp((t - t0) / d)
    return ease_out(u), lerp(0.88, 1.0, back_out(u)) if u > 0 else 0.88


# ---------------------------------------------------------------- formas
def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def glow(ctx, cx, cy, r, color, alpha=0.5):
    ctx.new_path()
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    g.add_color_stop_rgba(0, color[0], color[1], color[2], alpha)
    g.add_color_stop_rgba(1, color[0], color[1], color[2], 0)
    ctx.set_source(g)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()


def panel(ctx, x, y, w, h, color=CYAN, alpha=1.0, label=None, dashed=True, fill=0.025):
    rrect(ctx, x, y, w, h, 22)
    ctx.set_source_rgba(color[0], color[1], color[2], fill * alpha)
    ctx.fill_preserve()
    rgba(ctx, color, 0.45 * alpha)
    ctx.set_line_width(2)
    if dashed:
        ctx.set_dash([10, 8])
    ctx.stroke()
    ctx.set_dash([])
    if label:
        text(ctx, label.upper(), x + 24, y + 38, 19, color, bold=True, alpha=0.9 * alpha)


def card(ctx, x, y, w, h, color, title, sub=None, alpha=1.0, hl=0.0, icon=None,
         title_size=30, sub_size=21, top=False):
    if alpha <= 0.001:
        return
    if hl > 0:
        glow(ctx, x + w / 2, y + h / 2, max(w, h) * 0.75, color, 0.22 * hl * alpha)
    rrect(ctx, x, y, w, h, 18)
    ctx.set_source_rgba(0.06, 0.13, 0.25, 0.92 * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(color[0], color[1], color[2], (0.07 + 0.08 * hl) * alpha)
    ctx.fill_preserve()
    rgba(ctx, color, (0.75 + 0.25 * hl) * alpha)
    ctx.set_line_width(2 + 1.5 * hl)
    ctx.stroke()
    # faixa de cor à esquerda
    rrect(ctx, x, y, 8, h, 4)
    rgba(ctx, color, alpha)
    ctx.fill()
    tx = x + 28
    if icon:
        icon(ctx, x + 60, y + h / 2)
        tx = x + 112
    if top:
        text(ctx, title, tx, y + 24 + title_size * 0.8, title_size, WHITE, bold=True, alpha=alpha)
        if sub:
            text(ctx, sub, tx, y + 24 + title_size * 0.8 + 34, sub_size, MUTED, alpha=alpha)
    elif sub:
        text(ctx, title, tx, y + h / 2 - 6, title_size, WHITE, bold=True, alpha=alpha)
        text(ctx, sub, tx, y + h / 2 + 28, sub_size, MUTED, alpha=alpha)
    else:
        text(ctx, title, tx, y + h / 2, title_size, WHITE, bold=True, alpha=alpha, middle=True)


def pill(ctx, cx, cy, s, color, size=22, filled=True, alpha=1.0, bold=True, pad=18, mono=False):
    if alpha <= 0.001:
        return
    w = text_w(ctx, s, size, bold, mono) + pad * 2
    h = size * 1.75
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
    if filled:
        rgba(ctx, color, 0.9 * alpha)
        ctx.fill()
        text(ctx, s, cx, cy, size, hexc("06101F"), bold=bold, align="center", alpha=alpha,
             middle=True, mono=mono)
    else:
        ctx.set_source_rgba(color[0], color[1], color[2], 0.14 * alpha)
        ctx.fill_preserve()
        rgba(ctx, color, alpha)
        ctx.set_line_width(2)
        ctx.stroke()
        text(ctx, s, cx, cy, size, color, bold=bold, align="center", alpha=alpha, middle=True,
             mono=mono)
    return w


# ---------------------------------------------------------------- caminhos
def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def path_at(pts, u):
    total = path_len(pts)
    d = clamp(u) * total
    for i in range(len(pts) - 1):
        seg = math.dist(pts[i], pts[i + 1])
        if d <= seg or i == len(pts) - 2:
            k = 0 if seg == 0 else d / seg
            k = clamp(k)
            return (lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)), i
        d -= seg
    return pts[-1], len(pts) - 2


def arrow(ctx, pts, color=MUTED, u=1.0, width=3, alpha=1.0, head=True, dash=None):
    if u <= 0.001 or alpha <= 0.001:
        return
    end, idx = path_at(pts, u)
    ctx.move_to(*pts[0])
    for p in pts[1:idx + 1]:
        ctx.line_to(*p)
    ctx.line_to(*end)
    rgba(ctx, color, alpha)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash:
        ctx.set_dash(dash)
    ctx.stroke()
    ctx.set_dash([])
    if head:
        prev = pts[idx] if math.dist(pts[idx], end) > 1 else pts[max(0, idx - 1)]
        ang = math.atan2(end[1] - prev[1], end[0] - prev[0])
        s = 7 + width * 2.2
        ctx.move_to(end[0], end[1])
        ctx.line_to(end[0] - s * math.cos(ang - 0.45), end[1] - s * math.sin(ang - 0.45))
        ctx.line_to(end[0] - s * math.cos(ang + 0.45), end[1] - s * math.sin(ang + 0.45))
        ctx.close_path()
        rgba(ctx, color, alpha)
        ctx.fill()


def packet(ctx, pts, u, color=CYAN, label=None, alpha=1.0, r=9, label_size=19, label_dy=-30,
           mono=True):
    if u <= 0 or u >= 1 or alpha <= 0.001:
        return
    (x, y), _ = path_at(pts, u)
    a = alpha * min(1, u * 8, (1 - u) * 8)
    glow(ctx, x, y, r * 3.2, color, 0.55 * a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    rgba(ctx, color, a)
    ctx.fill()
    ctx.arc(x, y, r * 0.45, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 1, 1, 0.9 * a)
    ctx.fill()
    if label:
        pill(ctx, x, y + label_dy, label, color, size=label_size, filled=False, alpha=a, mono=mono)


def loop_packets(ctx, pts, t, t0, period=2.2, color=CYAN, alpha=1.0, n=1, r=7, travel=None):
    """Pacotes contínuos ao longo de um caminho a partir de t0."""
    if t < t0 or alpha <= 0.001:
        return
    travel = travel or period
    for k in range(n):
        ph = ((t - t0) - k * period / n) % period
        if (t - t0) - k * period / n < 0:
            continue
        u = ph / travel
        if u < 1:
            packet(ctx, pts, ease_in_out(u), color, alpha=alpha, r=r)


# ---------------------------------------------------------------- ícones
def icon_check(ctx, cx, cy, r, color=GREEN, u=1.0, alpha=1.0):
    ctx.new_path()
    if u <= 0 or alpha <= 0.001:
        return
    a = alpha * clamp(u * 3)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    rgba(ctx, color, 0.18 * a)
    ctx.fill_preserve()
    rgba(ctx, color, a)
    ctx.set_line_width(max(2, r * 0.12))
    ctx.stroke()
    pts = [(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.35), (cx + r * 0.5, cy - r * 0.35)]
    arrow(ctx, pts, color, u=clamp(u * 1.4 - 0.2), width=max(3, r * 0.16), alpha=a, head=False)


def icon_x(ctx, cx, cy, r, color=RED, alpha=1.0):
    ctx.new_path()
    if alpha <= 0.001:
        return
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    rgba(ctx, color, 0.18 * alpha)
    ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(max(2, r * 0.12))
    ctx.stroke()
    k = r * 0.38
    ctx.move_to(cx - k, cy - k)
    ctx.line_to(cx + k, cy + k)
    ctx.move_to(cx + k, cy - k)
    ctx.line_to(cx - k, cy + k)
    ctx.set_line_width(max(3, r * 0.16))
    ctx.stroke()


def icon_wifi(ctx, cx, cy, s, color=CYAN, level=3.0, crossed=0.0, alpha=1.0):
    """level 0..3 (arcos acesos); crossed 0..1 desenha o corte."""
    ctx.new_path()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(3):
        on = clamp(level - i)
        r = s * (0.25 + 0.25 * i)
        ctx.arc(cx, cy + s * 0.35, r, math.radians(225), math.radians(315))
        rgba(ctx, mix(DIM, color, on), alpha * (0.45 + 0.55 * on))
        ctx.set_line_width(s * 0.1)
        ctx.stroke()
    ctx.arc(cx, cy + s * 0.35, s * 0.07, 0, 2 * math.pi)
    rgba(ctx, mix(DIM, color, clamp(level + 0.5)), alpha)
    ctx.fill()
    if crossed > 0:
        x0, y0, x1, y1 = cx - s * 0.5, cy - s * 0.4, cx + s * 0.5, cy + s * 0.55
        arrow(ctx, [(x0, y0), (x1, y1)], RED, u=crossed, width=s * 0.1, alpha=alpha, head=False)


def icon_db(ctx, cx, cy, w, h, color, label=None, sub=None, alpha=1.0, hl=0.0, fill_u=0.0):
    if alpha <= 0.001:
        return
    rx, ry = w / 2, w * 0.14
    top, bot = cy - h / 2 + ry, cy + h / 2 - ry
    if hl > 0:
        glow(ctx, cx, cy, w * 0.95, color, 0.3 * hl * alpha)

    def ell(y):
        ctx.save()
        ctx.translate(cx, y)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()

    # corpo
    ctx.move_to(cx - rx, top)
    ctx.line_to(cx - rx, bot)
    ctx.save()
    ctx.translate(cx, bot)
    ctx.scale(rx, ry)
    ctx.arc_negative(0, 0, 1, math.pi, 0)
    ctx.restore()
    ctx.line_to(cx + rx, top)
    ctx.close_path()
    g = cairo.LinearGradient(cx - rx, 0, cx + rx, 0)
    g.add_color_stop_rgba(0, color[0] * 0.35, color[1] * 0.35, color[2] * 0.45, 0.95 * alpha)
    g.add_color_stop_rgba(0.5, color[0] * 0.55, color[1] * 0.55, color[2] * 0.65, 0.95 * alpha)
    g.add_color_stop_rgba(1, color[0] * 0.3, color[1] * 0.3, color[2] * 0.4, 0.95 * alpha)
    ctx.set_source(g)
    ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(2.5)
    ctx.stroke()
    # faixas
    for k in (1 / 3, 2 / 3):
        y = lerp(top, bot, k)
        ctx.save()
        ctx.translate(cx, y)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, math.pi)
        ctx.restore()
        rgba(ctx, color, 0.55 * alpha)
        ctx.set_line_width(2)
        ctx.stroke()
    ell(top)
    rgba(ctx, mix(color, WHITE, 0.15), 0.9 * alpha)
    ctx.fill_preserve()
    rgba(ctx, WHITE, 0.6 * alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    if fill_u > 0:
        glow(ctx, cx, top, w * 0.6, WHITE, 0.5 * fill_u * alpha)
    if label:
        text(ctx, label, cx, cy + h * 0.12, min(30, w * 0.16), WHITE, bold=True, align="center",
             alpha=alpha, middle=True)
    if sub:
        text(ctx, sub, cx, cy + h / 2 + 34, 20, MUTED, align="center", alpha=alpha)


def icon_laptop(ctx, cx, cy, w, color=CYAN, alpha=1.0, screen=None):
    h = w * 0.62
    x, y = cx - w / 2, cy - h / 2
    rrect(ctx, x, y, w, h, 12)
    ctx.set_source_rgba(0.04, 0.09, 0.18, alpha)
    ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(3)
    ctx.stroke()
    # base
    ctx.move_to(x - w * 0.08, y + h + 4)
    ctx.line_to(x + w * 1.08, y + h + 4)
    ctx.line_to(x + w * 1.0, y + h + w * 0.07)
    ctx.line_to(x, y + h + w * 0.07)
    ctx.close_path()
    rgba(ctx, color, 0.8 * alpha)
    ctx.fill()
    if screen:
        screen(ctx, x + 10, y + 10, w - 20, h - 20)
    else:
        for i in range(3):
            rrect(ctx, x + w * 0.12, y + h * (0.25 + 0.2 * i), w * (0.6 - 0.12 * i), h * 0.08, 4)
            rgba(ctx, color, 0.45 * alpha)
            ctx.fill()


def icon_server(ctx, cx, cy, w, h, color=PG, t=0.0, alpha=1.0):
    n = 3
    uh = (h - 10 * (n - 1)) / n
    for i in range(n):
        y = cy - h / 2 + i * (uh + 10)
        rrect(ctx, cx - w / 2, y, w, uh, 8)
        ctx.set_source_rgba(0.05, 0.11, 0.21, alpha)
        ctx.fill_preserve()
        rgba(ctx, color, alpha)
        ctx.set_line_width(2.5)
        ctx.stroke()
        for j in range(3):
            on = 0.5 + 0.5 * math.sin(t * 5 + i * 1.7 + j * 2.3)
            ctx.arc(cx + w / 2 - 22 - j * 18, y + uh / 2, 4.5, 0, 2 * math.pi)
            rgba(ctx, GREEN if j == 0 else CYAN, alpha * (0.35 + 0.65 * on))
            ctx.fill()
        rrect(ctx, cx - w / 2 + 16, y + uh / 2 - 3, w * 0.35, 6, 3)
        rgba(ctx, color, 0.5 * alpha)
        ctx.fill()


def icon_person(ctx, cx, cy, s, color=CYAN, alpha=1.0, medic=False):
    ctx.new_path()
    ctx.arc(cx, cy - s * 0.28, s * 0.2, 0, 2 * math.pi)
    rgba(ctx, color, alpha)
    ctx.fill()
    ctx.save()
    ctx.translate(cx, cy + s * 0.32)
    ctx.scale(s * 0.38, s * 0.3)
    ctx.arc(0, 0, 1, math.pi, 2 * math.pi)
    ctx.restore()
    ctx.close_path()
    ctx.fill()
    if medic:
        k = s * 0.07
        ctx.rectangle(cx - k / 2, cy + s * 0.12 - k * 1.5, k, k * 3)
        ctx.rectangle(cx - k * 1.5, cy + s * 0.12 - k / 2, k * 3, k)
        rgba(ctx, RED, alpha)
        ctx.fill()


def icon_cross(ctx, cx, cy, s, color=RED, alpha=1.0):
    k = s / 3
    rrect(ctx, cx - k / 2, cy - s / 2, k, s, 3)
    rrect(ctx, cx - s / 2, cy - k / 2, s, k, 3)
    rgba(ctx, color, alpha)
    ctx.fill()


def icon_ambulance(ctx, cx, cy, w, t=0.0, alpha=1.0, lights=True):
    h = w * 0.42
    x, y = cx - w / 2, cy - h / 2
    # caixa traseira
    rrect(ctx, x, y, w * 0.68, h, 10)
    ctx.set_source_rgba(0.95, 0.97, 1, alpha)
    ctx.fill()
    # cabine
    ctx.move_to(x + w * 0.68, y + h * 0.22)
    ctx.line_to(x + w * 0.86, y + h * 0.22)
    ctx.line_to(x + w, y + h * 0.55)
    ctx.line_to(x + w, y + h - 8)
    ctx.line_to(x + w * 0.68, y + h - 8)
    ctx.close_path()
    ctx.set_source_rgba(0.9, 0.93, 0.98, alpha)
    ctx.fill()
    ctx.move_to(x + w * 0.72, y + h * 0.3)
    ctx.line_to(x + w * 0.85, y + h * 0.3)
    ctx.line_to(x + w * 0.95, y + h * 0.52)
    ctx.line_to(x + w * 0.72, y + h * 0.52)
    ctx.close_path()
    rgba(ctx, hexc("7DD3FC"), alpha)
    ctx.fill()
    # faixa
    ctx.rectangle(x, y + h * 0.62, w, h * 0.09)
    rgba(ctx, RED, alpha)
    ctx.fill()
    icon_cross(ctx, x + w * 0.34, y + h * 0.36, h * 0.38, RED, alpha)
    # rodas
    for wx in (x + w * 0.2, x + w * 0.8):
        ctx.arc(wx, y + h, h * 0.2, 0, 2 * math.pi)
        ctx.set_source_rgba(0.1, 0.12, 0.16, alpha)
        ctx.fill()
        ctx.arc(wx, y + h, h * 0.09, 0, 2 * math.pi)
        ctx.set_source_rgba(0.7, 0.75, 0.82, alpha)
        ctx.fill()
    if lights:
        on = (math.sin(t * 9) > 0)
        for i, c in enumerate((RED, BLUE)):
            lit = on if i == 0 else not on
            rrect(ctx, x + w * 0.22 + i * w * 0.14, y - h * 0.1, w * 0.12, h * 0.1, 4)
            rgba(ctx, c, alpha * (1 if lit else 0.35))
            ctx.fill()
            if lit:
                glow(ctx, x + w * 0.28 + i * w * 0.14, y - h * 0.05, w * 0.18, c, 0.5 * alpha)


def icon_doc(ctx, cx, cy, w, h, color=WHITE, alpha=1.0, lines_u=1.0, badge="PDF", fill=True):
    x, y = cx - w / 2, cy - h / 2
    f = w * 0.22
    ctx.move_to(x + 8, y)
    ctx.line_to(x + w - f, y)
    ctx.line_to(x + w, y + f)
    ctx.line_to(x + w, y + h - 8)
    ctx.arc(x + w - 8, y + h - 8, 8, 0, math.pi / 2)
    ctx.line_to(x + 8, y + h)
    ctx.arc(x + 8, y + h - 8, 8, math.pi / 2, math.pi)
    ctx.line_to(x, y + 8)
    ctx.arc(x + 8, y + 8, 8, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    if fill:
        ctx.set_source_rgba(0.96, 0.97, 1, alpha)
        ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    n = 6
    for i in range(n):
        u = clamp(lines_u * n - i)
        if u <= 0:
            break
        ly = y + h * 0.28 + i * h * 0.1
        ctx.rectangle(x + w * 0.14, ly, (w * (0.72 if i % 3 else 0.5)) * u, h * 0.035)
        ctx.set_source_rgba(0.35, 0.45, 0.6, alpha)
        ctx.fill()
    if badge:
        rrect(ctx, x - w * 0.12, y + h * 0.72, w * 0.62, h * 0.18, 6)
        rgba(ctx, RED, alpha)
        ctx.fill()
        text(ctx, badge, x - w * 0.12 + w * 0.31, y + h * 0.81, h * 0.11, WHITE, bold=True,
             align="center", alpha=alpha, middle=True)


def icon_envelope(ctx, cx, cy, w, color=CYAN, alpha=1.0):
    h = w * 0.66
    x, y = cx - w / 2, cy - h / 2
    rrect(ctx, x, y, w, h, 8)
    ctx.set_source_rgba(0.95, 0.97, 1, alpha)
    ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.move_to(x + 4, y + 6)
    ctx.line_to(cx, cy + h * 0.1)
    ctx.line_to(x + w - 4, y + 6)
    ctx.stroke()


def icon_lock(ctx, cx, cy, s, color=CYAN, alpha=1.0):
    ctx.new_path()
    ctx.arc(cx, cy - s * 0.12, s * 0.24, math.pi, 2 * math.pi)
    rgba(ctx, color, alpha)
    ctx.set_line_width(s * 0.09)
    ctx.stroke()
    rrect(ctx, cx - s * 0.36, cy - s * 0.12, s * 0.72, s * 0.55, s * 0.08)
    ctx.fill()
    ctx.arc(cx, cy + s * 0.12, s * 0.07, 0, 2 * math.pi)
    ctx.set_source_rgba(0.04, 0.09, 0.18, alpha)
    ctx.fill()


def icon_shield(ctx, cx, cy, s, color=CYAN, alpha=1.0):
    ctx.move_to(cx, cy - s / 2)
    ctx.curve_to(cx + s * 0.25, cy - s * 0.38, cx + s * 0.42, cy - s * 0.38, cx + s * 0.42, cy - s * 0.38)
    ctx.curve_to(cx + s * 0.42, cy + s * 0.1, cx + s * 0.25, cy + s * 0.38, cx, cy + s / 2)
    ctx.curve_to(cx - s * 0.25, cy + s * 0.38, cx - s * 0.42, cy + s * 0.1, cx - s * 0.42, cy - s * 0.38)
    ctx.curve_to(cx - s * 0.42, cy - s * 0.38, cx - s * 0.25, cy - s * 0.38, cx, cy - s / 2)
    ctx.close_path()
    rgba(ctx, color, 0.2 * alpha)
    ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(3)
    ctx.stroke()


def icon_gear(ctx, cx, cy, r, ang=0.0, color=CYAN, alpha=1.0):
    ctx.new_path()
    n = 8
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang)
    for i in range(n * 2):
        a0 = i * math.pi / n
        rr = r if i % 2 == 0 else r * 0.78
        ctx.arc(0, 0, rr, a0, a0 + math.pi / n)
    ctx.close_path()
    rgba(ctx, color, alpha)
    ctx.fill()
    ctx.arc(0, 0, r * 0.35, 0, 2 * math.pi)
    ctx.set_source_rgba(0.06, 0.13, 0.25, alpha)
    ctx.fill()
    ctx.restore()


def icon_heart(ctx, cx, cy, s, color=RED, alpha=1.0):
    ctx.move_to(cx, cy + s * 0.35)
    ctx.curve_to(cx - s * 0.6, cy - s * 0.05, cx - s * 0.3, cy - s * 0.55, cx, cy - s * 0.2)
    ctx.curve_to(cx + s * 0.3, cy - s * 0.55, cx + s * 0.6, cy - s * 0.05, cx, cy + s * 0.35)
    rgba(ctx, color, alpha)
    ctx.fill()


def ecg(ctx, x0, y0, w, h, t, color=GREEN, alpha=1.0, speed=260, period=260, width=3):
    """Traçado de ECG rolando da direita para a esquerda."""
    ctx.save()
    ctx.rectangle(x0, y0 - h, w, h * 2)
    ctx.clip()
    ctx.push_group()
    off = (t * speed) % period
    pts = []
    x = x0 - period + off
    while x < x0 + w + period:
        b = x
        pts += [(b, y0), (b + period * 0.35, y0), (b + period * 0.4, y0 - h * 0.15),
                (b + period * 0.45, y0), (b + period * 0.5, y0 + h * 0.18),
                (b + period * 0.54, y0 - h * 0.95), (b + period * 0.58, y0 + h * 0.4),
                (b + period * 0.62, y0), (b + period * 0.75, y0 - h * 0.2), (b + period * 0.85, y0)]
        x += period
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    rgba(ctx, color, alpha)
    ctx.set_line_width(width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    pat = ctx.pop_group()
    m = cairo.LinearGradient(x0, 0, x0 + w, 0)
    fe = min(0.15, 70 / w)
    m.add_color_stop_rgba(0, 0, 0, 0, 0)
    m.add_color_stop_rgba(fe, 0, 0, 0, 1)
    m.add_color_stop_rgba(1 - fe, 0, 0, 0, 1)
    m.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(pat)
    ctx.mask(m)
    ctx.restore()


def icon_pill(ctx, cx, cy, s, alpha=1.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-0.6)
    rrect(ctx, -s / 2, -s * 0.2, s, s * 0.4, s * 0.2)
    ctx.clip()
    ctx.rectangle(-s / 2, -s * 0.2, s / 2, s * 0.4)
    rgba(ctx, CYAN, alpha)
    ctx.fill()
    ctx.rectangle(0, -s * 0.2, s / 2, s * 0.4)
    rgba(ctx, WHITE, alpha)
    ctx.fill()
    ctx.restore()


def icon_triage(ctx, cx, cy, s, alpha=1.0):
    cols = [RED, ORANGE, hexc("FACC15"), GREEN, BLUE]
    bw = s / 5
    for i, c in enumerate(cols):
        rrect(ctx, cx - s / 2 + i * bw + 3, cy - s * 0.3 + (i % 2) * 0, bw - 6, s * 0.6, 6)
        rgba(ctx, c, alpha)
        ctx.fill()


def icon_gcs(ctx, cx, cy, s, alpha=1.0):
    ctx.arc(cx, cy, s * 0.45, 0, 2 * math.pi)
    rgba(ctx, PURPLE, 0.2 * alpha)
    ctx.fill_preserve()
    rgba(ctx, PURPLE, alpha)
    ctx.set_line_width(4)
    ctx.stroke()
    text(ctx, "GCS", cx, cy - s * 0.06, s * 0.26, WHITE, bold=True, align="center", alpha=alpha,
         middle=True)
    text(ctx, "3–15", cx, cy + s * 0.24, s * 0.15, MUTED, align="center", alpha=alpha, middle=True)


def icon_browser(ctx, cx, cy, w, color=CYAN, alpha=1.0):
    h = w * 0.68
    x, y = cx - w / 2, cy - h / 2
    rrect(ctx, x, y, w, h, 10)
    ctx.set_source_rgba(0.04, 0.09, 0.18, alpha)
    ctx.fill_preserve()
    rgba(ctx, color, alpha)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.move_to(x, y + h * 0.22)
    ctx.line_to(x + w, y + h * 0.22)
    ctx.stroke()
    for i in range(3):
        ctx.arc(x + 12 + i * 12, y + h * 0.11, 3.5, 0, 2 * math.pi)
        ctx.fill()
    for i in range(3):
        rrect(ctx, x + w * 0.12, y + h * (0.38 + 0.17 * i), w * 0.76, h * 0.08, 3)
        rgba(ctx, color, 0.4 * alpha)
        ctx.fill()


def icon_jwt(ctx, cx, cy, w, alpha=1.0, label="JWT"):
    h = w * 0.42
    x, y = cx - w / 2, cy - h / 2
    rrect(ctx, x, y, w, h, h * 0.3)
    ctx.set_source_rgba(0.05, 0.1, 0.2, alpha)
    ctx.fill_preserve()
    rgba(ctx, PURPLE, alpha)
    ctx.set_line_width(2.5)
    ctx.stroke()
    for i, c in enumerate((RED, PURPLE, CYAN)):
        rrect(ctx, x + w * 0.1 + i * w * 0.27, y + h * 0.66, w * 0.22, h * 0.14, 3)
        rgba(ctx, c, alpha)
        ctx.fill()
    text(ctx, label, cx, y + h * 0.38, h * 0.36, WHITE, bold=True, align="center", alpha=alpha,
         middle=True)


def icon_sync(ctx, cx, cy, r, ang=0.0, color=CYAN, alpha=1.0):
    ctx.new_path()
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang)
    for k in (0, math.pi):
        ctx.arc(0, 0, r, k + 0.3, k + math.pi - 0.3)
        rgba(ctx, color, alpha)
        ctx.set_line_width(r * 0.18)
        ctx.stroke()
        ex, ey = r * math.cos(k + math.pi - 0.3), r * math.sin(k + math.pi - 0.3)
        a = k + math.pi - 0.3 + math.pi / 2
        s = r * 0.42
        ctx.move_to(ex + s * math.cos(a), ey + s * math.sin(a))
        ctx.line_to(ex + s * 0.7 * math.cos(a - 2.3), ey + s * 0.7 * math.sin(a - 2.3))
        ctx.line_to(ex + s * 0.7 * math.cos(a + 2.3), ey + s * 0.7 * math.sin(a + 2.3))
        ctx.close_path()
        ctx.fill()
    ctx.restore()


def logo_mark(ctx, cx, cy, s, t=0.0, alpha=1.0):
    """Emblema: quadrado arredondado com cruz e traçado de ECG."""
    glow(ctx, cx, cy, s * 1.1, CYAN, 0.35 * alpha)
    rrect(ctx, cx - s / 2, cy - s / 2, s, s, s * 0.26)
    g = cairo.LinearGradient(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
    g.add_color_stop_rgba(0, 0.22, 0.74, 0.97, alpha)
    g.add_color_stop_rgba(1, 0.15, 0.39, 0.92, alpha)
    ctx.set_source(g)
    ctx.fill()
    icon_cross(ctx, cx, cy, s * 0.56, WHITE, alpha)
    pts = [(cx - s * 0.42, cy + s * 0.05), (cx - s * 0.16, cy + s * 0.05), (cx - s * 0.08, cy - s * 0.18),
           (cx + s * 0.02, cy + s * 0.26), (cx + s * 0.1, cy + s * 0.05), (cx + s * 0.42, cy + s * 0.05)]
    arrow(ctx, pts, hexc("1D4ED8"), u=1, width=s * 0.06, alpha=alpha, head=False)


def logo(ctx, cx, cy, size, t=0.0, alpha=1.0, sub=None):
    mark = size * 1.25
    font(ctx, size, True)
    w1 = ctx.text_extents("Medical").x_advance
    w2 = ctx.text_extents("Field").x_advance
    total = mark + size * 0.4 + w1 + w2
    x = cx - total / 2
    logo_mark(ctx, x + mark / 2, cy, mark, t, alpha)
    tx = x + mark + size * 0.4
    text(ctx, "Medical", tx, cy, size, WHITE, bold=True, alpha=alpha, middle=True)
    text(ctx, "Field", tx + w1, cy, size, CYAN, bold=True, alpha=alpha, middle=True)
    if sub:
        text(ctx, sub, cx, cy + size * 1.25, size * 0.36, MUTED, align="center", alpha=alpha)


# ---------------------------------------------------------------- fundo
def make_background():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *BG_TOP)
    g.add_color_stop_rgba(1, *BG_BOT)
    ctx.set_source(g)
    ctx.paint()
    # brilho difuso
    for (x, y, r, c, a) in ((300, 150, 900, BLUE, 0.10), (1700, 900, 1000, CYAN, 0.07)):
        glow(ctx, x, y, r, c, a)
    # grade de pontos
    ctx.set_source_rgba(1, 1, 1, 0.035)
    for x in range(24, W, 48):
        for y in range(24, H, 48):
            ctx.arc(x, y, 1.3, 0, 2 * math.pi)
            ctx.fill()
    # vinheta
    v = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05)
    v.add_color_stop_rgba(0, 0, 0, 0, 0)
    v.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    ctx.set_source(v)
    ctx.paint()
    return surf


_rng = random.Random(7)
PARTICLES = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(4, 14), _rng.uniform(0, 6.28),
              _rng.uniform(0.8, 2.4)) for _ in range(70)]


def particles(ctx, t):
    for (x, y, sp, ph, r) in PARTICLES:
        px = (x + t * sp) % W
        py = (y - t * sp * 0.6) % H
        a = 0.08 + 0.1 * (0.5 + 0.5 * math.sin(t * 0.8 + ph))
        ctx.arc(px, py, r, 0, 2 * math.pi)
        ctx.set_source_rgba(0.5, 0.8, 1, a)
        ctx.fill()
