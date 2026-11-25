import type { Atendimento, Pessoa, Prontuario } from '../shared/tipos';
import { ApiClient, HttpError, OfflineError } from './api';
import { Banco } from './db';
import {
  AtendimentoRepository, EstadoRepository, LogRepository, MedicamentoRepository, OutboxRepository, PessoaRepository,
  ProntuarioRepository,
} from './repositories';

const TABELA: Record<string, string> = { PESSOA: 'pessoa', PRONTUARIO: 'prontuario', ATENDIMENTO: 'atendimento' };
const SUCESSO = new Set(['APLICADO', 'DUPLICADO', 'CONFLITO_RESOLVIDO']);

export type Resumo = { enviados: number; erros: number; logs: number; recebidos: number };

/**
 * Esvazia a Outbox (push), envia os logs locais e baixa as novidades (pull).
 * Disparado pelo ConnectivityMonitor quando a conexão volta, após cada gravação
 * feita online e pelo botão "Sincronizar".
 */
export class SyncService {
  sincronizando = false;
  mensagem: string | null = null;

  constructor(
    private banco: Banco,
    private repos: {
      pessoas: PessoaRepository; prontuarios: ProntuarioRepository; atendimentos: AtendimentoRepository;
      medicamentos: MedicamentoRepository; outbox: OutboxRepository; logs: LogRepository; estado: EstadoRepository;
    },
    private api: ApiClient,
    private renovarToken: () => Promise<boolean>,
    private aoMudar: () => void,
  ) {}

  async sincronizar(): Promise<Resumo | null> {
    if (this.sincronizando) return null;
    this.sincronizando = true;
    this.mensagem = 'Sincronizando…';
    this.aoMudar();
    try {
      let r: Resumo;
      try {
        r = await this.executar();
      } catch (e) {
        if (e instanceof HttpError && e.status === 401 && (await this.renovarToken())) r = await this.executar();
        else throw e;
      }
      const agora = new Date().toISOString();
      this.repos.estado.gravar('ultima_sync', agora);
      this.mensagem = `Sincronizado: ${r.enviados} enviado(s), ${r.recebidos} recebido(s)` + (r.erros ? `, ${r.erros} com erro` : '');
      return r;
    } catch (e) {
      this.mensagem = e instanceof OfflineError ? 'Sem conexão: os dados seguem salvos no dispositivo'
        : e instanceof HttpError && e.status === 401 ? 'Sessão expirada: entre novamente para sincronizar'
          : `Falha na sincronização: ${(e as Error).message}`;
      throw e;
    } finally {
      this.sincronizando = false;
      this.aoMudar();
    }
  }

  private async executar(): Promise<Resumo> {
    const { enviados, erros } = await this.push();
    const logs = await this.enviarLogs();
    const recebidos = await this.pull();
    return { enviados, erros, logs, recebidos };
  }

  /** Envia a Outbox em lotes, na ordem de criação (pessoa → prontuário → atendimento). */
  async push() {
    const itens = this.repos.outbox.paraEnviar(500);
    let enviados = 0;
    let erros = 0;
    for (let i = 0; i < itens.length; i += 20) {
      const lote = itens.slice(i, i + 20);
      const resp = await this.api.push(lote.map((it) => ({
        outboxId: it.id, chave: it.chave, entidade: it.entidade, operacao: it.operacao, baseVersion: it.baseVersion,
        payload: JSON.parse(it.payload),
      })));
      this.banco.transacao(() => {
        for (const r of resp.resultados) {
          const item = lote.find((x) => x.id === r.outboxId);
          if (!item) continue;
          if (SUCESSO.has(r.status)) {
            this.repos.outbox.marcarEnviado(item.id);
            const tabela = TABELA[item.entidade];
            const resta = this.repos.outbox.pendentesDe(item.entidade, item.entidadeId);
            if (tabela && r.versao != null) {
              this.banco.run(`UPDATE ${tabela} SET version = ?, sync_status = ? WHERE id = ?`,
                r.versao, resta ? 'PENDENTE' : 'SINCRONIZADO', item.entidadeId);
            }
            enviados++;
          } else {
            this.repos.outbox.marcarErro(item.id, r.mensagem ?? r.status);
            if (TABELA[item.entidade]) {
              this.banco.run(`UPDATE ${TABELA[item.entidade]} SET sync_status = 'ERRO' WHERE id = ?`, item.entidadeId);
            }
            erros++;
          }
        }
      });
      this.aoMudar();
    }
    return { enviados, erros };
  }

  async enviarLogs() {
    const logs = this.repos.logs.naoEnviados();
    if (!logs.length) return 0;
    await this.api.enviarLogs(logs.map((l) => ({
      dataHora: l.dataHora, acao: l.acao, entidade: l.entidade, entidadeId: l.entidadeId, profissionalId: l.profissionalId,
    })));
    this.repos.logs.marcarEnviados(logs.map((l) => l.id));
    return logs.length;
  }

  /** Baixa o que mudou no servidor; registros com alteração local pendente não são sobrescritos. */
  async pull() {
    const since = this.repos.estado.ler('last_pull_at');
    const d = await this.api.pull(since);
    const livre = (ent: string, id: string) => this.repos.outbox.pendentesDe(ent, id) === 0;
    this.banco.transacao(() => {
      for (const m of d.medicamentos) this.repos.medicamentos.gravar(m);
      for (const p of d.pessoas as Pessoa[]) if (livre('PESSOA', p.id)) this.repos.pessoas.gravar(p, 'SINCRONIZADO');
      for (const p of d.prontuarios as Prontuario[]) if (livre('PRONTUARIO', p.id)) this.repos.prontuarios.gravar(p, 'SINCRONIZADO');
      for (const a of d.atendimentos as Atendimento[]) {
        if (livre('ATENDIMENTO', a.id)) {
          this.repos.atendimentos.gravar({ ...a, glasgow: a.glasgow ?? {}, sinaisVitais: a.sinaisVitais ?? [], medicacoes: a.medicacoes ?? [] }, 'SINCRONIZADO');
        }
      }
      this.repos.estado.gravar('last_pull_at', d.serverTime);
    });
    return d.medicamentos.length + d.pessoas.length + d.prontuarios.length + d.atendimentos.length;
  }
}
