#!/usr/bin/env bash
# Volta o servidor ao começo do roteiro de testes: apaga pessoas, prontuários,
# atendimentos, medicamentos, e-mails e logs de auditoria, e recarrega o db/seed.sql.
# Os profissionais são mantidos.
# Uso (na raiz do repositório, na VM): sudo ./deploy/zerar.sh [--sim]
#   --sim  não pede confirmação
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" != "--sim" ]; then
  echo "Isto APAGA todos os dados clínicos, e-mails e logs do servidor e recarrega os dados do roteiro."
  read -r -p "Digite ZERAR para continuar: " resposta
  [ "$resposta" = "ZERAR" ] || { echo "Cancelado."; exit 1; }
fi

psql() { sudo -u postgres psql -d medicalfield -v ON_ERROR_STOP=1 -q "$@"; }

echo "== apagando dados"
psql -c "TRUNCATE clinical.medicacao_administrada, clinical.sinal_vital, clinical.atendimento,
           clinical.prontuario, clinical.pessoa, clinical.medicamento, clinical.idempotencia,
           document.envio_email, audit.access_log, audit.sync_evento RESTART IDENTITY CASCADE"
rm -f /opt/medicalfield/document/emails/*.eml

echo "== recarregando o seed"
psql -f db/seed.sql

psql -tA -c "SELECT (SELECT count(*) FROM auth.profissional) || ' profissionais, ' ||
  (SELECT count(*) FROM clinical.medicamento) || ' medicamentos, ' ||
  (SELECT count(*) FROM clinical.pessoa) || ' pessoas, ' ||
  (SELECT count(*) FROM clinical.atendimento) || ' atendimentos'"
echo "Pronto. No notebook, apague também o banco local do cliente (client-vm.sqlite)."
