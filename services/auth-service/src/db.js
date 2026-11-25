import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';
import { config } from './config.js';

export const pool = new pg.Pool(config.db);

/** Aplica, em ordem, os arquivos de migrations/ ainda não executados. */
export async function migrar() {
  const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'migrations');
  await pool.query(`CREATE TABLE IF NOT EXISTS auth.schema_migrations (
    arquivo VARCHAR(100) PRIMARY KEY, aplicado_em TIMESTAMPTZ NOT NULL DEFAULT now())`);
  const feitos = new Set((await pool.query('SELECT arquivo FROM auth.schema_migrations')).rows.map((r) => r.arquivo));
  for (const arquivo of (await readdir(dir)).filter((f) => f.endsWith('.sql')).sort()) {
    if (feitos.has(arquivo)) continue;
    const sql = await readFile(path.join(dir, arquivo), 'utf8');
    const c = await pool.connect();
    try {
      await c.query('BEGIN');
      await c.query(sql);
      await c.query('INSERT INTO auth.schema_migrations (arquivo) VALUES ($1)', [arquivo]);
      await c.query('COMMIT');
      console.log(`migração aplicada: ${arquivo}`);
    } catch (e) {
      await c.query('ROLLBACK');
      throw e;
    } finally {
      c.release();
    }
  }
}
