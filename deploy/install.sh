#!/usr/bin/env bash
# Implantação do MedicalField na VM (Ubuntu/Debian), sem contêineres.
# Uso (na raiz do repositório, como root): sudo ./deploy/install.sh
# Pré-requisitos: postgresql, nginx, openjdk-21-jre, nodejs >= 20, npm, python3-venv
# (+ maven, se o jar e o portal não vierem compilados).
# Antes de rodar, crie os .env a partir dos .env.example (ver README).
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=/opt/medicalfield

id medicalfield >/dev/null 2>&1 || useradd --system --home "$DEST" --shell /usr/sbin/nologin medicalfield
mkdir -p "$DEST"/{auth,clinical,document} /var/www/medicalfield

for f in services/auth-service/.env services/clinical-service/.env services/document-service/.env; do
  [ -f "$f" ] || { echo "Falta $f (copie de $f.example e ajuste)"; exit 1; }
done

echo "== banco"
# Senhas dos usuários do banco lidas dos .env de cada serviço.
pw() { grep -E '^DB_PASSWORD=' "$1" | cut -d= -f2-; }
sudo -u postgres psql -v auth_pw="$(pw services/auth-service/.env)" \
  -v clinical_pw="$(pw services/clinical-service/.env)" \
  -v document_pw="$(pw services/document-service/.env)" -f db/init.sql

echo "== clinical-service"
# Em VMs com pouca memória, compile antes na sua máquina e envie o jar pronto.
[ -f services/clinical-service/target/clinical-service.jar ] || (cd services/clinical-service && mvn -q -B -DskipTests package)
install -m 644 services/clinical-service/target/clinical-service.jar "$DEST/clinical/"
install -m 600 services/clinical-service/.env "$DEST/clinical/.env"

echo "== auth-service"
rsync -a --delete --exclude node_modules --exclude .env services/auth-service/ "$DEST/auth/"
install -m 600 services/auth-service/.env "$DEST/auth/.env"
(cd "$DEST/auth" && npm ci --omit=dev --no-audit --no-fund)

echo "== document-service"
rsync -a --delete --exclude .venv --exclude .env --exclude emails services/document-service/ "$DEST/document/"
install -m 600 services/document-service/.env "$DEST/document/.env"
python3 -m venv "$DEST/document/.venv"
"$DEST/document/.venv/bin/pip" install -q -r "$DEST/document/requirements.txt"

echo "== portal"
[ -f portal/dist/index.html ] || (cd portal && npm ci --no-audit --no-fund && npm run build)
rsync -a --delete portal/dist/ /var/www/medicalfield/

chown -R medicalfield:medicalfield "$DEST"

echo "== systemd e nginx"
install -m 644 deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
# O clinical-service cria o schema audit; os outros dois gravam nele.
systemctl enable --now medicalfield-clinical
for _ in $(seq 60); do
  sudo -u postgres psql -d medicalfield -tAc "SELECT to_regclass('audit.access_log')" | grep -q access_log && break
  sleep 2
done
systemctl enable --now medicalfield-auth medicalfield-document
install -m 644 deploy/nginx/medicalfield.conf /etc/nginx/sites-available/medicalfield
ln -sf /etc/nginx/sites-available/medicalfield /etc/nginx/sites-enabled/medicalfield
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "Pronto. Para carregar os dados do roteiro: sudo -u postgres psql -d medicalfield -f db/seed.sql"
