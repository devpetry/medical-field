import { DatabaseSync } from 'node:sqlite';

/** Banco local embarcado (SQLite). Toda gravação acontece aqui primeiro. */
const SCHEMA = `
CREATE TABLE IF NOT EXISTS pessoa (
  id TEXT PRIMARY KEY, nome TEXT NOT NULL, cpf TEXT, data_nascimento TEXT, sexo TEXT, tipo_sanguineo TEXT,
  alergias TEXT, telefone TEXT, email_contato TEXT, contato_emergencia TEXT,
  version INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, updated_by INTEGER,
  sync_status TEXT NOT NULL DEFAULT 'PENDENTE');
CREATE TABLE IF NOT EXISTS prontuario (
  id TEXT PRIMARY KEY, pessoa_id TEXT NOT NULL REFERENCES pessoa(id), comorbidades TEXT, uso_continuo TEXT,
  observacoes TEXT, version INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, updated_by INTEGER,
  sync_status TEXT NOT NULL DEFAULT 'PENDENTE');
CREATE TABLE IF NOT EXISTS atendimento (
  id TEXT PRIMARY KEY, prontuario_id TEXT NOT NULL REFERENCES prontuario(id), profissional_id INTEGER NOT NULL,
  device_id TEXT, inicio TEXT NOT NULL, fim TEXT, local TEXT, queixa_principal TEXT,
  glasgow_ocular INTEGER, glasgow_verbal INTEGER, glasgow_motora INTEGER, glasgow_total INTEGER,
  triagem_manchester TEXT, triagem_start TEXT, conduta TEXT, destino TEXT, status TEXT NOT NULL DEFAULT 'ABERTO',
  criado_offline INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
  sync_status TEXT NOT NULL DEFAULT 'PENDENTE');
CREATE TABLE IF NOT EXISTS sinal_vital (
  id TEXT PRIMARY KEY, atendimento_id TEXT NOT NULL REFERENCES atendimento(id) ON DELETE CASCADE,
  aferido_em TEXT NOT NULL, pa_sistolica INTEGER, pa_diastolica INTEGER, fc INTEGER, fr INTEGER, spo2 INTEGER,
  temperatura REAL, glicemia INTEGER);
CREATE TABLE IF NOT EXISTS medicacao_administrada (
  id TEXT PRIMARY KEY, atendimento_id TEXT NOT NULL REFERENCES atendimento(id) ON DELETE CASCADE,
  medicamento_id INTEGER NOT NULL, dose REAL NOT NULL, unidade TEXT NOT NULL, via TEXT, administrado_em TEXT NOT NULL,
  profissional_id INTEGER, alerta_confirmado INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS medicamento (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, principio_ativo TEXT NOT NULL, apresentacao TEXT,
  dose_maxima REAL NOT NULL, unidade TEXT NOT NULL, via_padrao TEXT, alertas TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, entidade TEXT NOT NULL, entidade_id TEXT NOT NULL, operacao TEXT NOT NULL,
  base_version INTEGER NOT NULL DEFAULT 0, payload TEXT NOT NULL, criado_em TEXT NOT NULL,
  tentativas INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'PENDENTE', ultimo_erro TEXT, chave TEXT);
CREATE TABLE IF NOT EXISTS local_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT NOT NULL, acao TEXT NOT NULL, entidade TEXT,
  entidade_id TEXT, profissional_id INTEGER, enviado INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS sessao (
  profissional_id INTEGER PRIMARY KEY, nome TEXT NOT NULL, registro TEXT NOT NULL, tipo TEXT NOT NULL,
  perfil TEXT NOT NULL, token TEXT, senha_hash TEXT NOT NULL, expira_em TEXT, ativa INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS sync_state (chave TEXT PRIMARY KEY, valor TEXT);
`;

export type Valor = string | number | null;

export class Banco {
  readonly db: DatabaseSync;

  constructor(arquivo: string) {
    this.db = new DatabaseSync(arquivo);
    this.db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON;');
    this.db.exec(SCHEMA);
    // Bancos criados antes da coluna chave (chave de idempotência por item).
    const cols = this.all<{ name: string }>('PRAGMA table_info(outbox)').map((c) => c.name);
    if (!cols.includes('chave')) this.db.exec('ALTER TABLE outbox ADD COLUMN chave TEXT');
  }

  all<T>(sql: string, ...p: Valor[]): T[] {
    return this.db.prepare(sql).all(...p) as T[];
  }

  get<T>(sql: string, ...p: Valor[]): T | undefined {
    return this.db.prepare(sql).get(...p) as T | undefined;
  }

  run(sql: string, ...p: Valor[]) {
    return this.db.prepare(sql).run(...p);
  }

  /** Executa fn numa transação: o registro e o item da Outbox entram juntos ou nenhum entra. */
  transacao<T>(fn: () => T): T {
    this.db.exec('BEGIN');
    try {
      const r = fn();
      this.db.exec('COMMIT');
      return r;
    } catch (e) {
      this.db.exec('ROLLBACK');
      throw e;
    }
  }
}

/** Converte undefined/boolean para valores aceitos pelo SQLite. */
export function v(x: unknown): Valor {
  if (x === undefined || x === null || x === '') return null;
  if (typeof x === 'boolean') return x ? 1 : 0;
  if (typeof x === 'number' || typeof x === 'string') return x;
  return String(x);
}
