import bcrypt from 'bcryptjs';
import express from 'express';
import jwt from 'jsonwebtoken';
import { config } from './config.js';
import { migrar, pool } from './db.js';
import { accessLog, autenticar, somenteAdmin } from './middleware.js';

const TIPOS = ['CRM', 'COREN', 'SOCORRISTA'];
const app = express();
app.disable('x-powered-by');
app.use(accessLog);
app.use(express.json({ limit: '100kb' }));

function publico(p) {
  return { id: Number(p.id), nome: p.nome, registro: p.registro, tipo: p.tipo_registro, perfil: p.perfil };
}

app.post('/auth/login', async (req, res, next) => {
  try {
    const { registro, tipoRegistro, senha } = req.body ?? {};
    if (!registro || !senha || (tipoRegistro && !TIPOS.includes(tipoRegistro))) {
      return res.status(400).json({ erro: 'Informe registro, tipoRegistro (CRM, COREN ou SOCORRISTA) e senha' });
    }
    const { rows } = await pool.query(
      'SELECT * FROM auth.profissional WHERE registro = $1 AND ativo AND ($2::text IS NULL OR tipo_registro = $2)',
      [String(registro).trim(), tipoRegistro ?? null],
    );
    const p = rows[0];
    if (!p || !(await bcrypt.compare(String(senha), p.senha_hash))) {
      return res.status(401).json({ erro: 'Registro ou senha inválidos' });
    }
    const perfil = publico(p);
    const accessToken = jwt.sign(
      { registro: perfil.registro, tipo: perfil.tipo, nome: perfil.nome, perfil: perfil.perfil },
      config.jwtSecret,
      { algorithm: 'HS256', subject: String(perfil.id), expiresIn: `${config.jwtTtlHours}h` },
    );
    req.profissional = perfil;
    res.json({ accessToken, expiresIn: config.jwtTtlHours * 3600, profissional: perfil });
  } catch (e) {
    next(e);
  }
});

app.use(autenticar);

app.get('/auth/me', (req, res) => res.json(req.profissional));

app.get('/profissional', somenteAdmin, async (_req, res, next) => {
  try {
    const { rows } = await pool.query(
      'SELECT id, nome, registro, tipo_registro, perfil, ativo, criado_em FROM auth.profissional ORDER BY nome',
    );
    res.json(rows.map((r) => ({ ...publico(r), ativo: r.ativo, criadoEm: r.criado_em })));
  } catch (e) {
    next(e);
  }
});

app.use((_req, res) => res.status(404).json({ erro: 'Rota não encontrada' }));
app.use((err, _req, res, _next) => {
  if (err.type === 'entity.parse.failed') return res.status(400).json({ erro: 'JSON inválido' });
  console.error(err);
  res.status(500).json({ erro: 'Erro interno' });
});

await migrar();
app.listen(config.port, config.bind, () => console.log(`auth-service em http://${config.bind}:${config.port}`));
