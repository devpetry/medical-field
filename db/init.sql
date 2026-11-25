-- MedicalField: cria banco, schemas, usuários e permissões.
-- Executar como superusuário do PostgreSQL:
--   psql -U postgres -v auth_pw=... -v clinical_pw=... -v document_pw=... -f db/init.sql
-- As tabelas de cada schema são criadas pelas migrações do próprio serviço.

SELECT 'CREATE DATABASE medicalfield'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'medicalfield')\gexec

\c medicalfield

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mf_auth') THEN CREATE ROLE mf_auth LOGIN; END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mf_clinical') THEN CREATE ROLE mf_clinical LOGIN; END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mf_document') THEN CREATE ROLE mf_document LOGIN; END IF;
END $$;

ALTER ROLE mf_auth PASSWORD :'auth_pw';
ALTER ROLE mf_clinical PASSWORD :'clinical_pw';
ALTER ROLE mf_document PASSWORD :'document_pw';

REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Cada serviço é dono do seu schema.
CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION mf_auth;
CREATE SCHEMA IF NOT EXISTS clinical AUTHORIZATION mf_clinical;
CREATE SCHEMA IF NOT EXISTS document AUTHORIZATION mf_document;
-- audit pertence ao clinical-service; os demais só gravam em audit.access_log
-- (o GRANT INSERT é feito na migração que cria a tabela).
CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION mf_clinical;
GRANT USAGE ON SCHEMA audit TO mf_auth, mf_document;

ALTER ROLE mf_auth SET search_path = auth;
ALTER ROLE mf_clinical SET search_path = clinical, audit;
ALTER ROLE mf_document SET search_path = document;
