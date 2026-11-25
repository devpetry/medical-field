#!/usr/bin/env bash
# Gera os PNG (3840x2160, 16:9) a partir das páginas em fontes/*.html, com o Chrome/Chromium em modo headless.
# Uso: ./gerar.sh          (todos)
#      ./gerar.sh 06       (só os que têm 06 no nome)
# Para editar um diagrama, abra o .html no navegador; as setas são desenhadas pelo fontes/base.js.
set -euo pipefail
cd "$(dirname "$0")"
chrome=$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)
[ -n "$chrome" ] || { echo "Instale o Google Chrome ou o Chromium."; exit 1; }

for html in fontes/*.html; do
  nome=$(basename "$html" .html)
  [ -n "${1:-}" ] && [[ "$nome" != *"$1"* ]] && continue
  "$chrome" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=1920,1080 --virtual-time-budget=3000 \
    --screenshot="$PWD/$nome.png" "file://$PWD/$html" >/dev/null 2>&1
  echo "  $nome.png"
done
