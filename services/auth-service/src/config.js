function obrigatoria(nome) {
  const v = process.env[nome];
  if (!v) throw new Error(`Variável de ambiente ${nome} não definida`);
  return v;
}

// O pg ignora user/password quando há connectionString: as credenciais entram na URL.
const dbUrl = new URL(obrigatoria('DB_URL'));
if (process.env.DB_USER) dbUrl.username = process.env.DB_USER;
if (process.env.DB_PASSWORD) dbUrl.password = process.env.DB_PASSWORD;

export const config = {
  port: Number(process.env.PORT ?? 3001),
  bind: process.env.BIND_ADDRESS ?? '127.0.0.1',
  jwtSecret: obrigatoria('JWT_SECRET'),
  jwtTtlHours: Number(process.env.JWT_TTL_HOURS ?? 12),
  db: { connectionString: dbUrl.toString() },
};

if (config.jwtSecret.length < 32) throw new Error('JWT_SECRET deve ter pelo menos 32 caracteres');
