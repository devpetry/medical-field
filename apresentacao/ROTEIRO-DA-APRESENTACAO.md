# Roteiro da apresentação (cola rápida)

Tudo o que você digita ou clica no dia, na ordem. As explicações ficam no [guia de demonstração](GUIA-DE-DEMONSTRACAO.md).

## 1. Endereços e contas

| O quê | Valor |
| --- | --- |
| Portal | http://177.44.248.75 |
| Swagger | http://177.44.248.75/docs/ |
| API (Postman, cliente) | http://177.44.248.75/api |
| Portal (administrador) | `CRM-RS 99999` |
| Cliente (socorrista) | `CRM-RS 12345` · Ana Souza |
| Outros socorristas | `COREN-RS 5521` · `SOC-0042` |
| Senha de todos | `MedField@2026` |
| E-mails | inbox **MedicalField** no Mailtrap |
| SSH | `ssh univates@177.44.248.75` |

## 2. Antes de entrar na sala

```bash
./deploy/verificar.sh
```

Tem que terminar em **Tudo certo** (18 checagens: portal, Swagger, 401 sem token, logins, rotas, 403 de perfil e PDF).

Para começar o roteiro do zero (apaga os dados clínicos, e-mails e logs; mantém os profissionais):

```bash
ssh univates@177.44.248.75 "cd medical-field && sudo ./deploy/zerar.sh"
```

Checklist:

- [ ] `verificar.sh` → Tudo certo
- [ ] VM zerada; Ondansetrona **ainda não** inserida (é o passo 9)
- [ ] Executável do cliente no pendrive (seção 4)
- [ ] Abas abertas: portal, Swagger, Mailtrap e um terminal com SSH na VM
- [ ] Postman com o environment **MedicalField · VM Univates**
- [ ] Plano B: `video/MedicalField_video_explicativo.mp4` e os [diagramas](diagramas)

## 3. Banco de dados

Entrar no banco da VM:

```bash
ssh -t univates@177.44.248.75 sudo -u postgres psql -d medicalfield
```

**Passo 9** (inserir medicamento):

```sql
INSERT INTO clinical.medicamento (nome, principio_ativo, apresentacao, dose_maxima, unidade, via_padrao)
VALUES ('Ondansetrona', 'ondansetrona', 'ampola 2 mg/mL', 8, 'mg', 'EV');
```

Consultas úteis para mostrar:

```sql
SELECT nome, dose_maxima, unidade FROM clinical.medicamento ORDER BY nome;
SELECT data_hora, servico, metodo, rota, status_code, tempo_ms, origem FROM audit.access_log ORDER BY id DESC LIMIT 10;
SELECT entidade, status, estrategia, vencedor FROM audit.sync_evento ORDER BY id DESC LIMIT 10;
SELECT chave, entidade, resultado FROM clinical.idempotencia ORDER BY processado_em DESC LIMIT 5;
```

## 4. Cliente no notebook (Linux)

Baixe em https://github.com/devpetry/medical-field/releases/tag/v1.0.0 os arquivos `MedicalField-1.0.0.AppImage` e `abrir-medicalfield.sh`. Leve num pendrive para não depender da rede do laboratório. Na mesma pasta:

```bash
chmod +x abrir-medicalfield.sh && ./abrir-medicalfield.sh
```

O script funciona mesmo sem a biblioteca FUSE e com o sandbox do Chromium bloqueado (Ubuntu 22.04+ e 24.04+). O cliente já aponta para a VM. Para outro servidor ou outro nome de dispositivo:

```bash
./abrir-medicalfield.sh --api=http://<ip>/api --dispositivo=amb-03
```

Para recomeçar o cliente do zero, apague o banco local dele (`~/.config/medicalfield-client/medicalfield.db`).

## 5. Os 17 passos

Os passos 12 a 15 são o coração da demonstração: vá devagar e narre.

| # | Onde | Fazer | Falar |
| --- | --- | --- | --- |
| 1 | Portal | Entrar com `CRM-RS 99999` | "O login gera um JWT que os três serviços validam sozinhos. Só administrador entra no portal." |
| 2 | Portal | Profissionais, Medicamentos, Pessoas | "Cadastros de apoio, vindos do auth e do clinical." |
| 3 | Portal | Prontuários | — |
| 4 | Portal | Atendimentos | — |
| 5 | Cliente | Entrar com `CRM-RS 12345`, chave em Online | "Este notebook é a ambulância. O cliente tem banco SQLite próprio." |
| 6 | Cliente | **Sincronizar** | "Pull: baixou medicamentos, pessoas e atendimentos." |
| 7 | Cliente | Novo atendimento → salvar | "Gravou local e na Outbox; como está online, enviou na hora." |
| 8 | Portal | Atendimentos (atualizar) | "Chegou ao servidor." |
| 9 | Terminal | `INSERT` da seção 3 | "Medicamentos só entram pelo servidor, como pede o enunciado." |
| 10 | Portal | Medicamentos | "A Ondansetrona já aparece no portal…" |
| 11 | Cliente | **Sincronizar** | "…e agora chegou ao cliente pelo pull." |
| 12 | Cliente | Chave em **Offline** → nova pessoa, prontuário e atendimento | "Sem rede, tudo grava local. Olhem o contador de pendências subindo." |
| 13 | Portal | Prontuários e Atendimentos | "O servidor ainda não sabe desse paciente." |
| 14 | Cliente | Chave em **Online** (não clicar em nada) | "O ConnectivityMonitor (Observer) avisou o SyncService, que esvaziou a Outbox sozinho." |
| 15 | Portal | Prontuários e Atendimentos | "Chegou, marcado 'criado offline'. Reenvios não duplicam: cada item tem chave de idempotência." |
| 16 | Portal | Atendimento → **Gerar ficha (PDF)** | "O document-service, em Python, pede os dados ao clinical e gera o PDF." |
| 17 | Portal + Mailtrap | **Enviar por e-mail** → mostrar a inbox | "E-mail com a ficha anexada. O envio usa um Adapter: SMTP ou arquivo." |

## 6. Extras, se sobrar tempo

- **Auditoria** no portal: cada requisição com IP, profissional, rota, status e tempo; a aba de sincronização mostra a estratégia usada em cada item.
- **Regra clínica:** no Postman, `POST /atendimento — dose acima do máximo` devolve **422**.
- **Perfis:** no Postman, `Socorrista em rota de admin deve dar 403`; no portal, entrar com `CRM-RS 12345` é recusado.
- **Swagger:** http://177.44.248.75/docs/ → Authorize com o token do login → Try it out.
- **Login offline:** com a chave em Offline, sair e entrar de novo no cliente.

## 7. Se algo der errado

| Sintoma | Fazer |
| --- | --- |
| Portal não abre | `ssh univates@177.44.248.75 sudo systemctl restart nginx` |
| 502 no portal | `ssh univates@177.44.248.75 sudo systemctl restart medicalfield-clinical medicalfield-auth medicalfield-document` e esperar ~30 s |
| Ver o log de um serviço | `ssh univates@177.44.248.75 sudo journalctl -u medicalfield-clinical -f` |
| 401 no cliente ou no Postman | Token expirou (12 h): entrar de novo |
| Passo 14 não sincroniza sozinho | Esperar até 15 s (o monitor testa o servidor a cada 15 s) ou clicar **Sincronizar** |
| Item em ERRO no cliente | Ler a mensagem em **Pendências**: geralmente regra clínica (dose ou alergia) — vale mostrar como recurso |
| E-mail não chega | Conferir a inbox certa no Mailtrap; o histórico do portal mostra ENVIADO ou o erro |
| AppImage não abre | Usar sempre o `abrir-medicalfield.sh` (seção 4) |
| Rede da sala falhar | Vídeo explicativo e diagramas |

Se um passo falhar, diga o que deveria acontecer e por quê: entender o comportamento vale tanto quanto ver funcionando.

## 8. Atualizar ou reinstalar a VM

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

**Reinstalar do zero** (VM nova): instale os pacotes, crie os três `.env` a partir dos `.env.example` e rode o instalador.

```bash
sudo apt-get install -y openjdk-21-jre-headless nodejs npm postgresql nginx python3-venv rsync
```

```bash
sudo ./deploy/install.sh && sudo -u postgres psql -d medicalfield -f db/seed.sql
```

O `install.sh` sobrescreve os `.env` de `/opt/medicalfield`: depois dele, coloque de novo a senha do SMTP em `/opt/medicalfield/document/.env` (`EMAIL_ADAPTER=smtp`, `SMTP_USER`, `SMTP_PASSWORD`) e rode `sudo systemctl restart medicalfield-document`.
