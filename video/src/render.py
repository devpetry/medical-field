"""Renderiza o vídeo a partir de timeline.json.

Uso:
  python render.py <timeline.json> <saida_dir> --preview 12.5 40 ...   (PNGs de quadros)
  python render.py <timeline.json> <saida_dir> --video [--workers 14]  (partes .mp4 + concat)
"""
import argparse
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import cairo
import imageio_ffmpeg

from draw import (CYAN, MUTED, W, H, WHITE, clamp, layer, logo, make_background, particles,
                  prog, rrect, text, wrap)
from scenes import SCENES

FPS = 30
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


class Scene:
    def __init__(self, d):
        self.id, self.label, self.start, self.T = d["id"], d["label"], d["start"], d["dur"]
        self.c = [s["start"] for s in d["segs"]]
        self.e = [s["start"] + s["dur"] for s in d["segs"]]


def subtitle_cues(tl):
    """Divide cada frase em blocos de até 2 linhas, com tempo proporcional ao texto."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
    ctx = cairo.Context(surf)
    cues = []
    for sc in tl["scenes"]:
        for sg in sc["segs"]:
            lines = wrap(ctx, sg["text"], 38, 1500)
            blocks = [lines[i:i + 2] for i in range(0, len(lines), 2)]
            total = sum(len(" ".join(b)) for b in blocks)
            t0 = sc["start"] + sg["start"]
            for b in blocks:
                d = sg["dur"] * len(" ".join(b)) / total
                cues.append((t0, t0 + d, b))
                t0 += d
    return cues


def draw_subtitle(ctx, t, cues):
    for (a, b, lines) in cues:
        if a - 0.05 <= t <= b + 0.15:
            al = min(clamp((t - a + 0.05) / 0.12), clamp((b + 0.15 - t) / 0.12))
            n = len(lines)
            h = 30 + n * 50
            y0 = H - 40 - h
            from draw import text_w
            wmax = max(text_w(ctx, ln, 38) for ln in lines) + 60
            rrect(ctx, W / 2 - wmax / 2, y0, wmax, h, 16)
            ctx.set_source_rgba(0.02, 0.05, 0.1, 0.78 * al)
            ctx.fill()
            for i, ln in enumerate(lines):
                text(ctx, ln, W / 2, y0 + 15 + 25 + i * 50, 38, WHITE, align="center", alpha=al,
                     middle=True)
            return


def draw_header(ctx, sc, idx, t, alpha):
    if idx in (0, len(SCENES) - 1) or alpha <= 0:
        return
    text(ctx, f"{idx + 1:02d}", 60, 68, 26, CYAN, bold=True, alpha=alpha)
    text(ctx, sc.label, 106, 68, 26, WHITE, bold=True, alpha=alpha * 0.9)
    with layer(ctx, alpha * 0.85):
        logo(ctx, 1740, 58, 22, t)


class Renderer:
    def __init__(self, tl_path):
        self.tl = json.loads(Path(tl_path).read_text())
        self.scenes = [Scene(s) for s in self.tl["scenes"]]
        self.cues = subtitle_cues(self.tl)
        self.total = self.tl["total"]
        self.nframes = int(math.ceil(self.total * FPS))
        self.bg = None

    def frame(self, n):
        if self.bg is None:
            self.bg = make_background()
        t = n / FPS
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        ctx.set_source_surface(self.bg, 0, 0)
        ctx.paint()
        particles(ctx, t)
        idx = len(self.scenes) - 1
        for i, sc in enumerate(self.scenes):
            if t < sc.start + sc.T:
                idx = i
                break
        sc = self.scenes[idx]
        lt = t - sc.start
        fade = min(prog(lt, 0, 0.6), 1 - prog(lt, sc.T - 0.55, 0.55))
        if idx == len(self.scenes) - 1:
            fade = min(prog(lt, 0, 0.6), 1 - prog(lt, sc.T - 1.2, 1.2))
        with layer(ctx, fade):
            SCENES[idx](ctx, lt, sc)
        draw_header(ctx, sc, idx, t, fade)
        draw_subtitle(ctx, t, self.cues)
        surf.flush()
        return surf


_R = None


def _init(tl_path):
    global _R
    _R = Renderer(tl_path)


def _render_part(args):
    k, a, b, out = args
    cmd = [FFMPEG, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "17", "-pix_fmt", "yuv420p", "-threads", "2", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(a, b):
        p.stdin.write(bytes(_R.frame(n).get_data()))
    p.stdin.close()
    p.wait()
    return k, p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("out")
    ap.add_argument("--preview", nargs="*", type=float)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 2))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.preview:
        r = Renderer(args.timeline)
        for s in args.preview:
            r.frame(int(s * FPS)).write_to_png(str(out / f"preview_{s:07.2f}.png"))
        print("ok", len(args.preview))
        return
    if args.video:
        r = Renderer(args.timeline)
        n = r.nframes
        chunk = 300
        jobs = [(k, a, min(a + chunk, n), str(out / f"part_{k:04d}.mp4"))
                for k, a in enumerate(range(0, n, chunk))]
        with Pool(args.workers, initializer=_init, initargs=(args.timeline,)) as pool:
            for k, rc in pool.imap_unordered(_render_part, jobs):
                if rc != 0:
                    sys.exit(f"falha na parte {k}")
                print(f"parte {k + 1}/{len(jobs)}", flush=True)
        (out / "parts.txt").write_text("".join(f"file '{Path(j[3]).name}'\n" for j in jobs))
        subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                        str(out / "parts.txt"), "-c", "copy", str(out / "video_mudo.mp4")], check=True)
        print("video_mudo.mp4 pronto")


if __name__ == "__main__":
    main()
