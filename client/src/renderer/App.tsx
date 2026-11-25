import { FormEvent, ReactNode, useCallback, useEffect, useState } from 'react';
import type { Estado, ItemOutbox, LogLocal, Medicamento, Pessoa, Prontuario, SinalVital } from '../shared/tipos';
import { mensagem, mf, ResumoAtendimento } from './bridge';

const dataHora = (v?: string | null) =>
  v ? new Date(v).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';
const txt = (v: unknown) => (v === null || v === undefined || v === '' ? '—' : String(v));
const CORES: Record<string, string> = {
  VERMELHO: '#ef4444', LARANJA: '#f97316', AMARELO: '#facc15', VERDE: '#22c55e', AZUL: '#3b82f6', PRETO: '#1f2937',
};

export default function App() {
  const [estado, setEstado] = useState<Estado | null>(null);
  useEffect(() => {
    void mf.estado().then(setEstado);
    return mf.aoMudarEstado(setEstado);
  }, []);
  if (!estado) return null;
  if (!estado.profissional) return <Login estado={estado} />;
  return <Principal estado={estado} />;
}

function Logo({ tamanho = 22 }: { tamanho?: number }) {
  return (
    <span className="logo" style={{ fontSize: tamanho }}>
      <span className="logo-marca">✚</span>
      <span>Medical<b>Field</b></span>
    </span>
  );
}

function StatusRede({ estado }: { estado: Estado }) {
  return (
    <span className={`status ${estado.online ? 'on' : 'off'}`}>
      <i />{estado.online ? 'ONLINE' : 'OFFLINE'}
    </span>
  );
}

function Chave({ estado }: { estado: Estado }) {
  return (
    <label className="chave" title="Simula a perda e o retorno da conexão">
      <span>Simular Conectividade</span>
      <button type="button" className={estado.simulacaoOnline ? 'switch ligado' : 'switch'}
        onClick={() => void mf.definirSimulacao(!estado.simulacaoOnline)} aria-pressed={estado.simulacaoOnline}>
        <i />
      </button>
      <small>{estado.simulacaoOnline ? 'Online' : 'Offline'}</small>
    </label>
  );
}

function Login({ estado }: { estado: Estado }) {
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
      await mf.login(registro, tipo, senha);
    } catch (err) {
      setErro(mensagem(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login">
      <div className="login-topo"><StatusRede estado={estado} /><Chave estado={estado} /></div>
      <form className="cartao login-card" onSubmit={entrar}>
        <Logo tamanho={30} />
        <p className="sub">Cliente de atendimento · dispositivo {estado.deviceId}</p>
        <div className="chips">
          {(['CRM', 'COREN', 'SOCORRISTA'] as const).map((t) => (
            <button type="button" key={t} className={tipo === t ? 'chip ativo' : 'chip'} onClick={() => setTipo(t)}>
              {t === 'SOCORRISTA' ? 'ID Socorrista' : t}
            </button>
          ))}
        </div>
        <label>Registro<input value={registro} onChange={(e) => setRegistro(e.target.value)} placeholder="CRM-RS 12345" required autoFocus /></label>
        <label>Senha<input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required /></label>
        {!estado.online && <div className="aviso">Sem conexão: o login será conferido com o hash guardado neste dispositivo.</div>}
        {erro && <div className="erro">{erro}</div>}
        <button className="primario" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</button>
      </form>
    </div>
  );
}

const TELAS = ['Novo atendimento', 'Pacientes', 'Atendimentos', 'Pendências'] as const;
type Tela = (typeof TELAS)[number];

function Principal({ estado }: { estado: Estado }) {
  const [tela, setTela] = useState<Tela>('Novo atendimento');
  const [erroSync, setErroSync] = useState('');
  async function sincronizar() {
    setErroSync('');
    try {
      await mf.sincronizar();
    } catch (e) {
      setErroSync(mensagem(e));
    }
  }
  return (
    <div className="app">
      <header className="barra">
        <Logo />
        <StatusRede estado={estado} />
        <Chave estado={estado} />
        <button className={`pendencias ${estado.pendencias ? 'ha' : ''}`} onClick={() => setTela('Pendências')}>
          <b>{estado.pendencias}</b> pendência{estado.pendencias === 1 ? '' : 's'}
          {estado.erros > 0 && <em> · {estado.erros} com erro</em>}
        </button>
        <button className="secundario" onClick={sincronizar} disabled={!estado.online || estado.sincronizando}>
          {estado.sincronizando ? 'Sincronizando…' : '⟳ Sincronizar'}
        </button>
        <span className="msg">{erroSync || estado.mensagem || (estado.ultimaSync ? `Última sincronização ${dataHora(estado.ultimaSync)}` : 'Ainda não sincronizado')}</span>
        <span className="usuario">
          {estado.profissional!.nome} <small>{estado.profissional!.registro}</small>
          <button className="link" onClick={() => void mf.logout()}>Sair</button>
        </span>
      </header>
      {estado.online && !estado.tokenValido && (
        <div className="aviso faixa">Sessão sem token válido: saia e entre novamente com conexão para sincronizar.</div>
      )}
      <div className="corpo">
        <nav>
          {TELAS.map((t) => <button key={t} className={t === tela ? 'ativo' : ''} onClick={() => setTela(t)}>{t}</button>)}
          <div className="rodape-nav">
            <small>API {estado.apiUrl}</small>
            <small>Último pull {dataHora(estado.ultimoPull)}</small>
          </div>
        </nav>
        <main>
          {tela === 'Novo atendimento' && <NovoAtendimento atualizacao={`${estado.ultimoPull}|${estado.pendencias}`} />}
          {tela === 'Pacientes' && <Pacientes estado={estado} />}
          {tela === 'Atendimentos' && <Atendimentos estado={estado} />}
          {tela === 'Pendências' && <Pendencias estado={estado} />}
        </main>
      </div>
    </div>
  );
}

// ======================================================================= novo atendimento
const ETAPAS = ['Pessoa', 'Prontuário', 'Atendimento', 'Sinais vitais', 'Glasgow', 'Triagem', 'Medicação'];
type MedRascunho = { id: string; medicamentoId: number; dose: number; unidade: string; via: string; administradoEm: string; alertaConfirmado: boolean };
type SinalRascunho = Omit<SinalVital, 'id'> & { id: string };

const agoraLocal = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
};
const uid = () => crypto.randomUUID();
const num = (s: string) => (s.trim() === '' ? null : Number(s.replace(',', '.')));

function NovoAtendimento({ atualizacao }: { atualizacao: string }) {
  const [etapa, setEtapa] = useState(0);
  const [pessoa, setPessoa] = useState<Pessoa | null>(null);
  const [prontuario, setProntuario] = useState<Prontuario | null>(null);
  const [dados, setDados] = useState({ inicio: agoraLocal(), local: '', queixaPrincipal: '', destino: '', conduta: '' });
  const [sinais, setSinais] = useState<SinalRascunho[]>([]);
  const [glasgow, setGlasgow] = useState<{ ocular?: number; verbal?: number; motora?: number }>({});
  const [triagem, setTriagem] = useState<{ manchester?: string; start?: string }>({});
  const [meds, setMeds] = useState<MedRascunho[]>([]);
  const [alertas, setAlertas] = useState<{ medicacaoId: string; mensagem: string }[]>([]);
  const [erro, setErro] = useState('');
  const [salvo, setSalvo] = useState<string | null>(null);

  function reiniciar() {
    setEtapa(0); setPessoa(null); setProntuario(null); setSinais([]); setGlasgow({}); setTriagem({}); setMeds([]);
    setDados({ inicio: agoraLocal(), local: '', queixaPrincipal: '', destino: '', conduta: '' }); setSalvo(null); setErro('');
  }

  async function salvar(confirmados: string[] = []) {
    setErro('');
    try {
      const r = await mf.salvarAtendimento({
        prontuarioId: prontuario!.id, inicio: new Date(dados.inicio).toISOString(), local: dados.local,
        queixaPrincipal: dados.queixaPrincipal, destino: dados.destino, conduta: dados.conduta,
        glasgow, triagemManchester: triagem.manchester ?? null, triagemStart: triagem.start ?? null,
        sinaisVitais: sinais, medicacoes: meds.map((m) => ({ ...m, alertaConfirmado: m.alertaConfirmado || confirmados.includes(m.id) })),
      });
      if (r.salvo) {
        setAlertas([]);
        setSalvo(r.atendimento.id);
      } else setAlertas(r.alertas);
    } catch (e) {
      setErro(mensagem(e));
    }
  }

  if (salvo) {
    return (
      <div className="cartao concluido">
        <div className="check">✓</div>
        <h2>Atendimento registrado</h2>
        <p>{pessoa?.nome} · {dados.local || 'local não informado'}</p>
        <p className="sub">Gravado no SQLite do dispositivo. Se houver conexão, a Outbox é enviada automaticamente.</p>
        <button className="primario" onClick={reiniciar}>Novo atendimento</button>
      </div>
    );
  }

  const pode = [true, !!pessoa, !!prontuario, !!prontuario, !!prontuario, !!prontuario, !!prontuario];
  return (
    <div className="wizard">
      <ol className="etapas">
        {ETAPAS.map((e, i) => (
          <li key={e} className={i === etapa ? 'atual' : i < etapa ? 'feita' : ''}>
            <button disabled={!pode[i]} onClick={() => setEtapa(i)}><span>{i < etapa ? '✓' : i + 1}</span>{e}</button>
          </li>
        ))}
      </ol>
      <section className="cartao etapa">
        {etapa === 0 && <EtapaPessoa atualizacao={atualizacao} pessoa={pessoa} onEscolher={(p) => { setPessoa(p); setProntuario(null); setEtapa(1); }} />}
        {etapa === 1 && pessoa && <EtapaProntuario pessoa={pessoa} onPronto={(p) => { setProntuario(p); setEtapa(2); }} />}
        {etapa === 2 && (
          <>
            <h2>Atendimento</h2>
            <div className="campos">
              <label>Início<input type="datetime-local" value={dados.inicio} onChange={(e) => setDados({ ...dados, inicio: e.target.value })} /></label>
              <label>Local<input value={dados.local} onChange={(e) => setDados({ ...dados, local: e.target.value })} placeholder="BR-386, km 340" /></label>
              <label className="largo">Queixa principal<input value={dados.queixaPrincipal} onChange={(e) => setDados({ ...dados, queixaPrincipal: e.target.value })} /></label>
              <label>Destino<input value={dados.destino} onChange={(e) => setDados({ ...dados, destino: e.target.value })} placeholder="Hospital de referência" /></label>
            </div>
          </>
        )}
        {etapa === 3 && <EtapaSinais sinais={sinais} setSinais={setSinais} />}
        {etapa === 4 && <EtapaGlasgow g={glasgow} setG={setGlasgow} />}
        {etapa === 5 && <EtapaTriagem t={triagem} setT={setTriagem} />}
        {etapa === 6 && pessoa && (
          <EtapaMedicacao pessoa={pessoa} meds={meds} setMeds={setMeds} conduta={dados.conduta} setConduta={(c) => setDados({ ...dados, conduta: c })} />
        )}
        {erro && <div className="erro">{erro}</div>}
        {alertas.length > 0 && (
          <div className="alerta-clinico">
            <h3>Alerta de segurança clínica</h3>
            {alertas.map((a) => <p key={a.medicacaoId}>{a.mensagem}</p>)}
            <div className="linha">
              <button className="perigo" onClick={() => void salvar(alertas.map((a) => a.medicacaoId))}>Confirmar e salvar</button>
              <button className="secundario" onClick={() => setAlertas([])}>Revisar medicação</button>
            </div>
          </div>
        )}
        <div className="navegacao">
          <button className="secundario" disabled={etapa === 0} onClick={() => setEtapa(etapa - 1)}>← Voltar</button>
          {etapa >= 2 && etapa < 6 && <button className="primario" onClick={() => setEtapa(etapa + 1)}>Avançar →</button>}
          {etapa === 6 && <button className="primario" onClick={() => void salvar()}>Salvar atendimento</button>}
        </div>
      </section>
    </div>
  );
}

const PESSOA_VAZIA = { nome: '', cpf: '', dataNascimento: '', sexo: '', tipoSanguineo: '', alergias: '', telefone: '', contatoEmergencia: '' };

function EtapaPessoa({ pessoa, onEscolher, atualizacao }: { pessoa: Pessoa | null; onEscolher: (p: Pessoa) => void; atualizacao: string }) {
  const [busca, setBusca] = useState('');
  const [lista, setLista] = useState<Pessoa[]>([]);
  const [nova, setNova] = useState<typeof PESSOA_VAZIA | null>(null);
  const [erro, setErro] = useState('');
  // Recarrega também quando um pull ou envio muda os dados locais.
  useEffect(() => { void mf.listarPessoas(busca).then(setLista); }, [busca, atualizacao]);

  async function criar(e: FormEvent) {
    e.preventDefault();
    try {
      onEscolher(await mf.salvarPessoa(nova!));
    } catch (err) {
      setErro(mensagem(err));
    }
  }

  if (nova) {
    const campo = (k: keyof typeof PESSOA_VAZIA, rotulo: string, tipo = 'text', ph = '') => (
      <label>{rotulo}<input type={tipo} value={nova[k]} placeholder={ph} onChange={(e) => setNova({ ...nova, [k]: e.target.value })} required={k === 'nome'} /></label>
    );
    return (
      <form onSubmit={criar}>
        <h2>Nova pessoa</h2>
        <div className="campos">
          {campo('nome', 'Nome')}{campo('cpf', 'CPF', 'text', 'opcional para vítima não identificada')}
          {campo('dataNascimento', 'Nascimento', 'date')}
          <label>Sexo<select value={nova.sexo} onChange={(e) => setNova({ ...nova, sexo: e.target.value })}>
            <option value="">—</option><option>Feminino</option><option>Masculino</option><option>Outro</option></select></label>
          <label>Tipo sanguíneo<select value={nova.tipoSanguineo} onChange={(e) => setNova({ ...nova, tipoSanguineo: e.target.value })}>
            <option value="">—</option>{['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((t) => <option key={t}>{t}</option>)}</select></label>
          {campo('alergias', 'Alergias', 'text', 'separe por vírgula')}{campo('telefone', 'Telefone')}{campo('contatoEmergencia', 'Contato de emergência')}
        </div>
        {erro && <div className="erro">{erro}</div>}
        <div className="linha"><button className="primario">Salvar pessoa</button><button type="button" className="secundario" onClick={() => setNova(null)}>Cancelar</button></div>
      </form>
    );
  }
  return (
    <>
      <h2>Identificar paciente</h2>
      <div className="linha">
        <input className="busca" placeholder="Buscar por nome ou CPF" value={busca} onChange={(e) => setBusca(e.target.value)} autoFocus />
        <button className="primario" onClick={() => setNova({ ...PESSOA_VAZIA, nome: busca })}>+ Nova pessoa</button>
      </div>
      <ul className="lista">
        {lista.map((p) => (
          <li key={p.id} className={pessoa?.id === p.id ? 'sel' : ''} onClick={() => onEscolher(p)}>
            <b>{p.nome}</b><span>{txt(p.cpf)} · {txt(p.tipoSanguineo)} · alergias: {txt(p.alergias)}</span><Sync s={p.syncStatus} />
          </li>
        ))}
        {!lista.length && <li className="vazio">Nenhuma pessoa encontrada.</li>}
      </ul>
    </>
  );
}

function EtapaProntuario({ pessoa, onPronto }: { pessoa: Pessoa; onPronto: (p: Prontuario) => void }) {
  const [p, setP] = useState<{ id?: string; comorbidades: string; usoContinuo: string; observacoes: string } | null>(null);
  const [existe, setExiste] = useState(false);
  const [erro, setErro] = useState('');
  useEffect(() => {
    void mf.prontuarioDaPessoa(pessoa.id).then((r) => {
      setExiste(!!r);
      setP({ id: r?.id, comorbidades: r?.comorbidades ?? '', usoContinuo: r?.usoContinuo ?? '', observacoes: r?.observacoes ?? '' });
    });
  }, [pessoa.id]);
  if (!p) return null;
  async function salvar(e: FormEvent) {
    e.preventDefault();
    try {
      onPronto(await mf.salvarProntuario({ ...p!, pessoaId: pessoa.id }));
    } catch (err) {
      setErro(mensagem(err));
    }
  }
  return (
    <form onSubmit={salvar}>
      <h2>Prontuário · {pessoa.nome}</h2>
      <p className="sub">{existe ? 'Prontuário existente: confira e siga.' : 'Nenhum prontuário encontrado: será criado um novo.'} Alergias: {txt(pessoa.alergias)}</p>
      <div className="campos">
        <label className="largo">Comorbidades<input value={p.comorbidades} onChange={(e) => setP({ ...p, comorbidades: e.target.value })} /></label>
        <label className="largo">Uso contínuo<input value={p.usoContinuo} onChange={(e) => setP({ ...p, usoContinuo: e.target.value })} /></label>
        <label className="largo">Observações<input value={p.observacoes} onChange={(e) => setP({ ...p, observacoes: e.target.value })} /></label>
      </div>
      {erro && <div className="erro">{erro}</div>}
      <button className="primario">{existe ? 'Salvar e continuar' : 'Criar prontuário'}</button>
    </form>
  );
}

const SINAL_VAZIO = { paSistolica: '', paDiastolica: '', fc: '', fr: '', spo2: '', temperatura: '', glicemia: '' };

function EtapaSinais({ sinais, setSinais }: { sinais: SinalRascunho[]; setSinais: (s: SinalRascunho[]) => void }) {
  const [f, setF] = useState(SINAL_VAZIO);
  const rot: [keyof typeof SINAL_VAZIO, string][] = [
    ['paSistolica', 'PA sistólica (mmHg)'], ['paDiastolica', 'PA diastólica (mmHg)'], ['fc', 'FC (bpm)'], ['fr', 'FR (irpm)'],
    ['spo2', 'SpO₂ (%)'], ['temperatura', 'Temperatura (°C)'], ['glicemia', 'Glicemia (mg/dL)'],
  ];
  function adicionar() {
    const s: SinalRascunho = { id: uid(), aferidoEm: new Date().toISOString() };
    for (const [k] of rot) (s as Record<string, unknown>)[k] = num(f[k]);
    setSinais([...sinais, s]);
    setF(SINAL_VAZIO);
  }
  return (
    <>
      <h2>Sinais vitais</h2>
      <div className="campos sete">
        {rot.map(([k, r]) => <label key={k}>{r}<input inputMode="decimal" value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></label>)}
      </div>
      <button className="secundario" onClick={adicionar}>+ Registrar aferição</button>
      <Tabela linhas={sinais} chave={(s) => s.id} colunas={[
        { t: 'Hora', v: (s) => dataHora(s.aferidoEm) }, { t: 'PA', v: (s) => (s.paSistolica ? `${s.paSistolica}/${s.paDiastolica ?? '—'}` : '—') },
        { t: 'FC', v: (s) => txt(s.fc) }, { t: 'FR', v: (s) => txt(s.fr) }, { t: 'SpO₂', v: (s) => txt(s.spo2) },
        { t: 'Temp.', v: (s) => txt(s.temperatura) }, { t: 'Glicemia', v: (s) => txt(s.glicemia) },
      ]} />
    </>
  );
}

function EtapaGlasgow({ g, setG }: { g: { ocular?: number; verbal?: number; motora?: number }; setG: (g: { ocular?: number; verbal?: number; motora?: number }) => void }) {
  const itens: ['ocular' | 'verbal' | 'motora', string, number][] = [['ocular', 'Abertura ocular', 4], ['verbal', 'Resposta verbal', 5], ['motora', 'Resposta motora', 6]];
  const total = g.ocular && g.verbal && g.motora ? g.ocular + g.verbal + g.motora : null;
  return (
    <div className="glasgow">
      <div>
        <h2>Escala de Glasgow</h2>
        {itens.map(([k, r, max]) => (
          <div key={k} className="gcs-linha">
            <span>{r}</span>
            <div>{Array.from({ length: max }, (_, i) => i + 1).map((n) => (
              <button key={n} className={g[k] === n ? 'gcs sel' : 'gcs'} onClick={() => setG({ ...g, [k]: n })}>{n}</button>
            ))}</div>
          </div>
        ))}
      </div>
      <div className="gcs-total"><span>Total</span><b>{total ?? '—'}</b><small>3 a 15</small></div>
    </div>
  );
}

function EtapaTriagem({ t, setT }: { t: { manchester?: string; start?: string }; setT: (t: { manchester?: string; start?: string }) => void }) {
  const grupo = (titulo: string, ops: string[], atual: string | undefined, set: (v: string) => void) => (
    <div className="triagem-grupo">
      <h3>{titulo}</h3>
      <div>{ops.map((o) => (
        <button key={o} className={atual === o ? 'tri sel' : 'tri'} style={{ background: CORES[o] }} onClick={() => set(o)}>
          {o.charAt(0) + o.slice(1).toLowerCase()}
        </button>
      ))}</div>
    </div>
  );
  return (
    <>
      <h2>Triagem</h2>
      {grupo('Protocolo de Manchester', ['VERMELHO', 'LARANJA', 'AMARELO', 'VERDE', 'AZUL'], t.manchester, (v) => setT({ ...t, manchester: v }))}
      {grupo('START', ['VERMELHO', 'AMARELO', 'VERDE', 'PRETO'], t.start, (v) => setT({ ...t, start: v }))}
    </>
  );
}

function EtapaMedicacao({ pessoa, meds, setMeds, conduta, setConduta }: {
  pessoa: Pessoa; meds: MedRascunho[]; setMeds: (m: MedRascunho[]) => void; conduta: string; setConduta: (c: string) => void;
}) {
  const [lista, setLista] = useState<Medicamento[]>([]);
  const [sel, setSel] = useState('');
  const [dose, setDose] = useState('');
  const [via, setVia] = useState('');
  useEffect(() => { void mf.listarMedicamentos().then(setLista); }, []);
  const med = lista.find((m) => String(m.id) === sel);
  const doseN = num(dose);
  const acima = !!med && doseN != null && doseN > med.doseMaxima;
  function adicionar() {
    if (!med || doseN == null) return;
    setMeds([...meds, { id: uid(), medicamentoId: med.id, dose: doseN, unidade: med.unidade, via: via || med.viaPadrao || '', administradoEm: new Date().toISOString(), alertaConfirmado: false }]);
    setSel(''); setDose(''); setVia('');
  }
  return (
    <>
      <h2>Conduta e medicação</h2>
      <label className="bloco">Conduta<textarea value={conduta} onChange={(e) => setConduta(e.target.value)} rows={2} /></label>
      <div className="campos">
        <label>Medicamento<select value={sel} onChange={(e) => setSel(e.target.value)}>
          <option value="">Selecione…</option>{lista.map((m) => <option key={m.id} value={m.id}>{m.nome}</option>)}</select></label>
        <label>Dose{med && ` (${med.unidade}, máx. ${med.doseMaxima})`}<input inputMode="decimal" value={dose} onChange={(e) => setDose(e.target.value)} /></label>
        <label>Via<input value={via} placeholder={med?.viaPadrao ?? 'EV'} onChange={(e) => setVia(e.target.value)} /></label>
      </div>
      {med?.alertas && <div className="aviso">{med.alertas}</div>}
      {pessoa.alergias && med && <div className="sub">Alergias do paciente: {pessoa.alergias}</div>}
      {acima && <div className="erro">Dose acima do máximo cadastrado ({med!.doseMaxima} {med!.unidade}).</div>}
      <button className="secundario" disabled={!med || doseN == null || acima} onClick={adicionar}>+ Adicionar medicação</button>
      <Tabela linhas={meds} chave={(m) => m.id} colunas={[
        { t: 'Hora', v: (m) => dataHora(m.administradoEm) }, { t: 'Medicamento', v: (m) => lista.find((x) => x.id === m.medicamentoId)?.nome ?? m.medicamentoId },
        { t: 'Dose', v: (m) => `${m.dose} ${m.unidade}` }, { t: 'Via', v: (m) => txt(m.via) },
        { t: '', v: (m) => <button className="link" onClick={() => setMeds(meds.filter((x) => x.id !== m.id))}>remover</button> },
      ]} />
    </>
  );
}

// ======================================================================= listas
type Col<T> = { t: string; v: (r: T) => ReactNode };
function Tabela<T>({ linhas, colunas, chave, onClique }: { linhas: T[]; colunas: Col<T>[]; chave: (r: T) => string | number; onClique?: (r: T) => void }) {
  if (!linhas.length) return null;
  return (
    <div className="tabela-wrap">
      <table>
        <thead><tr>{colunas.map((c) => <th key={c.t}>{c.t}</th>)}</tr></thead>
        <tbody>{linhas.map((r) => (
          <tr key={chave(r)} className={onClique ? 'clicavel' : ''} onClick={onClique && (() => onClique(r))}>
            {colunas.map((c) => <td key={c.t}>{c.v(r)}</td>)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function Sync({ s }: { s?: string }) {
  if (!s) return null;
  const cls = s === 'SINCRONIZADO' ? 'ok' : s === 'ERRO' ? 'err' : 'pend';
  return <span className={`badge ${cls}`}>{s}</span>;
}

function Triagem({ v }: { v?: string | null }) {
  return v ? <span className="tri-txt"><i style={{ background: CORES[v] }} />{v.charAt(0) + v.slice(1).toLowerCase()}</span> : <>—</>;
}

function Pacientes({ estado }: { estado: Estado }) {
  const [busca, setBusca] = useState('');
  const [lista, setLista] = useState<Pessoa[]>([]);
  const [sel, setSel] = useState<Pessoa | null>(null);
  const [pront, setPront] = useState<Prontuario | null>(null);
  const [ats, setAts] = useState<ResumoAtendimento[]>([]);
  useEffect(() => { void mf.listarPessoas(busca).then(setLista); }, [busca, estado.pendencias, estado.ultimoPull]);
  useEffect(() => {
    if (!sel) return;
    void mf.prontuarioDaPessoa(sel.id).then(setPront);
    void mf.listarAtendimentos(sel.id).then(setAts);
  }, [sel, estado.ultimoPull]);
  return (
    <div className="duas">
      <section className="cartao">
        <h2>Pacientes no dispositivo</h2>
        <input className="busca" placeholder="Buscar" value={busca} onChange={(e) => setBusca(e.target.value)} />
        <ul className="lista">{lista.map((p) => (
          <li key={p.id} className={sel?.id === p.id ? 'sel' : ''} onClick={() => setSel(p)}><b>{p.nome}</b><span>{txt(p.cpf)}</span><Sync s={p.syncStatus} /></li>
        ))}</ul>
      </section>
      <section className="cartao">
        {!sel ? <p className="sub">Selecione um paciente.</p> : (
          <>
            <h2>{sel.nome}</h2>
            <div className="grade">
              <div><span>Nascimento</span>{txt(sel.dataNascimento)}</div><div><span>Tipo sanguíneo</span>{txt(sel.tipoSanguineo)}</div>
              <div><span>Alergias</span>{txt(sel.alergias)}</div><div><span>Comorbidades</span>{txt(pront?.comorbidades)}</div>
              <div><span>Uso contínuo</span>{txt(pront?.usoContinuo)}</div><div><span>Prontuário</span><Sync s={pront?.syncStatus ?? 'sem prontuário'} /></div>
            </div>
            <h3>Atendimentos</h3>
            <Tabela linhas={ats} chave={(a) => a.id} colunas={[
              { t: 'Início', v: (a) => dataHora(a.inicio) }, { t: 'Local', v: (a) => txt(a.local) },
              { t: 'Manchester', v: (a) => <Triagem v={a.triagemManchester} /> }, { t: 'Sync', v: (a) => <Sync s={a.syncStatus} /> },
            ]} />
          </>
        )}
      </section>
    </div>
  );
}

function Atendimentos({ estado }: { estado: Estado }) {
  const [lista, setLista] = useState<ResumoAtendimento[]>([]);
  const [sel, setSel] = useState<ResumoAtendimento | null>(null);
  const carregar = useCallback(() => void mf.listarAtendimentos().then(setLista), []);
  useEffect(carregar, [carregar, estado.pendencias, estado.ultimoPull]);
  return (
    <div className="duas larga">
      <section className="cartao">
        <h2>Atendimentos no dispositivo</h2>
        <Tabela linhas={lista} chave={(a) => a.id} onClique={setSel} colunas={[
          { t: 'Início', v: (a) => dataHora(a.inicio) }, { t: 'Pessoa', v: (a) => a.pessoaNome }, { t: 'Local', v: (a) => txt(a.local) },
          { t: 'GCS', v: (a) => txt(a.glasgow?.total) }, { t: 'Manchester', v: (a) => <Triagem v={a.triagemManchester} /> },
          { t: 'Origem', v: (a) => (a.criadoOffline ? 'offline' : 'online') }, { t: 'Sync', v: (a) => <Sync s={a.syncStatus} /> },
        ]} />
      </section>
      {sel && <DetalheAtendimento key={sel.id} a={sel} estado={estado} />}
    </div>
  );
}

function DetalheAtendimento({ a, estado }: { a: ResumoAtendimento; estado: Estado }) {
  const [msg, setMsg] = useState<{ ok: boolean; t: string } | null>(null);
  const [email, setEmail] = useState('');
  const [nome, setNome] = useState('');
  const [relacao, setRelacao] = useState('FAMILIAR');
  const sincronizado = a.syncStatus === 'SINCRONIZADO';
  async function pdf() {
    setMsg(null);
    try {
      const arq = await mf.salvarFicha(a.id);
      if (arq) setMsg({ ok: true, t: `Ficha salva em ${arq}` });
    } catch (e) {
      setMsg({ ok: false, t: mensagem(e) });
    }
  }
  async function enviar(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      const r = await mf.enviarFicha(a.id, email.trim(), nome.trim() || null, relacao);
      setMsg({ ok: true, t: `E-mail enviado (envio #${r.envioId}).` });
    } catch (err) {
      setMsg({ ok: false, t: mensagem(err) });
    }
  }
  return (
    <section className="cartao">
      <h2>{a.pessoaNome}</h2>
      <p className="sub">{dataHora(a.inicio)} · {txt(a.local)} · v{a.version} · <Sync s={a.syncStatus} /></p>
      <div className="grade">
        <div><span>Queixa</span>{txt(a.queixaPrincipal)}</div>
        <div><span>Glasgow</span>{txt(a.glasgow?.total)}</div>
        <div><span>Triagem</span><Triagem v={a.triagemManchester} /> · START <Triagem v={a.triagemStart} /></div>
        <div><span>Sinais / medicações</span>{a.sinaisVitais.length} / {a.medicacoes.length}</div>
      </div>
      <h3>Ficha de Atendimento</h3>
      {!estado.online && <div className="aviso">A ficha é gerada pelo servidor: disponível quando houver conexão.</div>}
      {estado.online && !sincronizado && <div className="aviso">Sincronize este atendimento antes de gerar a ficha.</div>}
      <div className="linha"><button className="primario" disabled={!estado.online || !sincronizado} onClick={pdf}>Gerar ficha (PDF)</button></div>
      <form className="linha" onSubmit={enviar}>
        <input type="email" placeholder="e-mail do destinatário" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="nome (opcional)" value={nome} onChange={(e) => setNome(e.target.value)} />
        <select value={relacao} onChange={(e) => setRelacao(e.target.value)}><option value="FAMILIAR">Familiar</option><option value="PACIENTE">Paciente</option></select>
        <button className="alerta" disabled={!estado.online || !sincronizado}>Enviar por e-mail</button>
      </form>
      {msg && <div className={msg.ok ? 'ok' : 'erro'}>{msg.t}</div>}
    </section>
  );
}

function Pendencias({ estado }: { estado: Estado }) {
  const [outbox, setOutbox] = useState<ItemOutbox[]>([]);
  const [logs, setLogs] = useState<LogLocal[]>([]);
  useEffect(() => {
    void mf.listarOutbox().then(setOutbox);
    void mf.listarLogs().then(setLogs);
  }, [estado.pendencias, estado.sincronizando]);
  return (
    <div className="duas larga">
      <section className="cartao">
        <h2>Outbox</h2>
        <p className="sub">{estado.pendencias} item(ns) aguardando envio ao servidor.</p>
        <Tabela linhas={outbox} chave={(o) => o.id} colunas={[
          { t: '#', v: (o) => o.id }, { t: 'Entidade', v: (o) => o.entidade }, { t: 'Operação', v: (o) => o.operacao },
          { t: 'Criado', v: (o) => dataHora(o.criadoEm) }, { t: 'Status', v: (o) => <Sync s={o.status === 'ENVIADO' ? 'SINCRONIZADO' : o.status} /> },
          { t: 'Tentativas', v: (o) => o.tentativas }, { t: 'Erro', v: (o) => txt(o.ultimoErro) },
        ]} />
      </section>
      <section className="cartao">
        <h2>local_log</h2>
        <Tabela linhas={logs} chave={(l) => l.id} colunas={[
          { t: 'Data/hora', v: (l) => dataHora(l.dataHora) }, { t: 'Ação', v: (l) => l.acao },
          { t: 'Entidade', v: (l) => txt(l.entidade) }, { t: 'Enviado', v: (l) => (l.enviado ? 'sim' : 'não') },
        ]} />
      </section>
    </div>
  );
}
