"""Gera legendas .srt, o roteiro/storyboard em Markdown e o MP4 final.

Uso: python deliver.py <timeline.json> <video_mudo.mp4> <narracao.wav> <musica.wav> <saida_dir>
"""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

from render import subtitle_cues

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def ts(x, sep=","):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s % 1) * 1000)) % 1000:03d}"


def mmss(x):
    return f"{int(x // 60)}:{int(x % 60):02d}"


def write_srt(tl, path):
    out = []
    for i, (a, b, lines) in enumerate(subtitle_cues(tl), 1):
        out.append(f"{i}\n{ts(a)} --> {ts(b)}\n" + "\n".join(lines) + "\n")
    path.write_text("\n".join(out), encoding="utf-8")


def write_script(tl, path):
    md = ["# MedicalField — roteiro, narração e storyboard", "",
          f"Duração total: {mmss(tl['total'])} · 1920 × 1080 · 30 fps · narração pt-BR", ""]
    for i, sc in enumerate(tl["scenes"], 1):
        md += [f"## Cena {i} — {sc['label']} ({mmss(sc['start'])} – {mmss(sc['start'] + sc['dur'])})", "",
               "| Tempo | Narração | Na tela |", "| --- | --- | --- |"]
        for sg in sc["segs"]:
            md.append(f"| {mmss(sc['start'] + sg['start'])} | {sg['text']} | {sg['visual']} |")
        md.append("")
    path.write_text("\n".join(md), encoding="utf-8")


def main(tl_path, video, voice, music, out_dir):
    tl = json.loads(Path(tl_path).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    srt = out / "MedicalField_legendas_pt-BR.srt"
    write_srt(tl, srt)
    write_script(tl, out / "MedicalField_roteiro.md")
    final = out / "MedicalField_video_explicativo.mp4"
    subprocess.run([
        FFMPEG, "-loglevel", "error", "-y",
        "-i", video, "-i", voice, "-i", music,
        "-filter_complex",
        "[1:a]aformat=channel_layouts=stereo[v];[v][2:a]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.95[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-metadata:s:a:0", "language=por", "-metadata", "title=MedicalField — vídeo explicativo",
        "-shortest", "-movflags", "+faststart", str(final)], check=True)
    print(final)


if __name__ == "__main__":
    main(*sys.argv[1:6])
