#!/usr/bin/env bash
# Confere se o MedicalField está pronto para o roteiro: portal, Swagger, autenticação,
# perfis, rotas dos três serviços e o PDF. Pode rodar de qualquer máquina.
# Uso: ./deploy/verificar.sh [endereço]      (padrão: http://177.44.248.75)
set -uo pipefail
BASE="${1:-http://177.44.248.75}"
API="$BASE/api"
SENHA="MedField@2026"
falhas=0

checar() { # descrição, esperado, obtido
  if [ "$2" = "$3" ]; then echo "  ok    $1"; else echo "  FALHA $1 (esperado $2, veio $3)"; falhas=$((falhas + 1)); fi
}
status() { curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$@"; }
token() {
  curl -s --max-time 15 -X POST "$API/auth/login" -H 'Content-Type: application/json' \
    -d "{\"registro\":\"$1\",\"senha\":\"$SENHA\"}" |
    python3 -c 'import sys, json; print(json.load(sys.stdin).get("accessToken", ""))' 2>/dev/null
}

echo "Verificando $BASE"
checar "portal" 200 "$(status "$BASE/")"
checar "swagger (/docs/)" 200 "$(status "$BASE/docs/")"
checar "rota sem token → 401" 401 "$(status "$API/pessoa")"

SOC=$(token 'CRM-RS 12345')
ADM=$(token 'CRM-RS 99999')
checar "login do socorrista" sim "$([ -n "$SOC" ] && echo sim || echo não)"
checar "login do administrador" sim "$([ -n "$ADM" ] && echo sim || echo não)"

for rota in auth/me medicamento pessoa prontuario atendimento "sync/pull"; do
  checar "GET /$rota (socorrista)" 200 "$(status -H "Authorization: Bearer $SOC" "$API/$rota")"
done
for rota in profissional "log?tipo=acesso&limite=1" documento/envio; do
  checar "GET /$rota (admin)" 200 "$(status -H "Authorization: Bearer $ADM" "$API/$rota")"
  checar "GET /$rota (socorrista) → 403" 403 "$(status -H "Authorization: Bearer $SOC" "$API/$rota")"
done

ATD=$(curl -s --max-time 15 -H "Authorization: Bearer $ADM" "$API/atendimento" |
  python3 -c 'import sys, json; d = json.load(sys.stdin); print(d[0]["id"] if d else "")' 2>/dev/null)
if [ -n "$ATD" ]; then
  checar "PDF da ficha" 200 "$(status -H "Authorization: Bearer $ADM" "$API/documento/ficha/$ATD")"
else
  checar "há atendimento para gerar o PDF" sim não
fi

echo
if [ "$falhas" -eq 0 ]; then echo "Tudo certo."; else echo "$falhas verificação(ões) falharam."; exit 1; fi
