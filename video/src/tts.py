"""Gera a narração de cada segmento com Piper e monta a linha do tempo.

Uso: python tts.py <modelo.onnx> <pasta_saida>
Saída: <pasta_saida>/seg_<cena>_<n>.wav e timeline.json
"""
import json
import sys
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

from narration import SCENES, phonetic

SCENE_PAD_IN = 0.9    # silêncio no início de cada cena (s)
SCENE_PAD_OUT = 1.1   # silêncio no fim de cada cena (s)
GAP = 0.45            # pausa entre frases (s)


def main(model, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    voice = PiperVoice.load(model)
    cfg = SynthesisConfig(length_scale=1.04, noise_scale=0.6, noise_w_scale=0.8)
    rate = voice.config.sample_rate

    timeline = {"sample_rate": rate, "scenes": []}
    t = 0.0
    for si, sc in enumerate(SCENES):
        scene = {"id": sc["id"], "label": sc["label"], "start": t, "segs": []}
        local = SCENE_PAD_IN
        for gi, (text, visual) in enumerate(sc["segs"]):
            path = out / f"seg_{si}_{gi:02d}.wav"
            with wave.open(str(path), "wb") as wf:
                voice.synthesize_wav(phonetic(text), wf, syn_config=cfg)
            with wave.open(str(path), "rb") as wf:
                dur = wf.getnframes() / wf.getframerate()
            scene["segs"].append({"text": text, "visual": visual, "wav": path.name,
                                  "start": local, "dur": dur})
            local += dur + GAP
        scene["dur"] = local - GAP + SCENE_PAD_OUT
        t += scene["dur"]
        timeline["scenes"].append(scene)
        print(f"{sc['id']}: {scene['dur']:.1f}s", flush=True)
    timeline["total"] = t
    (out / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))
    print(f"total: {t:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
