# MedicalField

Prontuário médico de emergência **offline-first** — Trabalho final de Arquiteturas de Software (Univates, 2026/B).

O socorrista registra o atendimento no cliente desktop, que grava tudo primeiro num SQLite local e enfileira as alterações numa Outbox. Quando a conexão volta, o cliente sincroniza com o servidor central. A documentação completa (arquitetura, APIs, bancos, sincronização e roteiro de testes) está no documento de arquitetura do projeto.

## Estrutura

| Pasta | Componente | Tecnologia |
| --- | --- | --- |
| `services/auth-service` | Login e emissão do JWT, profissionais | Node.js 20+ · Express |
| `services/clinical-service` | Pessoas, prontuários, atendimentos, sincronização, auditoria | Java 21 · Spring Boot 3 · Flyway |
| `services/document-service` | Ficha em PDF e envio por e-mail | Python 3.12 · FastAPI · ReportLab |
| `portal` | Portal administrativo | React · Vite · TypeScript |
| `client` | Cliente desktop offline-first | Electron · React · TypeScript · SQLite (`node:sqlite`) |
| `db` | `init.sql` (banco, schemas, usuários) e `seed.sql` (dados do roteiro) | PostgreSQL 16 |
| `deploy` | Nginx, unidades systemd e `install.sh` para a VM | — |
| `postman` | Coleção com todas as rotas | Postman v2.1 |
| `video` | Vídeo explicativo e o código que o gera | — |

## Credenciais de teste (seed)

Todos os profissionais do `db/seed.sql` usam a senha `MedField@2026`:

| Registro | Tipo | Perfil |
| --- | --- | --- |
| `CRM-RS 12345` | CRM | Socorrista (Ana Souza) |
| `COREN-RS 5521` | COREN | Socorrista (Bruno Alves) |
| `SOC-0042` | SOCORRISTA | Socorrista (Carla Dias) |
| `CRM-RS 99999` | CRM | Administrador |

## Rodando localmente

Pré-requisitos: Java 21 + Maven, Node.js 20+, Python 3.12, PostgreSQL 16 (ou Docker).

1. **Banco.** Com Docker, um PostgreSQL de desenvolvimento:

   ```bash
   docker run -d --name mf-postgres -e POSTGRES_PASSWORD=admin -p 127.0.0.1:55432:5432 postgres:16
   docker cp db/init.sql mf-postgres:/tmp/init.sql
   docker exec mf-postgres psql -U postgres -v auth_pw=mf_auth_dev -v clinical_pw=mf_clinical_dev -v document_pw=mf_document_dev -f /tmp/init.sql
   ```

2. **Configuração.** Em cada serviço, copie `.env.example` para `.env` e ajuste `DB_URL`, `DB_PASSWORD` e `JWT_SECRET` (o mesmo segredo, com 32+ caracteres, nos três serviços).

3. **Serviços** (nesta ordem: o clinical-service cria o schema `audit`):

   ```bash
   cd services/clinical-service && mvn -DskipTests package && set -a && . ./.env && set +a && java -jar target/clinical-service.jar
   ```

   ```bash
   cd services/auth-service && npm install && npm start
   ```

   ```bash
   cd services/document-service && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python run.py
   ```

4. **Dados do roteiro:**

   ```bash
   docker cp db/seed.sql mf-postgres:/tmp/seed.sql && docker exec mf-postgres psql -U postgres -d medicalfield -f /tmp/seed.sql
   ```

5. **Portal** (o Vite faz o papel do Nginx em desenvolvimento): `cd portal && npm install && npm run dev` → <http://localhost:5173>

6. **Cliente desktop:** `cd client && npm install && npm run build && API_URL=http://localhost:5173/api npm start`

   Variáveis opcionais: `DEVICE_ID` (identificação do dispositivo, ex. `amb-03`) e `MF_DB` (arquivo do SQLite).

No `document-service`, `EMAIL_ADAPTER=file` grava os e-mails como `.eml` em `EMAIL_DIR`, útil sem servidor SMTP. Na apresentação use `EMAIL_ADAPTER=smtp` com Mailtrap ou Gmail (senha de app).

## Implantação na VM da Univates

Sem contêineres: serviços `systemd` e Nginx na porta 80. Na VM, com os `.env` preenchidos:

```bash
sudo ./deploy/install.sh
```

```bash
sudo -u postgres psql -d medicalfield -f db/seed.sql
```

O script cria o banco e os usuários, compila e instala os três serviços em `/opt/medicalfield`, publica o portal em `/var/www/medicalfield` e configura o Nginx (`deploy/nginx/medicalfield.conf`). No notebook da apresentação, o cliente aponta para a VM com `API_URL=http://<ip-da-vm>/api`.

## Roteiro de testes

| # | Onde | Como |
| --- | --- | --- |
| 1–4 | Portal | Entrar e abrir Profissionais/Medicamentos/Pessoas, Prontuários e Atendimentos |
| 5 | Cliente | Entrar (chave "Simular Conectividade" em Online) |
| 6 | Cliente | Botão **Sincronizar** (pull) |
| 7 | Cliente | Online: Novo atendimento → salvar; a Outbox é enviada na hora |
| 8 | Portal | Atendimentos → o registro aparece |
| 9 | Banco | `INSERT` de medicamento (exemplo no fim de `db/seed.sql`) |
| 10–11 | Portal / Cliente | Medicamento novo no portal; **Sincronizar** no cliente |
| 12 | Cliente | Chave em Offline: nova pessoa, prontuário e atendimento; o contador de pendências sobe |
| 13 | Portal | O cadastro novo ainda não aparece |
| 14 | Cliente | Chave em Online: o SyncService envia a Outbox sozinho |
| 15 | Portal | O atendimento aparece com a marca "criado offline" |
| 16–17 | Portal ou cliente | **Gerar ficha (PDF)** e **Enviar por e-mail** |

A coleção `postman/MedicalField.postman_collection.json` cobre todas as rotas: rode `POST /auth/login` primeiro e ajuste `baseUrl` para `http://<ip-da-vm>/api`.
