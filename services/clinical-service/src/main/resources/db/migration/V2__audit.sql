-- Schema audit: logs de acesso dos três serviços e trilha da sincronização.

CREATE TABLE audit.access_log (
  id              BIGSERIAL PRIMARY KEY,
  data_hora       TIMESTAMPTZ NOT NULL,
  servico         VARCHAR(20) NOT NULL,
  ip_cliente      VARCHAR(60),
  profissional_id BIGINT,
  metodo          VARCHAR(10) NOT NULL,
  rota            VARCHAR(300) NOT NULL,
  status_code     SMALLINT,
  tempo_ms        INTEGER,
  origem          VARCHAR(10) NOT NULL DEFAULT 'ONLINE',
  device_id       VARCHAR(60)
);
CREATE INDEX ix_access_log_data ON audit.access_log (data_hora DESC);

-- auth-service e document-service só podem inserir aqui.
GRANT INSERT ON audit.access_log TO mf_auth, mf_document;
GRANT USAGE ON SEQUENCE audit.access_log_id_seq TO mf_auth, mf_document;

CREATE TABLE audit.sync_evento (
  id              BIGSERIAL PRIMARY KEY,
  data_hora       TIMESTAMPTZ NOT NULL DEFAULT now(),
  device_id       VARCHAR(60),
  profissional_id BIGINT,
  entidade        VARCHAR(20) NOT NULL,
  entidade_id     VARCHAR(60) NOT NULL,
  operacao        VARCHAR(10) NOT NULL,
  status          VARCHAR(30) NOT NULL,
  versao_cliente  INTEGER,
  versao_servidor INTEGER,
  estrategia      VARCHAR(40),
  vencedor        VARCHAR(10),
  antes           JSONB,
  depois          JSONB
);
CREATE INDEX ix_sync_evento_data ON audit.sync_evento (data_hora DESC);
