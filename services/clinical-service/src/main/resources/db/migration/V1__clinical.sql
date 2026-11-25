-- Schema clinical: cadastros e atendimentos.
-- `version` e `updated_at` vêm do dispositivo (merge); `sincronizado_em` é o
-- relógio do servidor e serve de marcador para o GET /sync/pull.

CREATE TABLE clinical.medicamento (
  id              BIGSERIAL PRIMARY KEY,
  nome            VARCHAR(120) NOT NULL,
  principio_ativo VARCHAR(120) NOT NULL,
  apresentacao    VARCHAR(120),
  dose_maxima     NUMERIC(10, 2) NOT NULL,
  unidade         VARCHAR(10) NOT NULL,
  via_padrao      VARCHAR(10),
  alertas         TEXT,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clinical.pessoa (
  id                 UUID PRIMARY KEY,
  nome               VARCHAR(150) NOT NULL,
  cpf                VARCHAR(14) UNIQUE,
  data_nascimento    DATE,
  sexo               VARCHAR(20),
  tipo_sanguineo     VARCHAR(3),
  alergias           TEXT,
  telefone           VARCHAR(30),
  email_contato      VARCHAR(150),
  contato_emergencia VARCHAR(150),
  version            INTEGER NOT NULL DEFAULT 1,
  updated_at         TIMESTAMPTZ NOT NULL,
  updated_by         BIGINT,
  sincronizado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clinical.prontuario (
  id              UUID PRIMARY KEY,
  pessoa_id       UUID NOT NULL UNIQUE REFERENCES clinical.pessoa (id),
  comorbidades    TEXT,
  uso_continuo    TEXT,
  observacoes     TEXT,
  version         INTEGER NOT NULL DEFAULT 1,
  updated_at      TIMESTAMPTZ NOT NULL,
  updated_by      BIGINT,
  sincronizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clinical.atendimento (
  id                 UUID PRIMARY KEY,
  prontuario_id      UUID NOT NULL REFERENCES clinical.prontuario (id),
  profissional_id    BIGINT NOT NULL,
  device_id          VARCHAR(60),
  inicio             TIMESTAMPTZ NOT NULL,
  fim                TIMESTAMPTZ,
  local              VARCHAR(200),
  queixa_principal   TEXT,
  glasgow_ocular     SMALLINT CHECK (glasgow_ocular BETWEEN 1 AND 4),
  glasgow_verbal     SMALLINT CHECK (glasgow_verbal BETWEEN 1 AND 5),
  glasgow_motora     SMALLINT CHECK (glasgow_motora BETWEEN 1 AND 6),
  glasgow_total      SMALLINT CHECK (glasgow_total BETWEEN 3 AND 15),
  triagem_manchester VARCHAR(10),
  triagem_start      VARCHAR(10),
  conduta            TEXT,
  destino            VARCHAR(150),
  status             VARCHAR(10) NOT NULL DEFAULT 'ABERTO',
  criado_offline     BOOLEAN NOT NULL DEFAULT FALSE,
  version            INTEGER NOT NULL DEFAULT 1,
  updated_at         TIMESTAMPTZ NOT NULL,
  sincronizado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_atendimento_prontuario ON clinical.atendimento (prontuario_id);

CREATE TABLE clinical.sinal_vital (
  id             UUID PRIMARY KEY,
  atendimento_id UUID NOT NULL REFERENCES clinical.atendimento (id) ON DELETE CASCADE,
  aferido_em     TIMESTAMPTZ NOT NULL,
  pa_sistolica   SMALLINT,
  pa_diastolica  SMALLINT,
  fc             SMALLINT,
  fr             SMALLINT,
  spo2           SMALLINT,
  temperatura    NUMERIC(4, 1),
  glicemia       SMALLINT
);

CREATE TABLE clinical.medicacao_administrada (
  id                UUID PRIMARY KEY,
  atendimento_id    UUID NOT NULL REFERENCES clinical.atendimento (id) ON DELETE CASCADE,
  medicamento_id    BIGINT NOT NULL REFERENCES clinical.medicamento (id),
  dose              NUMERIC(10, 2) NOT NULL,
  unidade           VARCHAR(10) NOT NULL,
  via               VARCHAR(10),
  administrado_em   TIMESTAMPTZ NOT NULL,
  profissional_id   BIGINT,
  alerta_confirmado BOOLEAN NOT NULL DEFAULT FALSE
);

-- Chave de idempotência = deviceId:outboxId (texto).
CREATE TABLE clinical.idempotencia (
  chave         VARCHAR(120) PRIMARY KEY,
  entidade      VARCHAR(20) NOT NULL,
  payload_hash  VARCHAR(64) NOT NULL,
  resultado     VARCHAR(30) NOT NULL,
  processado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
