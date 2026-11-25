#!/usr/bin/env bash
# Atualiza o código já instalado na VM sem tocar nos dados nem nos .env de /opt/medicalfield
# (o install.sh sobrescreveria o .env do document-service, onde fica a senha do SMTP).
# Espera o jar e o portal já compilados (a VM tem pouca memória para compilar):
#   na sua máquina: (cd services/clinical-service && mvn -DskipTests package) e (cd portal && npm run build)
#   envie o repositório para a VM (rsync) e, nela: sudo ./deploy/atualizar.sh
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=/opt/medicalfield

[ -f services/clinical-service/target/clinical-service.jar ] || { echo "Falta o jar do clinical-service"; exit 1; }
[ -f portal/dist/index.html ] || { echo "Falta o build do portal (portal/dist)"; exit 1; }

echo "== código"
install -m 644 services/clinical-service/target/clinical-service.jar "$DEST/clinical/"
rsync -a --exclude node_modules --exclude .env services/auth-service/ "$DEST/auth/"
(cd "$DEST/auth" && npm ci --omit=dev --no-audit --no-fund >/dev/null)
rsync -a --exclude .venv --exclude .env --exclude emails services/document-service/ "$DEST/document/"
"$DEST/document/.venv/bin/pip" install -q -r "$DEST/document/requirements.txt"
chown -R medicalfield:medicalfield "$DEST"
rsync -a --delete portal/dist/ /var/www/medicalfield/
chmod -R a+rX /var/www/medicalfield

echo "== nginx"
install -m 644 deploy/nginx/medicalfield.conf /etc/nginx/sites-available/medicalfield
nginx -t

echo "== reiniciando"
systemctl restart medicalfield-clinical
for _ in $(seq 60); do curl -s -o /dev/null http://127.0.0.1:8080/ && break; sleep 2; done
systemctl restart medicalfield-auth medicalfield-document
systemctl reload nginx
sleep 3
systemctl is-active medicalfield-clinical medicalfield-auth medicalfield-document nginx
echo "Pronto. Confira com: ./deploy/verificar.sh"
