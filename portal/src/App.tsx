import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError, Sessao, baixar, get, lerSessao, login, post, quandoExpirar, salvarSessao } from './api';
import { CORES_TRIAGEM, data, dataHora, texto } from './format';

type Medicamento = { id: number; nome: string; principioAtivo: string; apresentacao?: string; doseMaxima: number; unidade: string; viaPadrao?: string; alertas?: string; updatedAt: string };
type Pessoa = { id: string; nome: string; cpf?: string; dataNascimento?: string; sexo?: string; tipoSanguineo?: string; alergias?: string; telefone?: string; updatedAt: string };
type Prontuario = { id: string; pessoaId: string; comorbidades?: string; usoContinuo?: string; observacoes?: string; version: number; updatedAt: string };
type SinalVital = { id: string; aferidoEm: string; paSistolica?: number; paDiastolica?: number; fc?: number; fr?: number; spo2?: number; temperatura?: number; glicemia?: number };
type Medicacao = { id: string; medicamentoId: number; dose: number; unidade: string; via?: string; administradoEm: string; alertaConfirmado?: boolean };
type Atendimento = {
  id: string; prontuarioId: string; profissionalId: number; deviceId?: string; inicio: string; local?: string; queixaPrincipal?: string;
  glasgow?: { ocular?: number; verbal?: number; motora?: number; total?: number }; triagemManchester?: string; triagemStart?: string;
  conduta?: string; destino?: string; status: string; criadoOffline: boolean; version: number; sincronizadoEm: string;
  sinaisVitais: SinalVital[]; medicacoes: Medicacao[];
};
type ProfissionalLista = { id: number; nome: string; registro: string; tipo: string; perfil: string; ativo: boolean };
type Registro = Record<string, unknown>;

const SECOES = ['Profissionais', 'Medicamentos', 'Pessoas', 'Prontuários', 'Atendimentos', 'Auditoria', 'E-mails enviados'] as const;
type Secao = (typeof SECOES)[number];

export default function App() {
  const [sessao, setSessao] = useState<Sessao | null>(lerSessao);
  const sair = useCallback(() => {
    salvarSessao(null);
    setSessao(null);
  }, []);
  useEffect(() => quandoExpirar(sair), [sair]);
  if (!sessao) return <Login onEntrar={(s) => { salvarSessao(s); setSessao(s); }} />;
  return <Painel sessao={sessao} onSair={sair} />;
}

function Logo({ tamanho = 22 }: { tamanho?: number }) {
  return (
    <span className="logo" style={{ fontSize: tamanho }}>
      <span className="logo-marca">✚</span>
      <span>Medical<b>Field</b></span>
    </span>
  );
}

function Login({ onEntrar }: { onEntrar: (s: Sessao) => void }) {
  const [registro, setRegistro] = useState('');
  const [tipo, setTipo] = useState('CRM');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function entrar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    setEnviando(true);
    try {
      const sessao = await login(registro.trim(), tipo, senha);
      if (sessao.profissional.perfil !== 'ADMIN') {
        setErro('Acesso restrito a administradores. Socorristas usam o cliente desktop.');
        return;
      }
      onEntrar(sessao);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Servidor indisponível');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login">
      <form className="login-card" onSubmit={entrar}>
        <Logo tamanho={30} />
        <p className="sub">Portal administrativo</p>
        <div className="chips">
          {(['CRM', 'COREN', 'SOCORRISTA'] as const).map((t) => (
            <button type="button" key={t} className={tipo === t ? 'chip ativo' : 'chip'} onClick={() => setTipo(t)}>
              {t === 'SOCORRISTA' ? 'ID Socorrista' : t}
            </button>
          ))}
        </div>
        <label>Registro<input value={registro} onChange={(e) => setRegistro(e.target.value)} placeholder="CRM-RS 12345" autoFocus required /></label>
        <label>Senha<input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required /></label>
        {erro && <div className="erro">{erro}</div>}
        <button className="primario" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</button>
      </form>
    </div>
  );
}

function Painel({ sessao, onSair }: { sessao: Sessao; onSair: () => void }) {
  const [secao, setSecao] = useState<Secao>('Atendimentos');
  const [versao, setVersao] = useState(0);
  return (
    <div className="painel">
      <aside>
        <Logo />
        <nav>
          {SECOES.map((s) => (
            <button key={s} className={s === secao ? 'ativo' : ''} onClick={() => setSecao(s)}>{s}</button>
          ))}
        </nav>
        <div className="usuario">
          <div>{sessao.profissional.nome}</div>
          <small>{sessao.profissional.registro}</small>
          <button className="link" onClick={onSair}>Sair</button>
        </div>
      </aside>
      <main>
        <header>
          <h1>{secao}</h1>
          <button className="secundario" onClick={() => setVersao((v) => v + 1)}>↻ Atualizar</button>
        </header>
        <Conteudo key={`${secao}-${versao}`} secao={secao} token={sessao.token} />
      </main>
    </div>
  );
}

function useDados<T>(carregar: () => Promise<T>) {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState('');
  useEffect(() => {
    let vivo = true;
    carregar().then((d) => vivo && setDados(d)).catch((e) => vivo && setErro(e instanceof Error ? e.message : 'Erro'));
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return { dados, erro };
}

function Conteudo({ secao, token }: { secao: Secao; token: string }) {
  switch (secao) {
    case 'Profissionais': return <Profissionais token={token} />;
    case 'Medicamentos': return <Medicamentos token={token} />;
    case 'Pessoas': return <Pessoas token={token} />;
    case 'Prontuários': return <Prontuarios token={token} />;
    case 'Atendimentos': return <Atendimentos token={token} />;
    case 'Auditoria': return <Auditoria token={token} />;
    case 'E-mails enviados': return <Envios token={token} />;
  }
}

type Coluna<T> = { titulo: string; valor: (r: T) => ReactNode; mono?: boolean };

function Tabela<T>({ colunas, linhas, chave, onClique, destaque }: {
  colunas: Coluna<T>[]; linhas: T[] | null; chave: (r: T) => string | number; onClique?: (r: T) => void; destaque?: (r: T) => boolean;
}) {
  if (!linhas) return <p className="vazio">Carregando…</p>;
  if (!linhas.length) return <p className="vazio">Nenhum registro.</p>;
  return (
    <div className="tabela-wrap">
      <table>
        <thead><tr>{colunas.map((c) => <th key={c.titulo}>{c.titulo}</th>)}</tr></thead>
        <tbody>
          {linhas.map((r) => (
            <tr key={chave(r)} onClick={onClique && (() => onClique(r))} className={`${onClique ? 'clicavel' : ''} ${destaque?.(r) ? 'destaque' : ''}`}>
              {colunas.map((c) => <td key={c.titulo} className={c.mono ? 'mono' : ''}>{c.valor(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Erro({ msg }: { msg: string }) {
  return msg ? <div className="erro">{msg}</div> : null;
}

function Triagem({ v }: { v?: string }) {
  if (!v) return <>—</>;
  return <span className="triagem"><i style={{ background: CORES_TRIAGEM[v] ?? '#94a3b8' }} />{v.charAt(0) + v.slice(1).toLowerCase()}</span>;
}

function Profissionais({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<ProfissionalLista[]>('/profissional', token));
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => r.id} colunas={[
    { titulo: 'Nome', valor: (r) => r.nome }, { titulo: 'Registro', valor: (r) => r.registro, mono: true },
    { titulo: 'Tipo', valor: (r) => r.tipo }, { titulo: 'Perfil', valor: (r) => r.perfil },
    { titulo: 'Ativo', valor: (r) => (r.ativo ? 'sim' : 'não') },
  ]} /></>);
}

function Medicamentos({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<Medicamento[]>('/medicamento', token));
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => r.id} colunas={[
    { titulo: 'Nome', valor: (r) => r.nome }, { titulo: 'Princípio ativo', valor: (r) => r.principioAtivo },
    { titulo: 'Apresentação', valor: (r) => texto(r.apresentacao) },
    { titulo: 'Dose máxima', valor: (r) => `${r.doseMaxima} ${r.unidade}` }, { titulo: 'Via', valor: (r) => texto(r.viaPadrao) },
    { titulo: 'Alertas', valor: (r) => texto(r.alertas) }, { titulo: 'Atualizado', valor: (r) => dataHora(r.updatedAt) },
  ]} /></>);
}

function Pessoas({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<Pessoa[]>('/pessoa', token));
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => r.id} colunas={[
    { titulo: 'Nome', valor: (r) => r.nome }, { titulo: 'CPF', valor: (r) => texto(r.cpf), mono: true },
    { titulo: 'Nascimento', valor: (r) => data(r.dataNascimento) }, { titulo: 'Tipo sang.', valor: (r) => texto(r.tipoSanguineo) },
    { titulo: 'Alergias', valor: (r) => texto(r.alergias) }, { titulo: 'Telefone', valor: (r) => texto(r.telefone) },
  ]} /></>);
}

function useMapaPessoas(token: string) {
  const { dados } = useDados(() => get<Pessoa[]>('/pessoa', token));
  return useMemo(() => new Map((dados ?? []).map((p) => [p.id, p])), [dados]);
}

function Prontuarios({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<Prontuario[]>('/prontuario', token));
  const pessoas = useMapaPessoas(token);
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => r.id} colunas={[
    { titulo: 'Pessoa', valor: (r) => pessoas.get(r.pessoaId)?.nome ?? '…' },
    { titulo: 'Comorbidades', valor: (r) => texto(r.comorbidades) }, { titulo: 'Uso contínuo', valor: (r) => texto(r.usoContinuo) },
    { titulo: 'Observações', valor: (r) => texto(r.observacoes) }, { titulo: 'Versão', valor: (r) => r.version },
    { titulo: 'Atualizado em', valor: (r) => dataHora(r.updatedAt) },
  ]} /></>);
}

function Atendimentos({ token }: { token: string }) {
  const { dados, erro } = useDados(async () => {
    const [ats, prs, pes, meds] = await Promise.all([
      get<Atendimento[]>('/atendimento', token), get<Prontuario[]>('/prontuario', token),
      get<Pessoa[]>('/pessoa', token), get<Medicamento[]>('/medicamento', token),
    ]);
    const pessoaDe = new Map(prs.map((p) => [p.id, pes.find((x) => x.id === p.pessoaId)]));
    return { ats, pessoaDe, meds: new Map(meds.map((m) => [m.id, m])) };
  });
  const [aberto, setAberto] = useState<Atendimento | null>(null);
  return (
    <>
      <Erro msg={erro} />
      <Tabela linhas={dados?.ats ?? null} chave={(r) => r.id} onClique={setAberto} destaque={(r) => r.criadoOffline}
        colunas={[
          { titulo: 'Início', valor: (r) => dataHora(r.inicio) },
          { titulo: 'Pessoa', valor: (r) => dados?.pessoaDe.get(r.prontuarioId)?.nome ?? '—' },
          { titulo: 'Local', valor: (r) => texto(r.local) },
          { titulo: 'Glasgow', valor: (r) => texto(r.glasgow?.total) },
          { titulo: 'Manchester', valor: (r) => <Triagem v={r.triagemManchester} /> },
          { titulo: 'START', valor: (r) => <Triagem v={r.triagemStart} /> },
          { titulo: 'Origem', valor: (r) => (r.criadoOffline ? <span className="badge offline">criado offline</span> : <span className="badge">online</span>) },
        ]} />
      {aberto && dados && (
        <Detalhe at={aberto} pessoa={dados.pessoaDe.get(aberto.prontuarioId)} meds={dados.meds} token={token} onFechar={() => setAberto(null)} />
      )}
    </>
  );
}

function Detalhe({ at, pessoa, meds, token, onFechar }: {
  at: Atendimento; pessoa?: Pessoa; meds: Map<number, Medicamento>; token: string; onFechar: () => void;
}) {
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);
  const [email, setEmail] = useState('');
  const [nome, setNome] = useState('');
  const [relacao, setRelacao] = useState<'PACIENTE' | 'FAMILIAR'>('FAMILIAR');
  const [ocupado, setOcupado] = useState(false);

  async function gerarPdf() {
    setMsg(null);
    setOcupado(true);
    try {
      await baixar(`/documento/ficha/${at.id}`, token, 'ficha_atendimento.pdf');
      setMsg({ tipo: 'ok', texto: 'Ficha gerada e baixada.' });
    } catch (e) {
      setMsg({ tipo: 'erro', texto: e instanceof Error ? e.message : 'Falha ao gerar a ficha' });
    } finally {
      setOcupado(false);
    }
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setOcupado(true);
    try {
      const r = await post<{ envioId: number; status: string }>(`/documento/ficha/${at.id}/email`,
        { destinatario: email.trim(), nomeDestinatario: nome.trim() || null, relacao }, token);
      setMsg({ tipo: 'ok', texto: `E-mail enviado para ${email} (envio #${r.envioId}).` });
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err instanceof Error ? err.message : 'Falha no envio' });
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="modal-fundo" onClick={onFechar}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-topo">
          <div>
            <h2>{pessoa?.nome ?? 'Atendimento'}</h2>
            <small>{dataHora(at.inicio)} · {texto(at.local)} · {at.criadoOffline ? 'criado offline' : 'online'} · v{at.version}</small>
          </div>
          <button className="link" onClick={onFechar}>Fechar ✕</button>
        </div>
        <div className="grade">
          <div><span>Queixa</span>{texto(at.queixaPrincipal)}</div>
          <div><span>Glasgow</span>{texto(at.glasgow?.total)} (O{texto(at.glasgow?.ocular)} V{texto(at.glasgow?.verbal)} M{texto(at.glasgow?.motora)})</div>
          <div><span>Triagem</span><Triagem v={at.triagemManchester} /> · START <Triagem v={at.triagemStart} /></div>
          <div><span>Conduta</span>{texto(at.conduta)}</div>
          <div><span>Alergias</span>{texto(pessoa?.alergias)}</div>
          <div><span>Dispositivo</span>{texto(at.deviceId)}</div>
        </div>
        <h3>Sinais vitais</h3>
        <Tabela linhas={at.sinaisVitais} chave={(s) => s.id} colunas={[
          { titulo: 'Hora', valor: (s) => dataHora(s.aferidoEm) },
          { titulo: 'PA', valor: (s) => (s.paSistolica ? `${s.paSistolica}/${s.paDiastolica}` : '—') },
          { titulo: 'FC', valor: (s) => texto(s.fc) }, { titulo: 'FR', valor: (s) => texto(s.fr) },
          { titulo: 'SpO₂', valor: (s) => texto(s.spo2) }, { titulo: 'Temp.', valor: (s) => texto(s.temperatura) },
          { titulo: 'Glicemia', valor: (s) => texto(s.glicemia) },
        ]} />
        <h3>Medicações</h3>
        <Tabela linhas={at.medicacoes} chave={(m) => m.id} colunas={[
          { titulo: 'Hora', valor: (m) => dataHora(m.administradoEm) },
          { titulo: 'Medicamento', valor: (m) => meds.get(m.medicamentoId)?.nome ?? `#${m.medicamentoId}` },
          { titulo: 'Dose', valor: (m) => `${m.dose} ${m.unidade}` }, { titulo: 'Via', valor: (m) => texto(m.via) },
          { titulo: 'Alerta confirmado', valor: (m) => (m.alertaConfirmado ? 'sim' : '—') },
        ]} />
        <div className="acoes">
          <button className="primario" onClick={gerarPdf} disabled={ocupado}>Gerar ficha (PDF)</button>
          <form onSubmit={enviar} className="form-email">
            <input type="email" placeholder="e-mail do destinatário" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <input placeholder="nome (opcional)" value={nome} onChange={(e) => setNome(e.target.value)} />
            <select value={relacao} onChange={(e) => setRelacao(e.target.value as 'PACIENTE' | 'FAMILIAR')}>
              <option value="FAMILIAR">Familiar</option>
              <option value="PACIENTE">Paciente</option>
            </select>
            <button className="alerta" disabled={ocupado}>Enviar por e-mail</button>
          </form>
        </div>
        {msg && <div className={msg.tipo === 'ok' ? 'ok' : 'erro'}>{msg.texto}</div>}
      </div>
    </div>
  );
}

function Auditoria({ token }: { token: string }) {
  const [tipo, setTipo] = useState<'acesso' | 'sync'>('acesso');
  return (
    <>
      <div className="chips">
        <button className={tipo === 'acesso' ? 'chip ativo' : 'chip'} onClick={() => setTipo('acesso')}>Logs de acesso</button>
        <button className={tipo === 'sync' ? 'chip ativo' : 'chip'} onClick={() => setTipo('sync')}>Eventos de sincronização</button>
      </div>
      {tipo === 'acesso' ? <Acessos key="a" token={token} /> : <EventosSync key="s" token={token} />}
    </>
  );
}

function Acessos({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<Registro[]>('/log?tipo=acesso&limite=300', token));
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => String(r.id)} colunas={[
    { titulo: 'data_hora', valor: (r) => dataHora(r.data_hora as string), mono: true },
    { titulo: 'serviço', valor: (r) => texto(r.servico) }, { titulo: 'ip_cliente', valor: (r) => texto(r.ip_cliente), mono: true },
    { titulo: 'profissional_id', valor: (r) => texto(r.profissional_id), mono: true },
    { titulo: 'método', valor: (r) => texto(r.metodo), mono: true }, { titulo: 'rota', valor: (r) => texto(r.rota), mono: true },
    { titulo: 'status', valor: (r) => <span className={Number(r.status_code) >= 400 ? 'txt-erro' : ''}>{texto(r.status_code)}</span>, mono: true },
    { titulo: 'tempo_ms', valor: (r) => texto(r.tempo_ms), mono: true }, { titulo: 'origem', valor: (r) => texto(r.origem) },
  ]} /></>);
}

function EventosSync({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<Registro[]>('/log?tipo=sync&limite=300', token));
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => String(r.id)} colunas={[
    { titulo: 'data_hora', valor: (r) => dataHora(r.data_hora as string), mono: true },
    { titulo: 'dispositivo', valor: (r) => texto(r.device_id) }, { titulo: 'entidade', valor: (r) => texto(r.entidade) },
    { titulo: 'operação', valor: (r) => texto(r.operacao) }, { titulo: 'status', valor: (r) => texto(r.status) },
    { titulo: 'estratégia', valor: (r) => texto(r.estrategia) }, { titulo: 'vencedor', valor: (r) => texto(r.vencedor) },
    { titulo: 'versões (cli/srv)', valor: (r) => `${texto(r.versao_cliente)} / ${texto(r.versao_servidor)}` },
  ]} /></>);
}

function Envios({ token }: { token: string }) {
  const { dados, erro } = useDados(() => get<Registro[]>('/documento/envio', token));
  return (<><Erro msg={erro} /><Tabela linhas={dados} chave={(r) => String(r.id)} colunas={[
    { titulo: 'Enviado em', valor: (r) => dataHora(r.enviadoEm as string) }, { titulo: 'Destinatário', valor: (r) => texto(r.destinatario) },
    { titulo: 'Nome', valor: (r) => texto(r.nomeDestinatario) }, { titulo: 'Relação', valor: (r) => texto(r.relacao) },
    { titulo: 'Status', valor: (r) => texto(r.status) }, { titulo: 'Atendimento', valor: (r) => String(r.atendimentoId).slice(0, 8), mono: true },
  ]} /></>);
}
