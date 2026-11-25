CREATE TABLE document.envio_email (
  id                BIGSERIAL PRIMARY KEY,
  atendimento_id    UUID NOT NULL,
  destinatario      VARCHAR(150) NOT NULL,
  nome_destinatario VARCHAR(150),
  relacao           VARCHAR(20) NOT NULL CHECK (relacao IN ('PACIENTE', 'FAMILIAR')),
  status            VARCHAR(10) NOT NULL,
  erro              TEXT,
  enviado_em        TIMESTAMPTZ NOT NULL DEFAULT now(),
  profissional_id   BIGINT
);
