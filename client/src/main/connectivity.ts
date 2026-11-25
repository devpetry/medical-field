import type { ApiClient } from './api';

type Ouvinte = (online: boolean) => void;

/**
 * Observer: acompanha a chave "Simular Conectividade" e a alcançabilidade do
 * servidor (GET /auth/me a cada 15 s) e avisa os inscritos quando muda.
 */
export class ConnectivityMonitor {
  simulacaoOnline = true;
  servidorAlcancavel = false;
  private ouvintes: Ouvinte[] = [];
  private timer: NodeJS.Timeout | null = null;
  private ultimo = false;

  constructor(private api: () => ApiClient, private intervaloMs = 15000) {}

  get online() {
    return this.simulacaoOnline && this.servidorAlcancavel;
  }

  inscrever(fn: Ouvinte) {
    this.ouvintes.push(fn);
    return () => { this.ouvintes = this.ouvintes.filter((o) => o !== fn); };
  }

  iniciar() {
    void this.verificar();
    this.timer = setInterval(() => void this.verificar(), this.intervaloMs);
  }

  parar() {
    if (this.timer) clearInterval(this.timer);
  }

  async definirSimulacao(online: boolean) {
    this.simulacaoOnline = online;
    await this.verificar();
  }

  async verificar() {
    this.servidorAlcancavel = this.simulacaoOnline ? await this.api().ping() : false;
    this.notificarSeMudou();
  }

  private notificarSeMudou() {
    const agora = this.online;
    if (agora !== this.ultimo) {
      this.ultimo = agora;
      for (const o of this.ouvintes) o(agora);
    }
  }
}
