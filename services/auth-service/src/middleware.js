import jwt from 'jsonwebtoken';
import { config } from './config.js';
import { pool } from './db.js';

function ipCliente(req) {
  const xff = req.headers['x-forwarded-for'];
  return xff ? String(xff).split(',')[0].trim() : req.socket.remoteAddress;
}

function tokenDe(req) {
  const h = req.headers.authorization ?? '';
  return h.startsWith('Bearer ') ? h.slice(7) : null;
}

/** Log de acesso de cada requisição (primeiro elo da cadeia de middlewares). */
export function accessLog(req, res, next) {
  const inicio = new Date();
  const t0 = process.hrtime.bigint();
  res.on('finish', () => {
    const ms = Number((process.hrtime.bigint() - t0) / 1_000_000n);
    let profissional = req.profissional?.id ?? null;
    if (profissional == null) {
      try {
        const t = tokenDe(req);
        if (t) profissional = Number(jwt.verify(t, config.jwtSecret, { algorithms: ['HS256'] }).sub);
      } catch {
        profissional = null;
      }
    }
    const ip = ipCliente(req);
    const device = req.headers['x-device-id'] ?? null;
    console.log(`${req.method} ${req.originalUrl} ${res.statusCode} ${ms}ms prof=${profissional ?? '-'} ip=${ip}`);
    pool
      .query(
        `INSERT INTO audit.access_log
           (data_hora, servico, ip_cliente, profissional_id, metodo, rota, status_code, tempo_ms, origem, device_id)
         VALUES ($1, 'auth', $2, $3, $4, $5, $6, $7, 'ONLINE', $8)`,
        [inicio, ip, profissional, req.method, req.path, res.statusCode, ms, device],
      )
      .catch((e) => console.warn(`falha ao gravar access_log: ${e.message}`));
  });
  next();
}

/** Restringe a rota ao perfil ADMIN (portal administrativo). */
export function somenteAdmin(req, res, next) {
  if (req.profissional?.perfil !== 'ADMIN') return res.status(403).json({ erro: 'Acesso restrito a administradores' });
  next();
}

/** Exige JWT válido; o login é a única rota pública. */
export function autenticar(req, res, next) {
  const t = tokenDe(req);
  if (!t) return res.status(401).json({ erro: 'Token ausente, inválido ou expirado' });
  try {
    const c = jwt.verify(t, config.jwtSecret, { algorithms: ['HS256'] });
    req.profissional = { id: Number(c.sub), registro: c.registro, tipo: c.tipo, nome: c.nome, perfil: c.perfil };
    next();
  } catch {
    res.status(401).json({ erro: 'Token ausente, inválido ou expirado' });
  }
}
