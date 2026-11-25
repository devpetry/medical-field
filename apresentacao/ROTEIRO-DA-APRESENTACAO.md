# Roteiro da apresentação (passo a passo)

Tudo o que você faz no dia, em ordem: do que levar até desligar. A apresentação é feita no **PC do professor (Linux)**, no laboratório. As explicações de cada peça ficam no [guia de demonstração](GUIA-DE-DEMONSTRACAO.md).

## 0. Referência rápida

| O quê | Valor |
| --- | --- |
| Portal | http://177.44.248.75 |
| Swagger | http://177.44.248.75/docs/ |
| API (cliente, Postman) | http://177.44.248.75/api |
| Executáveis | https://github.com/devpetry/medical-field/releases/tag/v1.0.0 |
| VM por SSH | `ssh univates@177.44.248.75` · senha: a que você definiu na troca de senha |
| Portal (administrador) | `CRM-RS 99999` |
| Cliente (socorrista) | `CRM-RS 12345` · Ana Souza |
| Outros socorristas | `COREN-RS 5521` · `SOC-0042` |
| Senha das contas de teste | `MedField@2026` |
| E-mails | Mailtrap → inbox **MedicalField** (com a sua conta do Mailtrap) |

---

## 1. Antes do dia

1. **Tudo vem do GitHub:** os executáveis estão na Release (link acima) e o restante (roteiro, diagramas, vídeo) em https://github.com/devpetry/medical-field. Não é preciso levar nada além de anotações.
2. **Anote** a senha da VM e o login do Mailtrap. No PC do professor não há a sua chave SSH, então a VM vai pedir a senha.
3. **Na véspera**, de casa, confira e zere a VM (passos 3 e 4 abaixo). Assim, no dia, só se confirma.
4. **Plano B:** o vídeo (`video/MedicalField_video_explicativo.mp4`) e os diagramas (`apresentacao/diagramas/`) abrem direto no GitHub, pelo navegador.

---

## 2. Chegando ao laboratório: abrir o terminal

No PC do professor, abra um terminal: **Ctrl+Alt+T** ou, no menu de aplicativos, procure **Terminal**.

---

## 3. Acessar a VM

No terminal:

```bash
ssh univates@177.44.248.75
```

1. **Primeira vez neste PC:** aparece `Are you sure you want to continue connecting (yes/no/[fingerprint])?`. Digite `yes` e Enter.
2. **Senha:** digite a senha da VM e Enter. Nada aparece enquanto você digita; é normal.
3. Entrou quando o prompt virar `univates@VMLS75:~$`.

Para sair da VM a qualquer momento: `exit`.

> Do seu próprio notebook, a chave `id_ed25519_pessoal` já está liberada: o `ssh` entra sem pedir senha.

---

## 4. Conferir que está tudo no ar

Ainda dentro da VM:

```bash
cd ~/medical-field && ./deploy/verificar.sh http://127.0.0.1
```

Tem que terminar em **Tudo certo**. São 18 checagens: portal, Swagger, 401 sem token, logins, rotas dos três serviços, 403 de perfil e o PDF.

Se alguma falhar, veja a seção 11. Para ver só se os serviços estão rodando:

```bash
systemctl is-active medicalfield-clinical medicalfield-auth medicalfield-document nginx postgresql
```

As cinco linhas devem dizer `active`.

---

## 5. Zerar para começar o roteiro do zero

Apaga pessoas, prontuários, atendimentos, medicamentos, e-mails e logs e recarrega os dados de demonstração. Os profissionais são mantidos.

```bash
sudo ./deploy/zerar.sh
```

Digite `ZERAR` e Enter. No fim aparece algo como `4 profissionais, 3 medicamentos, 3 pessoas, 2 atendimentos`. A Ondansetrona **não** pode estar lá: ela é inserida no passo 9.

**Deixe este terminal aberto, conectado à VM.** Ele será usado no passo 9.

---

## 6. Abrir o cliente desktop

1. Abra uma **segunda aba** do terminal (**Ctrl+Shift+T**).
2. No navegador, abra https://github.com/devpetry/medical-field/releases/tag/v1.0.0 e baixe `MedicalField-1.0.0.AppImage` (110 MB) e `abrir-medicalfield.sh`. Eles vão para `~/Downloads`. Faça isso logo ao chegar: o download pode demorar se a rede do laboratório estiver lenta.
3. Vá até a pasta e abra:

```bash
cd ~/Downloads
```

```bash
chmod +x abrir-medicalfield.sh && ./abrir-medicalfield.sh
```

A primeira abertura leva alguns segundos (o app se descompacta antes). O script funciona mesmo sem a biblioteca FUSE e com o sandbox do Chromium bloqueado, comuns em Ubuntu 22.04+ e 24.04+. O cliente já aponta para a VM: no canto superior direito deve aparecer **ONLINE**.

Se o PC do professor já tiver sido usado num ensaio, apague o banco local do cliente antes de abrir, para o passo 6 baixar tudo do zero:

```bash
rm -f ~/.config/medicalfield-client/medicalfield.db*
```

---

## 7. Abrir as abas do navegador

No navegador do PC, abra estas abas:

1. **Portal:** http://177.44.248.75 (ainda não entre)
2. **Swagger:** http://177.44.248.75/docs/
3. **Mailtrap:** https://mailtrap.io → entre com a sua conta → **Email Testing** → **Inboxes** → **MedicalField**
4. Esta página do roteiro, para consulta
5. Os links do código da seção 9 (padrões de projeto)

Organize a tela: navegador de um lado, cliente do outro, e o terminal da VM à mão.

---

## 8. Os 17 passos

Os passos 12 a 15 são o coração da demonstração: vá devagar e narre.

### Portal

**Passo 1 · Autenticar no portal**
- Fazer: na aba do portal, escolha **CRM**, registro `CRM-RS 99999`, senha `MedField@2026` → **Entrar**.
- Falar: "O login gera um JWT que os três serviços validam sozinhos, sem consultar o auth. O portal só aceita administradores."

**Passo 2 · Listar cadastros**
- Fazer: menu **Profissionais**, depois **Medicamentos**, depois **Pessoas**.
- Falar: "Profissionais vêm do auth-service, em Node; medicamentos e pessoas, do clinical-service, em Java."

**Passo 3 · Listar prontuários**
- Fazer: menu **Prontuários**.

**Passo 4 · Listar atendimentos**
- Fazer: menu **Atendimentos**.
- Falar: "A coluna Origem mostra se o atendimento foi criado online ou offline."

### Cliente

**Passo 5 · Autenticar no cliente**
- Fazer: confira a chave **Simular Conectividade** em **Online** (canto superior direito). Escolha **CRM**, registro `CRM-RS 12345`, senha `MedField@2026` → **Entrar**.
- Falar: "Este PC faz o papel da ambulância. O cliente tem banco SQLite próprio e guarda um hash da senha para permitir login sem internet."

**Passo 6 · Sincronizar (receber dados)**
- Fazer: clique em **⟳ Sincronizar** na barra superior. Abra **Pacientes** e **Atendimentos** para mostrar o que chegou.
- Falar: "Pull: o servidor mandou medicamentos, pessoas, prontuários e atendimentos para o banco local."

**Passo 7 · Online: registrar um atendimento**
- Fazer: aba **Novo atendimento**. São sete etapas; a partir da terceira, avance com **Avançar →**:
  1. **Pessoa:** busque pelo nome e clique num paciente existente.
  2. **Prontuário:** confira os dados → **Salvar e continuar**.
  3. **Atendimento:** local (ex.: `BR-386, km 340`) e queixa principal.
  4. **Sinais vitais:** preencha PA, FC, SpO₂ → **+ Registrar aferição**.
  5. **Glasgow:** ocular, verbal, motora (o total é calculado).
  6. **Triagem:** cor de Manchester e de START.
  7. **Medicação:** escolha um medicamento, dose e via → **+ Adicionar medicação**.

  Por fim, **Salvar atendimento**.
- Falar: "Gravou no SQLite e na Outbox na mesma transação. Como está online, a fila foi enviada na hora." O contador de pendências fica em 0.

**Passo 8 · Portal: ver o atendimento registrado**
- Fazer: no portal, **Atendimentos** → **↻ Atualizar**. O novo atendimento aparece no topo, com origem **online**.

### Banco de dados

**Passo 9 · Inserir um medicamento pelo banco**
- Fazer: no terminal conectado à VM (seção 5), entre no banco:

```bash
sudo -u postgres psql -d medicalfield
```

Cole o comando e Enter:

```sql
INSERT INTO clinical.medicamento (nome, principio_ativo, apresentacao, dose_maxima, unidade, via_padrao)
VALUES ('Ondansetrona', 'ondansetrona', 'ampola 2 mg/mL', 8, 'mg', 'EV');
```

Deve responder `INSERT 0 1`. Saia do banco com `\q`.
- Falar: "Medicamentos só entram pelo servidor, como o enunciado permite. Na sincronização, o servidor sempre vence para eles (ServerWins)."

**Passo 10 · Portal: o medicamento novo**
- Fazer: no portal, **Medicamentos** → **↻ Atualizar**. A Ondansetrona aparece.

**Passo 11 · Cliente: sincronizar de novo**
- Fazer: no cliente, **⟳ Sincronizar**. Comece um **Novo atendimento** até a etapa **Medicação** e mostre a Ondansetrona na lista; depois volte sem salvar.
- Falar: "O pull trouxe só o que mudou desde a última sincronização."

### O offline

**Passo 12 · Offline: registrar uma ocorrência completa**
- Fazer: desligue a chave **Simular Conectividade**. O indicador muda para **OFFLINE**. Em **Novo atendimento**:
  1. **Pessoa:** **+ Nova pessoa** → nome (ex.: `Paciente Offline`), nascimento, sexo, tipo sanguíneo, alergias → **Salvar pessoa**.
  2. **Prontuário:** comorbidades → **Criar prontuário**.
  3. Siga as demais etapas como no passo 7 (**Avançar →**) → **Salvar atendimento**.
- Falar: "Sem rede, tudo grava local. Olhem o contador de pendências subindo." Abra **Pendências** e mostre a Outbox com os itens pendentes e o `local_log`.

**Passo 13 · Portal: o cadastro novo ainda não aparece**
- Fazer: no portal, **Pessoas**, **Prontuários** e **Atendimentos** → **↻ Atualizar**. O "Paciente Offline" não está lá.
- Falar: "O servidor ainda não sabe desse paciente: o cliente trabalhou sozinho."

**Passo 14 · Online: sincronizar para o portal**
- Fazer: ligue a chave **Simular Conectividade**. **Não clique em mais nada.** Em poucos segundos o contador de pendências volta a 0.
- Falar: "O ConnectivityMonitor percebeu a volta da rede e avisou o SyncService, que esvaziou a Outbox sozinho: é o padrão Observer."

**Passo 15 · Portal: o cadastro novo aparece**
- Fazer: no portal, **Prontuários** e **Atendimentos** → **↻ Atualizar**. O atendimento aparece com a marca **criado offline**.
- Falar: "Se o envio fosse repetido, o servidor responderia DUPLICADO: cada item da fila tem uma chave de idempotência."

### Documentos

**Passo 16 · Gerar a ficha de atendimento**
- Fazer: no portal, **Atendimentos** → clique no atendimento offline → **Gerar ficha (PDF)**. Abra o PDF baixado.
- Falar: "O document-service, em Python, pede os dados ao clinical com o mesmo token e desenha a ficha com ReportLab."

**Passo 17 · Enviar a ficha por e-mail**
- Fazer: no mesmo atendimento, escolha **Familiar**, digite um e-mail qualquer (ex.: `familiar@exemplo.com`) → **Enviar por e-mail**. Vá à aba do Mailtrap: a mensagem chega com o PDF anexado. Mostre também **E-mails enviados** no portal.
- Falar: "O envio passa por um Adapter: SMTP aqui, ou arquivo em desenvolvimento. O Mailtrap retém a mensagem, nada sai para fora."

---

## 9. Padrões de projeto no código

O professor pede para explicar os padrões **e mostrar onde estão no código**. Abra os links abaixo em abas antes de começar (cada um já cai na linha certa) e siga esta ordem, que conta uma história: gravar → fila → rede volta → enviar → resolver conflito.

| # | Padrão | Abrir | Falar |
| --- | --- | --- | --- |
| 1 | **Repository** *(sugerido)* | [repositories.ts:8](https://github.com/devpetry/medical-field/blob/main/client/src/main/repositories.ts#L8) (comentário) e [PessoaRepository:16](https://github.com/devpetry/medical-field/blob/main/client/src/main/repositories.ts#L16) | "Todo SQL do cliente fica aqui. A tela e o SyncService só chamam métodos como gravar e listar; se o banco local mudasse, só este arquivo mudaria." |
| 2 | **Transactional Outbox** | [OutboxRepository:188](https://github.com/devpetry/medical-field/blob/main/client/src/main/repositories.ts#L188) e o [INSERT INTO outbox:202](https://github.com/devpetry/medical-field/blob/main/client/src/main/repositories.ts#L202) | "Toda alteração vira um item na fila, com uma chave UUID, na mesma transação do registro. É o que garante que nada se perde sem rede." |
| 3 | **Observer** *(sugerido)* | [ConnectivityMonitor:9](https://github.com/devpetry/medical-field/blob/main/client/src/main/connectivity.ts#L9), [inscrever:22](https://github.com/devpetry/medical-field/blob/main/client/src/main/connectivity.ts#L22) e [core.ts:68:68](https://github.com/devpetry/medical-field/blob/main/client/src/main/core.ts#L68) | "Quem quer saber da conexão se inscreve. O SyncService é um inscrito: quando a chave volta a Online, ele é avisado e esvazia a fila sozinho." |
| 4 | **Strategy** *(sugerido)* | [MergeStrategy:6](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/sync/MergeStrategy.java#L6) e as três implementações: [LastWriteWins:10](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/sync/LastWriteWinsStrategy.java#L10), [AppendOnlyMerge:18](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/sync/AppendOnlyMergeStrategy.java#L18), [ServerWins:8](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/sync/ServerWinsStrategy.java#L8) | "Uma interface, três regras de conflito. O AppendOnly une as listas de sinais vitais e medicações: nenhum registro clínico se perde." |
| 5 | **Factory** | [MergeStrategyFactory.para():20](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/sync/MergeStrategyFactory.java#L20) e o uso em [SyncService.java:128:128](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/sync/SyncService.java#L128) | "Pessoa e prontuário → LastWriteWins; atendimento → AppendOnly; medicamento → ServerWins. O SyncService não sabe qual regra usa: pede à fábrica." |
| 6 | **Adapter** | [EmailSender:12](https://github.com/devpetry/medical-field/blob/main/services/document-service/app/email_sender.py#L12) e [criar_sender():43](https://github.com/devpetry/medical-field/blob/main/services/document-service/app/email_sender.py#L43) | "O serviço só conhece enviar(mensagem). Por trás, SMTP ou arquivo .eml, escolhido pelo .env, sem mudar o código." |
| 7 | **Chain of Responsibility** | [server.js:11:11](https://github.com/devpetry/medical-field/blob/main/services/auth-service/src/server.js#L11) e [server.js:45:45](https://github.com/devpetry/medical-field/blob/main/services/auth-service/src/server.js#L45); os elos em [accessLog:16](https://github.com/devpetry/medical-field/blob/main/services/auth-service/src/middleware.js#L16) e [autenticar:52](https://github.com/devpetry/medical-field/blob/main/services/auth-service/src/middleware.js#L52) | "Cada requisição passa por uma cadeia: primeiro o log de acesso, depois a autenticação, só então a regra de negócio. O mesmo existe no Java ([AccessLogFilter:26](https://github.com/devpetry/medical-field/blob/main/services/clinical-service/src/main/java/br/univates/medicalfield/clinical/config/AccessLogFilter.java#L26)) e no Python ([seguranca_e_auditoria:32](https://github.com/devpetry/medical-field/blob/main/services/document-service/app/main.py#L32))." |

Para fechar: "São os três padrões sugeridos pelo enunciado, Repository, Strategy e Observer, mais quatro de livre escolha, cada um resolvendo um problema real do offline-first." O diagrama [`09-padroes-de-projeto`](diagramas/09-padroes-de-projeto.png) resume a tabela.

---

## 10. Extras, se sobrar tempo

- **Auditoria:** portal → **Auditoria** → **Logs de acesso** (IP, profissional, rota, status, tempo) e **Eventos de sincronização** (estratégia e resultado de cada item).
- **Regra clínica:** no cliente, num atendimento, ponha uma dose acima do máximo: aparece o **Alerta de segurança clínica**. No Swagger ou no Postman, o mesmo atendimento volta **422**.
- **Perfis:** saia do portal e tente entrar com `CRM-RS 12345`: é recusado (só administrador).
- **Swagger:** http://177.44.248.75/docs/ → `POST /auth/login` → **Try it out** → **Execute** → copie o `accessToken` → **Authorize** → cole → teste qualquer rota.
- **Login offline:** com a chave em Offline, **Sair** e entrar de novo com `CRM-RS 12345`.
- **O banco por dentro** (no terminal da VM, dentro do `psql`):

```sql
SELECT data_hora, servico, metodo, rota, status_code, tempo_ms, origem FROM audit.access_log ORDER BY id DESC LIMIT 10;
SELECT entidade, status, estrategia, vencedor FROM audit.sync_evento ORDER BY id DESC LIMIT 10;
SELECT chave, entidade, resultado FROM clinical.idempotencia ORDER BY processado_em DESC LIMIT 5;
```

---

## 11. Se algo der errado

| Sintoma | Fazer (no terminal da VM) |
| --- | --- |
| `ssh` não conecta | Teste a rede (`ping 177.44.248.75`). Se o laboratório bloquear a porta 22, use seu notebook ou o celular como roteador |
| Portal não abre | `sudo systemctl restart nginx` |
| Erro 502 no portal | `sudo systemctl restart medicalfield-clinical medicalfield-auth medicalfield-document` e espere ~30 s |
| Ver o log de um serviço | `sudo journalctl -u medicalfield-clinical -f` (Ctrl+C para sair) |
| 401 no cliente ou no Swagger | O token expira em 12 h: entre de novo |
| Passo 14 não sincroniza sozinho | Espere até 15 s (o cliente testa o servidor a cada 15 s) ou clique em **⟳ Sincronizar** |
| Item em ERRO no cliente | Leia a mensagem em **Pendências**; geralmente é regra clínica (dose ou alergia) — vale mostrar como recurso |
| E-mail não chega | Confira se está na inbox **MedicalField** do Mailtrap; o portal mostra ENVIADO ou o erro em **E-mails enviados** |
| Cliente não abre | Use sempre o `abrir-medicalfield.sh`, não o AppImage direto |
| Rede da sala cai | Sem rede não há GitHub nem VM: use os dados móveis do celular como roteador para abrir o vídeo e os diagramas |

Se um passo falhar, diga o que deveria acontecer e por quê: entender o comportamento vale tanto quanto ver funcionando.

---

## 12. Ao terminar

1. Feche o cliente e saia do portal (**Sair**).
2. No PC do professor, apague o banco local do cliente e os arquivos baixados:

```bash
rm -rf ~/.config/medicalfield-client ~/Downloads/MedicalField-1.0.0.AppImage ~/Downloads/abrir-medicalfield.sh
```

3. No terminal da VM, `exit`.
4. Saia da sua conta do Mailtrap no navegador.

---

## 13. Manutenção da VM (fora do dia)

**Atualizar o código** (mantém dados e `.env`). Na sua máquina, na raiz do repositório:

```bash
(cd services/clinical-service && mvn -q -DskipTests package) && (cd portal && npm run build)
```

```bash
rsync -az --delete --exclude='.git/' --exclude='node_modules/' --exclude='.venv/' --exclude='.env' --exclude='client/' --exclude='video/' --include='services/clinical-service/target/' --include='services/clinical-service/target/clinical-service.jar' --exclude='services/clinical-service/target/**' ./ univates@177.44.248.75:medical-field/
```

```bash
ssh univates@177.44.248.75 "cd medical-field && sudo ./deploy/atualizar.sh"
```

**Liberar o acesso por chave a partir de outra máquina** (para não digitar a senha toda vez):

```bash
ssh-keygen -t ed25519
```

```bash
ssh-copy-id univates@177.44.248.75
```

**Reinstalar do zero** (VM nova): na VM, instale os pacotes, envie o repositório, crie os três `.env` a partir dos `.env.example` e rode o instalador.

```bash
sudo apt-get install -y openjdk-21-jre-headless nodejs npm postgresql nginx python3-venv rsync
```

```bash
sudo ./deploy/install.sh && sudo -u postgres psql -d medicalfield -f db/seed.sql
```

O `install.sh` sobrescreve os `.env` de `/opt/medicalfield`. Depois dele, coloque de novo a senha do SMTP em `/opt/medicalfield/document/.env` (`EMAIL_ADAPTER=smtp`, `SMTP_USER`, `SMTP_PASSWORD`) e rode `sudo systemctl restart medicalfield-document`.
