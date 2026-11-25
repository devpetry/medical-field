import type { Atendimento, Medicamento, Pessoa, Profissional, Prontuario } from '../shared/tipos';

export class OfflineError extends Error {
  constructor() {
    super('Sem conexão com o servidor');
  }
}

export class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export type PushItem = { outboxId: number; chave: string; entidade: string; operacao: string; baseVersion: number; payload: unknown };
export type PushResultado = { outboxId: number; status: string; vencedor?: string; versao?: number; mensagem?: string };
export type PullResposta = {
  medicamentos: Medicamento[]; pessoas: Pessoa[]; prontuarios: Prontuario[]; atendimentos: Atendimento[]; serverTime: string;
};

/**
 * Repositório remoto (REST via Nginx). Quando a chave "Simular Conectividade"
 * está em OFFLINE, nenhuma chamada sai do dispositivo.
 */
export class ApiClient {
  token: string | null = null;

  constructor(public baseUrl: string, private deviceId: string, private permitido: () => boolean) {}

  private async req(path: string, init: RequestInit = {}, timeoutMs = 10000): Promise<Response> {
    if (!this.permitido()) throw new OfflineError();
    const headers = new Headers(init.headers);
    headers.set('X-Device-Id', this.deviceId);
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`);
    if (init.body) headers.set('Content-Type', 'application/json');
    let r: Response;
    try {
      r = await fetch(this.baseUrl + path, { ...init, headers, signal: AbortSignal.timeout(timeoutMs) });
    } catch {
      throw new OfflineError();
    }
    if (!r.ok) {
      let msg = `HTTP ${r.status}`;
      try {
        msg = ((await r.json()) as { erro?: string }).erro ?? msg;
      } catch {
        /* sem JSON */
      }
      throw new HttpError(r.status, msg);
    }
    return r;
  }

  /** Qualquer resposta HTTP (até 401) prova que o servidor está alcançável. */
  async ping(): Promise<boolean> {
    if (!this.permitido()) return false;
    try {
      await fetch(`${this.baseUrl}/auth/me`, {
        headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
        signal: AbortSignal.timeout(4000),
      });
      return true;
    } catch {
      return false;
    }
  }

  async login(registro: string, tipoRegistro: string, senha: string) {
    const r = await this.req('/auth/login', { method: 'POST', body: JSON.stringify({ registro, tipoRegistro, senha }) });
    return (await r.json()) as { accessToken: string; expiresIn: number; profissional: Profissional };
  }

  async push(itens: PushItem[]) {
    const r = await this.req('/sync/push', { method: 'POST', body: JSON.stringify({ deviceId: this.deviceId, itens }) }, 30000);
    return (await r.json()) as { resultados: PushResultado[]; serverTime: string };
  }

  async pull(since: string | null) {
    const q = since ? `?since=${encodeURIComponent(since)}` : '';
    return (await (await this.req(`/sync/pull${q}`, {}, 30000)).json()) as PullResposta;
  }

  async enviarLogs(logs: unknown[]) {
    await this.req('/log', { method: 'POST', body: JSON.stringify({ deviceId: this.deviceId, logs }) });
  }

  async fichaPdf(atendimentoId: string): Promise<Buffer> {
    const r = await this.req(`/documento/ficha/${atendimentoId}`, {}, 30000);
    return Buffer.from(await r.arrayBuffer());
  }

  async enviarFicha(atendimentoId: string, destinatario: string, nomeDestinatario: string | null, relacao: string) {
    const r = await this.req(`/documento/ficha/${atendimentoId}/email`, {
      method: 'POST', body: JSON.stringify({ destinatario, nomeDestinatario, relacao }),
    }, 30000);
    return (await r.json()) as { envioId: number; status: string };
  }
}
