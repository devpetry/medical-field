#!/usr/bin/env bash
# Abre o cliente MedicalField em qualquer Linux, mesmo sem a biblioteca FUSE (Ubuntu 22.04+ não a
# instala) e com o sandbox do Chromium bloqueado pelo AppArmor (Ubuntu 24.04+). Basta deixar este
# script na mesma pasta do .AppImage e rodar: ./abrir-medicalfield.sh
# Argumentos extras são repassados: ./abrir-medicalfield.sh --api=http://<ip>/api --dispositivo=amb-03
set -e
cd "$(dirname "$0")"
app=$(ls -1 MedicalField-*.AppImage 2>/dev/null | sort -V | tail -1)
[ -n "$app" ] || { echo "Coloque o MedicalField-*.AppImage nesta pasta."; exit 1; }
chmod +x "$app"
exec "./$app" --appimage-extract-and-run --no-sandbox "$@"
