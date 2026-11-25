export function dataHora(v?: string | null) {
  if (!v) return '—';
  return new Date(v).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function data(v?: string | null) {
  if (!v) return '—';
  const [a, m, d] = v.slice(0, 10).split('-');
  return `${d}/${m}/${a}`;
}

export function texto(v: unknown) {
  return v === null || v === undefined || v === '' ? '—' : String(v);
}

export const CORES_TRIAGEM: Record<string, string> = {
  VERMELHO: '#ef4444', LARANJA: '#f97316', AMARELO: '#facc15', VERDE: '#22c55e', AZUL: '#3b82f6', PRETO: '#94a3b8',
};
