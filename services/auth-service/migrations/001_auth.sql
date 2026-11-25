CREATE TABLE auth.profissional (
  id            BIGSERIAL PRIMARY KEY,
  nome          VARCHAR(150) NOT NULL,
  registro      VARCHAR(40) NOT NULL UNIQUE,
  tipo_registro VARCHAR(12) NOT NULL CHECK (tipo_registro IN ('CRM', 'COREN', 'SOCORRISTA')),
  senha_hash    VARCHAR(100) NOT NULL,
  perfil        VARCHAR(12) NOT NULL DEFAULT 'SOCORRISTA' CHECK (perfil IN ('SOCORRISTA', 'ADMIN')),
  ativo         BOOLEAN NOT NULL DEFAULT TRUE,
  criado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);
