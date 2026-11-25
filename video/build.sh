#!/usr/bin/env bash
# Gera o vídeo explicativo do MedicalField do zero.
# Requisitos: python3 com pycairo; o script cria um venv com piper-tts, numpy e imageio-ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
WORK=${WORK:-build}
VOICE=${VOICE:-pt_BR-faber-medium}
mkdir -p "$WORK/voice"

if [ ! -x "$WORK/venv/bin/python" ]; then
  python3 -m venv --system-site-packages "$WORK/venv"
  "$WORK/venv/bin/pip" install -q piper-tts numpy imageio-ffmpeg
fi
PY="$WORK/venv/bin/python"

if [ ! -f "$WORK/voice/$VOICE.onnx" ]; then
  base=https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/${VOICE#pt_BR-}
  base=${base%-medium}/medium
  curl -sSL -o "$WORK/voice/$VOICE.onnx" "$base/$VOICE.onnx"
  curl -sSL -o "$WORK/voice/$VOICE.onnx.json" "$base/$VOICE.onnx.json"
fi

cd src
"$PY" tts.py "../$WORK/voice/$VOICE.onnx" "../$WORK/audio"
"$PY" audio.py "../$WORK/audio/timeline.json" "../$WORK/audio" "../$WORK/mix"
"$PY" render.py "../$WORK/audio/timeline.json" "../$WORK/video" --video
"$PY" deliver.py "../$WORK/audio/timeline.json" "../$WORK/video/video_mudo.mp4" \
  "../$WORK/mix/narracao.wav" "../$WORK/mix/musica.wav" ..
