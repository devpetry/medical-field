import type {
  Atendimento, Estado, ItemOutbox, LogLocal, Medicamento, Pessoa, Profissional, Prontuario, ResultadoValidacao,
} from '../shared/tipos';

type Ponte = {
  chamar: (metodo: string, ...args: unknown[]) => Promise<unknown>;
  salvarFicha: (atendimentoId: string) => Promise<string | null>;
  aoMudarEstado: (fn: (e: Estado) => void) => () => void;
};
declare global {
  interface Window { mf: Ponte }
}

export type ResumoAtendimento = Atendimento & { pessoaNome: string; pessoaId: string };
export type SalvarAtendimento = { salvo: true; atendimento: Atendimento } | { salvo: false; alertas: ResultadoValidacao['alertas'] };

/** Erros do IPC chegam como "Error invoking remote method …: Error: mensagem". */
export function mensagem(e: unknown) {
  const m = e instanceof Error ? e.message : String(e);
  return m.replace(/^Error invoking remote method '[^']+': (Error: )?/, '');
}

const c = <T,>(metodo: string, ...args: unknown[]) => window.mf.chamar(metodo, ...args) as Promise<T>;

export const mf = {
  estado: () => c<Estado>('estado'),
  login: (registro: string, tipo: string, senha: string) => c<Profissional>('login', registro, tipo, senha),
  logout: () => c<void>('logout'),
  definirSimulacao: (online: boolean) => c<void>('definirSimulacao', online),
  sincronizar: () => c<unknown>('sincronizar'),
  listarPessoas: (busca = '') => c<Pessoa[]>('listarPessoas', busca),
  salvarPessoa: (p: Partial<Pessoa>) => c<Pessoa>('salvarPessoa', p),
  prontuarioDaPessoa: (pessoaId: string) => c<Prontuario | null>('prontuarioDaPessoa', pessoaId),
  salvarProntuario: (p: Partial<Prontuario> & { pessoaId: string }) => c<Prontuario>('salvarProntuario', p),
  listarMedicamentos: () => c<Medicamento[]>('listarMedicamentos'),
  listarAtendimentos: (pessoaId?: string) => c<ResumoAtendimento[]>('listarAtendimentos', pessoaId),
  salvarAtendimento: (a: Partial<Atendimento> & { prontuarioId: string }) => c<SalvarAtendimento>('salvarAtendimento', a),
  listarOutbox: () => c<ItemOutbox[]>('listarOutbox'),
  listarLogs: () => c<LogLocal[]>('listarLogs'),
  enviarFicha: (id: string, destinatario: string, nome: string | null, relacao: string) =>
    c<{ envioId: number; status: string }>('enviarFicha', id, destinatario, nome, relacao),
  salvarFicha: (id: string) => window.mf.salvarFicha(id),
  aoMudarEstado: (fn: (e: Estado) => void) => window.mf.aoMudarEstado(fn),
};
