import type {
  Atendimento, ItemOutbox, LogLocal, Medicacao, Medicamento, Pessoa, Profissional, Prontuario, SinalVital,
} from '../shared/tipos';
import { randomUUID } from 'node:crypto';
import { Banco, v } from './db';

/*
 * Repository Pattern: a interface gráfica e o SyncService só conversam com estes
 * repositórios (SQLite local) e com o ApiClient (REST remoto), nunca com SQL direto.
 */

type Linha = Record<string, unknown>;
const n = (x: unknown) => (x === null || x === undefined ? null : Number(x));
const s = (x: unknown) => (x === null || x === undefined ? null : String(x));

export class PessoaRepository {
  constructor(private b: Banco) {}

  listar(busca = ''): Pessoa[] {
    const q = `%${busca.trim().toLowerCase()}%`;
    return this.b.all<Linha>('SELECT * FROM pessoa WHERE lower(nome) LIKE ? OR cpf LIKE ? ORDER BY nome', q, q).map(lerPessoa);
  }

  buscar(id: string): Pessoa | null {
    const r = this.b.get<Linha>('SELECT * FROM pessoa WHERE id = ?', id);
    return r ? lerPessoa(r) : null;
  }

  gravar(p: Pessoa, syncStatus: string) {
    this.b.run(`INSERT INTO pessoa (id, nome, cpf, data_nascimento, sexo, tipo_sanguineo, alergias, telefone, email_contato,
        contato_emergencia, version, updated_at, updated_by, sync_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, cpf=excluded.cpf, data_nascimento=excluded.data_nascimento,
        sexo=excluded.sexo, tipo_sanguineo=excluded.tipo_sanguineo, alergias=excluded.alergias, telefone=excluded.telefone,
        email_contato=excluded.email_contato, contato_emergencia=excluded.contato_emergencia, version=excluded.version,
        updated_at=excluded.updated_at, updated_by=excluded.updated_by, sync_status=excluded.sync_status`,
      p.id, p.nome, v(p.cpf), v(p.dataNascimento), v(p.sexo), v(p.tipoSanguineo), v(p.alergias), v(p.telefone),
      v(p.emailContato), v(p.contatoEmergencia), p.version ?? 0, p.updatedAt, v(p.updatedBy), syncStatus);
  }
}

function lerPessoa(r: Linha): Pessoa {
  return {
    id: String(r.id), nome: String(r.nome), cpf: s(r.cpf), dataNascimento: s(r.data_nascimento), sexo: s(r.sexo),
    tipoSanguineo: s(r.tipo_sanguineo), alergias: s(r.alergias), telefone: s(r.telefone), emailContato: s(r.email_contato),
    contatoEmergencia: s(r.contato_emergencia), version: Number(r.version), updatedAt: String(r.updated_at),
    updatedBy: n(r.updated_by), syncStatus: String(r.sync_status),
  };
}

export class ProntuarioRepository {
  constructor(private b: Banco) {}

  daPessoa(pessoaId: string): Prontuario | null {
    const r = this.b.get<Linha>('SELECT * FROM prontuario WHERE pessoa_id = ?', pessoaId);
    return r ? lerProntuario(r) : null;
  }

  buscar(id: string): Prontuario | null {
    const r = this.b.get<Linha>('SELECT * FROM prontuario WHERE id = ?', id);
    return r ? lerProntuario(r) : null;
  }

  gravar(p: Prontuario, syncStatus: string) {
    this.b.run(`INSERT INTO prontuario (id, pessoa_id, comorbidades, uso_continuo, observacoes, version, updated_at,
        updated_by, sync_status) VALUES (?,?,?,?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET pessoa_id=excluded.pessoa_id, comorbidades=excluded.comorbidades,
        uso_continuo=excluded.uso_continuo, observacoes=excluded.observacoes, version=excluded.version,
        updated_at=excluded.updated_at, updated_by=excluded.updated_by, sync_status=excluded.sync_status`,
      p.id, p.pessoaId, v(p.comorbidades), v(p.usoContinuo), v(p.observacoes), p.version ?? 0, p.updatedAt,
      v(p.updatedBy), syncStatus);
  }
}

function lerProntuario(r: Linha): Prontuario {
  return {
    id: String(r.id), pessoaId: String(r.pessoa_id), comorbidades: s(r.comorbidades), usoContinuo: s(r.uso_continuo),
    observacoes: s(r.observacoes), version: Number(r.version), updatedAt: String(r.updated_at),
    updatedBy: n(r.updated_by), syncStatus: String(r.sync_status),
  };
}

export class AtendimentoRepository {
  constructor(private b: Banco) {}

  listar(prontuarioId?: string): Atendimento[] {
    const rows = prontuarioId
      ? this.b.all<Linha>('SELECT * FROM atendimento WHERE prontuario_id = ? ORDER BY inicio DESC', prontuarioId)
      : this.b.all<Linha>('SELECT * FROM atendimento ORDER BY inicio DESC');
    return rows.map((r) => this.montar(r));
  }

  buscar(id: string): Atendimento | null {
    const r = this.b.get<Linha>('SELECT * FROM atendimento WHERE id = ?', id);
    return r ? this.montar(r) : null;
  }

  gravar(a: Atendimento, syncStatus: string) {
    const g = a.glasgow ?? {};
    this.b.run(`INSERT INTO atendimento (id, prontuario_id, profissional_id, device_id, inicio, fim, local, queixa_principal,
        glasgow_ocular, glasgow_verbal, glasgow_motora, glasgow_total, triagem_manchester, triagem_start, conduta, destino,
        status, criado_offline, version, updated_at, sync_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET prontuario_id=excluded.prontuario_id, profissional_id=excluded.profissional_id,
        device_id=excluded.device_id, inicio=excluded.inicio, fim=excluded.fim, local=excluded.local,
        queixa_principal=excluded.queixa_principal, glasgow_ocular=excluded.glasgow_ocular,
        glasgow_verbal=excluded.glasgow_verbal, glasgow_motora=excluded.glasgow_motora,
        glasgow_total=excluded.glasgow_total, triagem_manchester=excluded.triagem_manchester,
        triagem_start=excluded.triagem_start, conduta=excluded.conduta, destino=excluded.destino, status=excluded.status,
        criado_offline=excluded.criado_offline, version=excluded.version, updated_at=excluded.updated_at,
        sync_status=excluded.sync_status`,
      a.id, a.prontuarioId, a.profissionalId, v(a.deviceId), a.inicio, v(a.fim), v(a.local), v(a.queixaPrincipal),
      v(g.ocular), v(g.verbal), v(g.motora), v(g.total), v(a.triagemManchester), v(a.triagemStart), v(a.conduta),
      v(a.destino), a.status ?? 'ABERTO', v(!!a.criadoOffline), a.version ?? 0, a.updatedAt, syncStatus);
    this.b.run('DELETE FROM sinal_vital WHERE atendimento_id = ?', a.id);
    for (const x of a.sinaisVitais ?? []) {
      this.b.run(`INSERT INTO sinal_vital (id, atendimento_id, aferido_em, pa_sistolica, pa_diastolica, fc, fr, spo2,
          temperatura, glicemia) VALUES (?,?,?,?,?,?,?,?,?,?)`,
        x.id, a.id, x.aferidoEm, v(x.paSistolica), v(x.paDiastolica), v(x.fc), v(x.fr), v(x.spo2), v(x.temperatura),
        v(x.glicemia));
    }
    this.b.run('DELETE FROM medicacao_administrada WHERE atendimento_id = ?', a.id);
    for (const m of a.medicacoes ?? []) {
      this.b.run(`INSERT INTO medicacao_administrada (id, atendimento_id, medicamento_id, dose, unidade, via,
          administrado_em, profissional_id, alerta_confirmado) VALUES (?,?,?,?,?,?,?,?,?)`,
        m.id, a.id, m.medicamentoId, m.dose, m.unidade, v(m.via), m.administradoEm, v(m.profissionalId),
        v(!!m.alertaConfirmado));
    }
  }

  private montar(r: Linha): Atendimento {
    const id = String(r.id);
    const sinais = this.b.all<Linha>('SELECT * FROM sinal_vital WHERE atendimento_id = ? ORDER BY aferido_em', id)
      .map((x): SinalVital => ({
        id: String(x.id), aferidoEm: String(x.aferido_em), paSistolica: n(x.pa_sistolica), paDiastolica: n(x.pa_diastolica),
        fc: n(x.fc), fr: n(x.fr), spo2: n(x.spo2), temperatura: n(x.temperatura), glicemia: n(x.glicemia),
      }));
    const meds = this.b.all<Linha>('SELECT * FROM medicacao_administrada WHERE atendimento_id = ? ORDER BY administrado_em', id)
      .map((x): Medicacao => ({
        id: String(x.id), medicamentoId: Number(x.medicamento_id), dose: Number(x.dose), unidade: String(x.unidade),
        via: s(x.via), administradoEm: String(x.administrado_em), profissionalId: n(x.profissional_id),
        alertaConfirmado: Number(x.alerta_confirmado) === 1,
      }));
    return {
      id, prontuarioId: String(r.prontuario_id), profissionalId: Number(r.profissional_id), deviceId: s(r.device_id),
      inicio: String(r.inicio), fim: s(r.fim), local: s(r.local), queixaPrincipal: s(r.queixa_principal),
      glasgow: { ocular: n(r.glasgow_ocular), verbal: n(r.glasgow_verbal), motora: n(r.glasgow_motora), total: n(r.glasgow_total) },
      triagemManchester: s(r.triagem_manchester), triagemStart: s(r.triagem_start), conduta: s(r.conduta),
      destino: s(r.destino), status: String(r.status), criadoOffline: Number(r.criado_offline) === 1,
      version: Number(r.version), updatedAt: String(r.updated_at), syncStatus: String(r.sync_status),
      sinaisVitais: sinais, medicacoes: meds,
    };
  }
}

export class MedicamentoRepository {
  constructor(private b: Banco) {}

  listar(): Medicamento[] {
    return this.b.all<Linha>('SELECT * FROM medicamento ORDER BY nome').map(lerMedicamento);
  }

  buscar(id: number): Medicamento | null {
    const r = this.b.get<Linha>('SELECT * FROM medicamento WHERE id = ?', id);
    return r ? lerMedicamento(r) : null;
  }

  gravar(m: Medicamento) {
    this.b.run(`INSERT INTO medicamento (id, nome, principio_ativo, apresentacao, dose_maxima, unidade, via_padrao, alertas,
        updated_at) VALUES (?,?,?,?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, principio_ativo=excluded.principio_ativo,
        apresentacao=excluded.apresentacao, dose_maxima=excluded.dose_maxima, unidade=excluded.unidade,
        via_padrao=excluded.via_padrao, alertas=excluded.alertas, updated_at=excluded.updated_at`,
      m.id, m.nome, m.principioAtivo, v(m.apresentacao), Number(m.doseMaxima), m.unidade, v(m.viaPadrao), v(m.alertas),
      v(m.updatedAt));
  }
}

function lerMedicamento(r: Linha): Medicamento {
  return {
    id: Number(r.id), nome: String(r.nome), principioAtivo: String(r.principio_ativo), apresentacao: s(r.apresentacao),
    doseMaxima: Number(r.dose_maxima), unidade: String(r.unidade), viaPadrao: s(r.via_padrao), alertas: s(r.alertas),
    updatedAt: s(r.updated_at) ?? undefined,
  };
}

export type ItemParaEnvio = ItemOutbox & { payload: string; chave: string };

/** Fila de alterações que ainda não chegaram ao servidor. */
export class OutboxRepository {
  constructor(private b: Banco) {}

  enfileirar(entidade: string, entidadeId: string, operacao: string, baseVersion: number, payload: unknown) {
    const json = JSON.stringify(payload);
    // Duas edições seguidas da mesma entidade, ainda nunca enviadas, viram um item só.
    const aberto = this.b.get<{ id: number }>(
      "SELECT id FROM outbox WHERE entidade = ? AND entidade_id = ? AND status = 'PENDENTE' AND tentativas = 0",
      entidade, entidadeId);
    if (aberto) {
      this.b.run('UPDATE outbox SET payload = ? WHERE id = ?', json, aberto.id);
      return;
    }
    // A chave de idempotência é um UUID do item: continua única mesmo se o banco local for recriado.
    this.b.run('INSERT INTO outbox (entidade, entidade_id, operacao, base_version, payload, criado_em, chave) VALUES (?,?,?,?,?,?,?)',
      entidade, entidadeId, operacao, baseVersion, json, new Date().toISOString(), randomUUID());
  }

  paraEnviar(limite = 50): ItemParaEnvio[] {
    return this.b.all<Linha>(
      "SELECT * FROM outbox WHERE status = 'PENDENTE' OR (status = 'ERRO' AND tentativas < 5) ORDER BY id LIMIT ?", limite)
      .map((r) => ({ ...lerItem(r), payload: String(r.payload), chave: r.chave ? String(r.chave) : `${r.id}` }));
  }

  listar(): ItemOutbox[] {
    return this.b.all<Linha>("SELECT * FROM outbox ORDER BY id DESC LIMIT 200").map(lerItem);
  }

  marcarEnviado(id: number) {
    this.b.run("UPDATE outbox SET status = 'ENVIADO', ultimo_erro = NULL WHERE id = ?", id);
  }

  marcarErro(id: number, erro: string) {
    this.b.run("UPDATE outbox SET status = 'ERRO', tentativas = tentativas + 1, ultimo_erro = ? WHERE id = ?", erro, id);
  }

  incrementarTentativa(id: number) {
    this.b.run('UPDATE outbox SET tentativas = tentativas + 1 WHERE id = ?', id);
  }

  pendentesDe(entidade: string, entidadeId: string): number {
    return this.b.get<{ c: number }>(
      "SELECT count(*) c FROM outbox WHERE entidade = ? AND entidade_id = ? AND status <> 'ENVIADO'", entidade, entidadeId)!.c;
  }

  contagem(): { pendencias: number; erros: number } {
    const r = this.b.get<{ p: number; e: number }>(
      "SELECT sum(status <> 'ENVIADO') p, sum(status = 'ERRO') e FROM outbox")!;
    return { pendencias: Number(r.p ?? 0), erros: Number(r.e ?? 0) };
  }
}

function lerItem(r: Linha): ItemOutbox {
  return {
    id: Number(r.id), entidade: String(r.entidade), entidadeId: String(r.entidade_id), operacao: String(r.operacao),
    baseVersion: Number(r.base_version), criadoEm: String(r.criado_em), tentativas: Number(r.tentativas),
    status: String(r.status), ultimoErro: s(r.ultimo_erro),
  };
}

export class LogRepository {
  constructor(private b: Banco) {}

  registrar(acao: string, entidade: string | null, entidadeId: string | null, profissionalId: number | null) {
    this.b.run('INSERT INTO local_log (data_hora, acao, entidade, entidade_id, profissional_id) VALUES (?,?,?,?,?)',
      new Date().toISOString(), acao, entidade, entidadeId, profissionalId);
  }

  naoEnviados(): (LogLocal & { profissionalId: number | null })[] {
    return this.b.all<Linha>('SELECT * FROM local_log WHERE enviado = 0 ORDER BY id').map((r) => ({
      ...lerLog(r), profissionalId: n(r.profissional_id),
    }));
  }

  marcarEnviados(ids: number[]) {
    for (const id of ids) this.b.run('UPDATE local_log SET enviado = 1 WHERE id = ?', id);
  }

  listar(): LogLocal[] {
    return this.b.all<Linha>('SELECT * FROM local_log ORDER BY id DESC LIMIT 200').map(lerLog);
  }
}

function lerLog(r: Linha): LogLocal {
  return {
    id: Number(r.id), dataHora: String(r.data_hora), acao: String(r.acao), entidade: s(r.entidade),
    entidadeId: s(r.entidade_id), enviado: Number(r.enviado) === 1,
  };
}

export type SessaoLocal = Profissional & { token: string | null; senhaHash: string; expiraEm: string | null };

export class SessaoRepository {
  constructor(private b: Banco) {}

  ativa(): SessaoLocal | null {
    const r = this.b.get<Linha>('SELECT * FROM sessao WHERE ativa = 1');
    return r ? lerSessao(r) : null;
  }

  porRegistro(registro: string, tipo: string): SessaoLocal | null {
    const r = this.b.get<Linha>('SELECT * FROM sessao WHERE registro = ? AND tipo = ?', registro, tipo);
    return r ? lerSessao(r) : null;
  }

  salvar(p: Profissional, token: string | null, senhaHash: string, expiraEm: string | null) {
    this.b.transacao(() => {
      this.b.run('UPDATE sessao SET ativa = 0');
      this.b.run(`INSERT INTO sessao (profissional_id, nome, registro, tipo, perfil, token, senha_hash, expira_em, ativa)
          VALUES (?,?,?,?,?,?,?,?,1)
        ON CONFLICT(profissional_id) DO UPDATE SET nome=excluded.nome, registro=excluded.registro, tipo=excluded.tipo,
          perfil=excluded.perfil, token=excluded.token, senha_hash=excluded.senha_hash, expira_em=excluded.expira_em, ativa=1`,
        p.id, p.nome, p.registro, p.tipo, p.perfil, token, senhaHash, expiraEm);
    });
  }

  ativar(profissionalId: number) {
    this.b.transacao(() => {
      this.b.run('UPDATE sessao SET ativa = 0');
      this.b.run('UPDATE sessao SET ativa = 1 WHERE profissional_id = ?', profissionalId);
    });
  }

  encerrar() {
    this.b.run('UPDATE sessao SET ativa = 0');
  }
}

function lerSessao(r: Linha): SessaoLocal {
  return {
    id: Number(r.profissional_id), nome: String(r.nome), registro: String(r.registro), tipo: String(r.tipo),
    perfil: String(r.perfil), token: s(r.token), senhaHash: String(r.senha_hash), expiraEm: s(r.expira_em),
  };
}

export class EstadoRepository {
  constructor(private b: Banco) {}

  ler(chave: string): string | null {
    return this.b.get<{ valor: string }>('SELECT valor FROM sync_state WHERE chave = ?', chave)?.valor ?? null;
  }

  gravar(chave: string, valor: string) {
    this.b.run('INSERT INTO sync_state (chave, valor) VALUES (?, ?) ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor',
      chave, valor);
  }
}
