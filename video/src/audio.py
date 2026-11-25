"""Monta a trilha: narração posicionada na linha do tempo + música ambiente
sintetizada (sem samples externos), com abaixamento da música sob a voz.

Uso: python audio.py <timeline.json> <pasta_wavs> <saida_dir>
Saída: narracao.wav (mono) e musica.wav (estéreo), ambos 48 kHz.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000


def read_wav(path):
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:  # reamostragem por interpolação com filtro passa-baixa simples
        n = int(len(data) * SR / sr)
        x = np.linspace(0, len(data) - 1, n)
        data = np.interp(x, np.arange(len(data)), data).astype(np.float32)
        k = np.array([0.25, 0.5, 0.25], dtype=np.float32)
        data = np.convolve(data, k, mode="same")
    return data


def write_wav(path, data):
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype(np.int16)
    ch = 1 if pcm.ndim == 1 else pcm.shape[1]
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(ch)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def narration(tl, wav_dir, n):
    out = np.zeros(n, dtype=np.float32)
    for sc in tl["scenes"]:
        for sg in sc["segs"]:
            v = read_wav(Path(wav_dir) / sg["wav"])
            # fade curto nas pontas para evitar estalos
            f = min(240, len(v) // 4)
            v[:f] *= np.linspace(0, 1, f)
            v[-f:] *= np.linspace(1, 0, f)
            a = int((sc["start"] + sg["start"]) * SR)
            b = min(n, a + len(v))
            out[a:b] += v[:b - a]
    # normaliza para pico de -1 dBFS
    return out * (0.89 / max(1e-6, np.abs(out).max()))


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music(n):
    t = np.arange(n, dtype=np.float32) / SR
    L = np.zeros(n, dtype=np.float32)
    R = np.zeros(n, dtype=np.float32)
    bpm = 80
    beat = 60 / bpm
    bar = beat * 4
    chord_len = bar * 2
    # Dmaj9 – Bm7 – Gmaj7 – A6sus (calmo, tecnológico)
    chords = [[50, 57, 62, 64, 66, 69], [47, 54, 59, 62, 66, 69], [43, 50, 55, 59, 62, 66],
              [45, 52, 57, 61, 64, 66]]
    n_ch = int(np.ceil(n / SR / chord_len)) + 1
    rng = np.random.default_rng(3)
    for k in range(n_ch):
        notes = chords[k % 4]
        t0 = k * chord_len
        a = int(max(0, (t0 - 1.5) * SR))
        b = int(min(n, (t0 + chord_len + 2.5) * SR))
        if a >= b:
            continue
        tt = t[a:b] - t0
        env = np.clip((tt + 1.5) / 2.5, 0, 1) * np.clip((chord_len + 2.5 - tt) / 3.0, 0, 1)
        env = env ** 1.5
        # pad: senoides levemente desafinadas + 3º harmônico suave
        for i, m in enumerate(notes):
            f = midi(m + 12 if i == 0 else m)
            for det, pan in ((-0.12, 0.25), (0.12, 0.75)):
                ff = f * 2 ** (det / 12)
                ph = rng.uniform(0, 6.28)
                w = np.sin(2 * np.pi * ff * tt + ph) + 0.18 * np.sin(2 * np.pi * 3 * ff * tt + ph)
                trem = 1 + 0.15 * np.sin(2 * np.pi * 0.11 * tt + i)
                sig = (0.045 * env * trem * w).astype(np.float32)
                L[a:b] += sig * (1 - pan)
                R[a:b] += sig * pan
        # baixo
        fb = midi(notes[0] - 12)
        sig = (0.11 * env * np.sin(2 * np.pi * fb * tt)).astype(np.float32)
        L[a:b] += sig
        R[a:b] += sig
        # arpejo suave em colcheias
        arp = [notes[2] + 12, notes[3] + 12, notes[4] + 12, notes[5] + 12]
        steps = int(chord_len / (beat / 2))
        for s in range(steps):
            if s % 8 in (3, 7) or rng.random() < 0.2:
                continue
            ts = t0 + s * beat / 2
            ia = int(ts * SR)
            ib = min(n, ia + int(1.6 * SR))
            if ia >= n or ia < 0:
                continue
            tn = t[ia:ib] - ts
            f = midi(arp[s % 4])
            e = np.exp(-tn * 3.2) * np.clip(tn / 0.005, 0, 1)
            sig = (0.035 * e * (np.sin(2 * np.pi * f * tn) + 0.3 * np.sin(4 * np.pi * f * tn))).astype(np.float32)
            pan = 0.3 if s % 2 else 0.7
            L[ia:ib] += sig * (1 - pan)
            R[ia:ib] += sig * pan
    # eco estéreo
    d = int(beat * 0.75 * SR)
    L2, R2 = L.copy(), R.copy()
    L2[d:] += 0.28 * R[:-d]
    R2[d:] += 0.28 * L[:-d]
    st = np.stack([L2, R2], axis=1)
    # entrada e saída
    fi, fo = int(3 * SR), int(5 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st / np.abs(st).max()


def duck(voice, n):
    """Ganho da música: mais baixo enquanto há fala, com ataque/soltura suaves."""
    hop = SR // 100
    frames = len(voice) // hop + 1
    env = np.zeros(frames, dtype=np.float32)
    for i in range(frames):
        seg = voice[i * hop:(i + 1) * hop]
        env[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    act = (env > 0.01).astype(np.float32)
    # segura 400 ms e suaviza
    hold = np.convolve(act, np.ones(40), mode="same") > 0
    g = np.where(hold, 0.12, 0.30).astype(np.float32)
    sm = np.convolve(g, np.ones(35) / 35, mode="same")
    return np.interp(np.arange(n) / hop, np.arange(frames), sm).astype(np.float32)


def main(tl_path, wav_dir, out_dir):
    tl = json.loads(Path(tl_path).read_text())
    n = int(np.ceil(tl["total"] * SR)) + SR
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    v = narration(tl, wav_dir, n)
    write_wav(out / "narracao.wav", v)
    m = music(n) * duck(v, n)[:, None]
    write_wav(out / "musica.wav", m)
    rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    speech = np.abs(v) > 0.02
    print(f"voz RMS (com fala): {rms(v[speech]):.1f} dBFS")
    print(f"música RMS sob a voz: {rms(m[speech]):.1f} dBFS · nas pausas: {rms(m[~speech]):.1f} dBFS")


if __name__ == "__main__":
    main(*sys.argv[1:4])
