import type { Atendimento, Medicamento, Pessoa, ResultadoValidacao } from '../shared/tipos';

/**
 * Regras de segurança clínica aplicadas no dispositivo, mesmo sem rede, com a
 * cópia local dos medicamentos. O clinical-service repete as mesmas checagens.
 */
const norm = (s: string) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();

export function alergiaConflitante(p: Pessoa | null, m: Medicamento): string | null {
  if (!p?.alergias) return null;
  const alvo = norm(`${m.nome} ${m.principioAtivo} ${m.alertas ?? ''}`);
  return p.alergias.split(/[,;/]/).map((t) => t.trim()).find((t) => t.length >= 3 && alvo.includes(norm(t))) ?? null;
}

const FAIXAS: [keyof Atendimento['sinaisVitais'][number], string, number, number][] = [
  ['paSistolica', 'PA sistólica', 40, 300], ['paDiastolica', 'PA diastólica', 20, 200], ['fc', 'FC', 20, 250],
  ['fr', 'FR', 4, 80], ['spo2', 'SpO₂', 50, 100], ['temperatura', 'Temperatura', 30, 45], ['glicemia', 'Glicemia', 10, 1000],
];

export function validarAtendimento(a: Atendimento, pessoa: Pessoa | null, medicamento: (id: number) => Medicamento | null): ResultadoValidacao {
  const erros: string[] = [];
  const alertas: ResultadoValidacao['alertas'] = [];
  const g = a.glasgow ?? {};
  const algum = g.ocular != null || g.verbal != null || g.motora != null;
  if (algum) {
    if (!(g.ocular! >= 1 && g.ocular! <= 4)) erros.push('Glasgow ocular deve estar entre 1 e 4');
    if (!(g.verbal! >= 1 && g.verbal! <= 5)) erros.push('Glasgow verbal deve estar entre 1 e 5');
    if (!(g.motora! >= 1 && g.motora! <= 6)) erros.push('Glasgow motora deve estar entre 1 e 6');
  }
  for (const s of a.sinaisVitais) {
    for (const [campo, nome, min, max] of FAIXAS) {
      const v = s[campo] as number | null | undefined;
      if (v != null && (v < min || v > max)) erros.push(`${nome} fora da faixa ${min}–${max}`);
    }
  }
  for (const m of a.medicacoes) {
    const med = medicamento(m.medicamentoId);
    if (!med) {
      erros.push(`Medicamento ${m.medicamentoId} não está na lista local; sincronize`);
      continue;
    }
    if (m.unidade.toLowerCase() === med.unidade.toLowerCase() && m.dose > med.doseMaxima) {
      erros.push(`Dose de ${med.nome} acima do máximo (${med.doseMaxima} ${med.unidade})`);
    }
    const alergia = alergiaConflitante(pessoa, med);
    if (alergia && !m.alertaConfirmado) {
      alertas.push({ medicacaoId: m.id, mensagem: `Paciente com alergia a ${alergia}: confirme para administrar ${med.nome}` });
    }
  }
  return { erros, alertas };
}
