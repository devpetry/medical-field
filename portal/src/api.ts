// Cliente HTTP do portal: tudo passa por /api (Nginx em produção, proxy do Vite em dev).
export type Profissional = { id: number; nome: string; registro: string; tipo: string; perfil: string };
export type Sessao = { token: string; profissional: Profissional };

const CHAVE = 'mf.sessao';

export function lerSessao(): Sessao | null {
  try {
    const s = sessionStorage.getItem(CHAVE);
    return s ? (JSON.parse(s) as Sessao) : null;
  } catch {
    return null;
  }
}

export function salvarSessao(s: Sessao | null) {
  try {
    if (s) sessionStorage.setItem(CHAVE, JSON.stringify(s));
    else sessionStorage.removeItem(CHAVE);
  } catch {
    /* sem storage: a sessão vale só enquanto a página estiver aberta */
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

let aoExpirar: () => void = () => {};
export function quandoExpirar(fn: () => void) {
  aoExpirar = fn;
}

async function req(path: string, init: RequestInit = {}, token?: string): Promise<Response> {
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const r = await fetch(`/api${path}`, { ...init, headers });
  if (r.status === 401 && token) aoExpirar();
  if (!r.ok) {
    let msg = `Erro ${r.status}`;
    try {
      msg = (await r.json()).erro ?? msg;
    } catch {
      /* corpo sem JSON */
    }
    throw new ApiError(r.status, msg);
  }
  return r;
}

export async function login(registro: string, tipoRegistro: string, senha: string): Promise<Sessao> {
  const r = await req('/auth/login', { method: 'POST', body: JSON.stringify({ registro, tipoRegistro, senha }) });
  const j = await r.json();
  return { token: j.accessToken, profissional: j.profissional };
}

export async function get<T>(path: string, token: string): Promise<T> {
  return (await req(path, {}, token)).json();
}

export async function post<T>(path: string, body: unknown, token: string): Promise<T> {
  return (await req(path, { method: 'POST', body: JSON.stringify(body) }, token)).json();
}

export async function baixar(path: string, token: string, nomePadrao: string) {
  const r = await req(path, {}, token);
  const nome = /filename="([^"]+)"/.exec(r.headers.get('Content-Disposition') ?? '')?.[1] ?? nomePadrao;
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement('a');
  a.href = url;
  a.download = nome;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
