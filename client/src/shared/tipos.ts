// Tipos compartilhados entre o processo principal e a interface.
export type Pessoa = {
  id: string; nome: string; cpf?: string | null; dataNascimento?: string | null; sexo?: string | null;
  tipoSanguineo?: string | null; alergias?: string | null; telefone?: string | null; emailContato?: string | null;
  contatoEmergencia?: string | null; version: number; updatedAt: string; updatedBy?: number | null; syncStatus?: string;
};

export type Prontuario = {
  id: string; pessoaId: string; comorbidades?: string | null; usoContinuo?: string | null; observacoes?: string | null;
  version: number; updatedAt: string; updatedBy?: number | null; syncStatus?: string;
};

export type SinalVital = {
  id: string; aferidoEm: string; paSistolica?: number | null; paDiastolica?: number | null; fc?: number | null;
  fr?: number | null; spo2?: number | null; temperatura?: number | null; glicemia?: number | null;
};

export type Medicacao = {
  id: string; medicamentoId: number; dose: number; unidade: string; via?: string | null; administradoEm: string;
  profissionalId?: number | null; alertaConfirmado: boolean;
};

export type Glasgow = { ocular?: number | null; verbal?: number | null; motora?: number | null; total?: number | null };

export type Atendimento = {
  id: string; prontuarioId: string; profissionalId: number; deviceId?: string | null; inicio: string; fim?: string | null;
  local?: string | null; queixaPrincipal?: string | null; glasgow: Glasgow; triagemManchester?: string | null;
  triagemStart?: string | null; conduta?: string | null; destino?: string | null; status: string; criadoOffline: boolean;
  version: number; updatedAt: string; syncStatus?: string; sinaisVitais: SinalVital[]; medicacoes: Medicacao[];
};

export type Medicamento = {
  id: number; nome: string; principioAtivo: string; apresentacao?: string | null; doseMaxima: number; unidade: string;
  viaPadrao?: string | null; alertas?: string | null; updatedAt?: string;
};

export type Profissional = { id: number; nome: string; registro: string; tipo: string; perfil: string };

export type ItemOutbox = {
  id: number; entidade: string; entidadeId: string; operacao: string; baseVersion: number; criadoEm: string;
  tentativas: number; status: string; ultimoErro?: string | null;
};

export type LogLocal = { id: number; dataHora: string; acao: string; entidade?: string | null; entidadeId?: string | null; enviado: boolean };

export type Estado = {
  online: boolean; simulacaoOnline: boolean; servidorAlcancavel: boolean; sincronizando: boolean;
  pendencias: number; erros: number; ultimoPull?: string | null; ultimaSync?: string | null; mensagem?: string | null;
  deviceId: string; apiUrl: string; profissional?: Profissional | null; tokenValido: boolean;
};

export type Alerta = { medicacaoId: string; mensagem: string };
export type ResultadoValidacao = { erros: string[]; alertas: Alerta[] };
