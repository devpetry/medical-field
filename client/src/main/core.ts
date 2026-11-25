import bcrypt from 'bcryptjs';
import { randomUUID } from 'node:crypto';
import type {
  Atendimento, Estado, ItemOutbox, LogLocal, Medicamento, Pessoa, Profissional, Prontuario, ResultadoValidacao,
} from '../shared/tipos';
import { ApiClient, HttpError, OfflineError } from './api';
import { ConnectivityMonitor } from './connectivity';
import { Banco } from './db';
import {
  AtendimentoRepository, EstadoRepository, LogRepository, MedicamentoRepository, OutboxRepository, PessoaRepository,
  ProntuarioRepository, SessaoRepository,
} from './repositories';
import { validarAtendimento } from './rules';
import { SyncService } from './sync';

export type Opcoes = { arquivoBanco: string; apiUrl: string; deviceId?: string; intervaloPingMs?: number };
export type ResumoAtendimento = Atendimento & { pessoaNome: string; pessoaId: string };
export type SalvarAtendimento = { salvo: true; atendimento: Atendimento } | { salvo: false; alertas: ResultadoValidacao['alertas'] };

const agora = () => new Date().toISOString();

/**
 * Núcleo do cliente (sem dependência do Electron): grava sempre no SQLite,
 * enfileira na Outbox na mesma transação e sincroniza quando há conexão.
 */
export class MedicalFieldCore {
  readonly banco: Banco;
  readonly pessoas: PessoaRepository;
  readonly prontuarios: ProntuarioRepository;
  readonly atendimentosRepo: AtendimentoRepository;
  readonly medicamentosRepo: MedicamentoRepository;
  readonly outboxRepo: OutboxRepository;
  readonly logs: LogRepository;
  readonly sessoes: SessaoRepository;
  readonly estadoRepo: EstadoRepository;
  readonly api: ApiClient;
  readonly monitor: ConnectivityMonitor;
  readonly sync: SyncService;
  readonly deviceId: string;
  private credenciais: { registro: string; tipo: string; senha: string } | null = null;
  private ouvintes: ((e: Estado) => void)[] = [];

  constructor(private opcoes: Opcoes) {
    this.banco = new Banco(opcoes.arquivoBanco);
    this.pessoas = new PessoaRepository(this.banco);
    this.prontuarios = new ProntuarioRepository(this.banco);
    this.atendimentosRepo = new AtendimentoRepository(this.banco);
    this.medicamentosRepo = new MedicamentoRepository(this.banco);
    this.outboxRepo = new OutboxRepository(this.banco);
    this.logs = new LogRepository(this.banco);
    this.sessoes = new SessaoRepository(this.banco);
    this.estadoRepo = new EstadoRepository(this.banco);

    let device = opcoes.deviceId ?? this.estadoRepo.ler('device_id');
    if (!device) device = `disp-${randomUUID().slice(0, 8)}`;
    this.estadoRepo.gravar('device_id', device);
    this.deviceId = device;

    this.api = new ApiClient(opcoes.apiUrl, device, () => this.monitor.simulacaoOnline);
    this.api.token = this.sessoes.ativa()?.token ?? null;
    this.monitor = new ConnectivityMonitor(() => this.api, opcoes.intervaloPingMs);
    this.sync = new SyncService(this.banco, {
      pessoas: this.pessoas, prontuarios: this.prontuarios, atendimentos: this.atendimentosRepo,
      medicamentos: this.medicamentosRepo, outbox: this.outboxRepo, logs: this.logs, estado: this.estadoRepo,
    }, this.api, () => this.renovarToken(), () => this.emitir());

    // Observer: quando a conexão volta, renova o token se preciso e esvazia a Outbox.
    this.monitor.inscrever((online) => {
      this.emitir();
      if (online && this.sessoes.ativa()) {
        void (async () => {
          if (!this.tokenValido()) await this.renovarToken();
          await this.sync.sincronizar().catch(() => undefined);
        })();
      }
    });
  }

  iniciar() {
    this.monitor.iniciar();
  }

  encerrar() {
    this.monitor.parar();
  }

  aoMudarEstado(fn: (e: Estado) => void) {
    this.ouvintes.push(fn);
  }

  private emitir() {
    const e = this.estado();
    for (const o of this.ouvintes) o(e);
  }

  // ------------------------------------------------------------- estado
  private tokenValido() {
    const s = this.sessoes.ativa();
    return !!s?.token && !!s.expiraEm && new Date(s.expiraEm).getTime() > Date.now() + 60_000;
  }

  estado(): Estado {
    const s = this.sessoes.ativa();
    const c = this.outboxRepo.contagem();
    return {
      online: this.monitor.online, simulacaoOnline: this.monitor.simulacaoOnline,
      servidorAlcancavel: this.monitor.servidorAlcancavel, sincronizando: this.sync.sincronizando,
      pendencias: c.pendencias, erros: c.erros, ultimoPull: this.estadoRepo.ler('last_pull_at'),
      ultimaSync: this.estadoRepo.ler('ultima_sync'), mensagem: this.sync.mensagem, deviceId: this.deviceId,
      apiUrl: this.opcoes.apiUrl, tokenValido: this.tokenValido(),
      profissional: s ? { id: s.id, nome: s.nome, registro: s.registro, tipo: s.tipo, perfil: s.perfil } : null,
    };
  }

  private profissionalAtivo(): Profissional {
    const s = this.sessoes.ativa();
    if (!s) throw new Error('Nenhum profissional autenticado');
    return s;
  }

  private registrarOffline(acao: string, entidade: string | null, id: string | null) {
    if (!this.monitor.online) this.logs.registrar(acao, entidade, id, this.sessoes.ativa()?.id ?? null);
  }

  // ------------------------------------------------------------- sessão
  async login(registro: string, tipo: string, senha: string): Promise<Profissional> {
    registro = registro.trim();
    try {
      const r = await this.api.login(registro, tipo, senha);
      const expira = new Date(Date.now() + r.expiresIn * 1000).toISOString();
      this.sessoes.salvar(r.profissional, r.accessToken, bcrypt.hashSync(senha, 10), expira);
      this.api.token = r.accessToken;
      this.credenciais = { registro, tipo, senha };
      this.emitir();
      return r.profissional;
    } catch (e) {
      if (e instanceof HttpError) throw new Error(e.status === 401 ? 'Registro ou senha inválidos' : e.message);
      if (!(e instanceof OfflineError)) throw e;
    }
    // Sem rede: confere o hash guardado no último login online deste profissional.
    const local = this.sessoes.porRegistro(registro, tipo);
    if (!local) throw new Error('Sem conexão e este profissional ainda não entrou online neste dispositivo');
    if (!bcrypt.compareSync(senha, local.senhaHash)) throw new Error('Registro ou senha inválidos');
    this.sessoes.ativar(local.id);
    this.api.token = local.token;
    this.credenciais = { registro, tipo, senha };
    this.logs.registrar('LOGIN_OFFLINE', 'profissional', String(local.id), local.id);
    this.emitir();
    return local;
  }

  /** Renova o JWT com as credenciais da sessão atual (só em memória, nunca gravadas). */
  async renovarToken(): Promise<boolean> {
    if (!this.credenciais) return false;
    try {
      const { registro, tipo, senha } = this.credenciais;
      const r = await this.api.login(registro, tipo, senha);
      this.sessoes.salvar(r.profissional, r.accessToken, bcrypt.hashSync(senha, 10),
        new Date(Date.now() + r.expiresIn * 1000).toISOString());
      this.api.token = r.accessToken;
      this.emitir();
      return true;
    } catch {
      return false;
    }
  }

  logout() {
    this.sessoes.encerrar();
    this.api.token = null;
    this.credenciais = null;
    this.emitir();
  }

  async definirSimulacao(online: boolean) {
    await this.monitor.definirSimulacao(online);
    this.emitir();
  }

  async sincronizar() {
    this.profissionalAtivo();
    return this.sync.sincronizar();
  }

  /** Após gravar: se estiver online, envia já (o fluxo de tela é o mesmo online ou offline). */
  private aposGravar() {
    this.emitir();
    if (this.monitor.online) void this.sync.sincronizar().catch(() => undefined);
  }

  // ------------------------------------------------------------- cadastros
  listarPessoas(busca = ''): Pessoa[] {
    return this.pessoas.listar(busca);
  }

  salvarPessoa(dados: Partial<Pessoa>): Pessoa {
    const prof = this.profissionalAtivo();
    if (!dados.nome?.trim()) throw new Error('Informe o nome da pessoa');
    const atual = dados.id ? this.pessoas.buscar(dados.id) : null;
    if (atual && semMudanca(atual, dados)) return atual;
    const p: Pessoa = {
      ...atual, ...dados, id: dados.id ?? randomUUID(), nome: dados.nome.trim(), version: atual?.version ?? 0,
      updatedAt: agora(), updatedBy: prof.id,
    };
    this.banco.transacao(() => {
      this.pessoas.gravar(p, 'PENDENTE');
      this.outboxRepo.enfileirar('PESSOA', p.id, atual?.version ? 'UPDATE' : 'CREATE', p.version, semLocal(p));
      this.registrarOffline(atual ? 'ATUALIZAR' : 'CRIAR', 'pessoa', p.id);
    });
    this.aposGravar();
    return this.pessoas.buscar(p.id)!;
  }

  prontuarioDaPessoa(pessoaId: string): Prontuario | null {
    return this.prontuarios.daPessoa(pessoaId);
  }

  salvarProntuario(dados: Partial<Prontuario> & { pessoaId: string }): Prontuario {
    const prof = this.profissionalAtivo();
    if (!this.pessoas.buscar(dados.pessoaId)) throw new Error('Pessoa não encontrada no dispositivo');
    const atual = dados.id ? this.prontuarios.buscar(dados.id) : this.prontuarios.daPessoa(dados.pessoaId);
    if (atual && semMudanca(atual, dados)) return atual;
    const p: Prontuario = {
      ...atual, ...dados, id: atual?.id ?? dados.id ?? randomUUID(), version: atual?.version ?? 0,
      updatedAt: agora(), updatedBy: prof.id,
    };
    this.banco.transacao(() => {
      this.prontuarios.gravar(p, 'PENDENTE');
      this.outboxRepo.enfileirar('PRONTUARIO', p.id, atual?.version ? 'UPDATE' : 'CREATE', p.version, semLocal(p));
      this.registrarOffline(atual ? 'ATUALIZAR' : 'CRIAR', 'prontuario', p.id);
    });
    this.aposGravar();
    return this.prontuarios.buscar(p.id)!;
  }

  listarMedicamentos(): Medicamento[] {
    return this.medicamentosRepo.listar();
  }

  listarAtendimentos(pessoaId?: string): ResumoAtendimento[] {
    const pr = pessoaId ? this.prontuarios.daPessoa(pessoaId) : null;
    if (pessoaId && !pr) return [];
    return this.atendimentosRepo.listar(pr?.id).map((a) => {
      const pront = this.prontuarios.buscar(a.prontuarioId);
      const pes = pront ? this.pessoas.buscar(pront.pessoaId) : null;
      return { ...a, pessoaId: pes?.id ?? '', pessoaNome: pes?.nome ?? '—' };
    });
  }

  validarAtendimento(a: Atendimento): ResultadoValidacao {
    const pr = this.prontuarios.buscar(a.prontuarioId);
    const pessoa = pr ? this.pessoas.buscar(pr.pessoaId) : null;
    return validarAtendimento(a, pessoa, (id) => this.medicamentosRepo.buscar(id));
  }

  salvarAtendimento(dados: Partial<Atendimento> & { prontuarioId: string }): SalvarAtendimento {
    const prof = this.profissionalAtivo();
    if (!this.prontuarios.buscar(dados.prontuarioId)) throw new Error('Prontuário não encontrado no dispositivo');
    const atual = dados.id ? this.atendimentosRepo.buscar(dados.id) : null;
    const g = dados.glasgow ?? atual?.glasgow ?? {};
    const total = g.ocular != null && g.verbal != null && g.motora != null ? g.ocular + g.verbal + g.motora : null;
    const a: Atendimento = {
      status: 'ABERTO', ...atual, ...dados,
      id: dados.id ?? randomUUID(),
      profissionalId: atual?.profissionalId ?? prof.id,
      deviceId: atual?.deviceId ?? this.deviceId,
      inicio: dados.inicio ?? atual?.inicio ?? agora(),
      glasgow: { ...g, total },
      criadoOffline: atual?.criadoOffline ?? !this.monitor.online,
      version: atual?.version ?? 0,
      updatedAt: agora(),
      sinaisVitais: (dados.sinaisVitais ?? atual?.sinaisVitais ?? []).map((s) => ({ ...s, id: s.id ?? randomUUID() })),
      medicacoes: (dados.medicacoes ?? atual?.medicacoes ?? []).map((m) => ({
        ...m, id: m.id ?? randomUUID(), profissionalId: m.profissionalId ?? prof.id, alertaConfirmado: !!m.alertaConfirmado,
      })),
    };
    const v = this.validarAtendimento(a);
    if (v.erros.length) throw new Error(v.erros.join('; '));
    if (v.alertas.length) return { salvo: false, alertas: v.alertas };
    this.banco.transacao(() => {
      this.atendimentosRepo.gravar(a, 'PENDENTE');
      this.outboxRepo.enfileirar('ATENDIMENTO', a.id, atual?.version ? 'UPDATE' : 'CREATE', a.version, semLocal(a));
      this.registrarOffline(atual ? 'ATUALIZAR' : 'CRIAR', 'atendimento', a.id);
    });
    this.aposGravar();
    return { salvo: true, atendimento: this.atendimentosRepo.buscar(a.id)! };
  }

  listarOutbox(): ItemOutbox[] {
    return this.outboxRepo.listar();
  }

  listarLogs(): LogLocal[] {
    return this.logs.listar();
  }

  // ------------------------------------------------------------- documentos (exigem conexão)
  async fichaPdf(atendimentoId: string): Promise<Buffer> {
    this.exigirSincronizado(atendimentoId);
    return this.api.fichaPdf(atendimentoId);
  }

  async enviarFicha(atendimentoId: string, destinatario: string, nome: string | null, relacao: string) {
    this.exigirSincronizado(atendimentoId);
    return this.api.enviarFicha(atendimentoId, destinatario, nome, relacao);
  }

  private exigirSincronizado(id: string) {
    if (!this.monitor.online) throw new Error('A ficha é gerada pelo servidor: conecte-se para gerar ou enviar');
    if (this.outboxRepo.pendentesDe('ATENDIMENTO', id)) throw new Error('Sincronize o atendimento antes de gerar a ficha');
  }
}

/** Nenhum campo enviado difere do registro atual (evita enfileirar edição vazia). */
function semMudanca(atual: object, dados: object) {
  const a = atual as Record<string, unknown>;
  return Object.entries(dados).every(([k, v]) => (a[k] ?? '') === (v ?? ''));
}

/** Remove os campos que só existem no dispositivo antes de enfileirar. */
function semLocal<T extends { syncStatus?: string }>(o: T) {
  const { syncStatus: _s, ...resto } = o;
  return resto;
}
