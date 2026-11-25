-- MedicalField: dados de apoio para o roteiro de testes.
-- Executar como superusuário, depois que os três serviços subiram uma vez
-- (as migrações criam as tabelas):
--   psql -U postgres -d medicalfield -f db/seed.sql
--
-- Senha de teste de todos os profissionais: MedField@2026

BEGIN;

INSERT INTO auth.profissional (nome, registro, tipo_registro, senha_hash, perfil) VALUES
  ('Ana Souza',   'CRM-RS 12345',  'CRM',        '$2a$10$6n4XTHZWyuhv9TkQGDY4P.3jseKXfT1E.CjsIwJyXAD4xlHXmLWAa', 'SOCORRISTA'),
  ('Bruno Alves', 'COREN-RS 5521', 'COREN',      '$2a$10$6n4XTHZWyuhv9TkQGDY4P.3jseKXfT1E.CjsIwJyXAD4xlHXmLWAa', 'SOCORRISTA'),
  ('Carla Dias',  'SOC-0042',      'SOCORRISTA', '$2a$10$6n4XTHZWyuhv9TkQGDY4P.3jseKXfT1E.CjsIwJyXAD4xlHXmLWAa', 'SOCORRISTA'),
  ('Administrador', 'CRM-RS 99999', 'CRM',       '$2a$10$6n4XTHZWyuhv9TkQGDY4P.3jseKXfT1E.CjsIwJyXAD4xlHXmLWAa', 'ADMIN')
ON CONFLICT (registro) DO NOTHING;

INSERT INTO clinical.medicamento (nome, principio_ativo, apresentacao, dose_maxima, unidade, via_padrao, alertas) VALUES
  ('Soro fisiológico 0,9%', 'cloreto de sódio', 'bolsa 1000 mL', 2000, 'mL', 'EV', NULL),
  ('Dipirona sódica', 'dipirona (metamizol)', 'ampola 500 mg/mL', 1000, 'mg', 'EV',
   'Contraindicado em alergia a dipirona ou metamizol'),
  ('Adrenalina', 'epinefrina', 'ampola 1 mg/mL', 1, 'mg', 'IM', 'Monitorar arritmia e pressão arterial');

INSERT INTO clinical.pessoa (id, nome, cpf, data_nascimento, sexo, tipo_sanguineo, alergias, telefone, email_contato, version, updated_at, updated_by) VALUES
  ('3f1c2a10-0000-4000-8000-000000000001', 'Maria Santos',   '111.222.333-44', '1975-05-02', 'Feminino',  'A+', NULL,         '(51) 99999-1001', NULL, 1, now() - interval '15 days', 1),
  ('3f1c2a10-0000-4000-8000-000000000002', 'Carlos Pereira', '222.333.444-55', '1990-09-19', 'Masculino', 'O-', 'Penicilina', '(51) 99999-1002', NULL, 1, now() - interval '14 days', 1),
  ('3f1c2a10-0000-4000-8000-000000000003', 'Lúcia Rocha',    '333.444.555-66', '1962-01-30', 'Feminino',  'B+', 'Dipirona',   '(51) 99999-1003', NULL, 1, now() - interval '13 days', 2);

INSERT INTO clinical.prontuario (id, pessoa_id, comorbidades, uso_continuo, observacoes, version, updated_at, updated_by) VALUES
  ('5a2b3c40-0000-4000-8000-000000000001', '3f1c2a10-0000-4000-8000-000000000001', 'Diabetes tipo 2', 'Metformina 850 mg', NULL, 1, now() - interval '15 days', 1),
  ('5a2b3c40-0000-4000-8000-000000000002', '3f1c2a10-0000-4000-8000-000000000002', NULL, NULL, 'Atleta amador', 1, now() - interval '14 days', 1),
  ('5a2b3c40-0000-4000-8000-000000000003', '3f1c2a10-0000-4000-8000-000000000003', 'Hipertensão', 'Losartana 50 mg', NULL, 1, now() - interval '13 days', 2);

INSERT INTO clinical.atendimento (id, prontuario_id, profissional_id, device_id, inicio, fim, local, queixa_principal,
    glasgow_ocular, glasgow_verbal, glasgow_motora, glasgow_total, triagem_manchester, triagem_start, conduta, destino,
    status, criado_offline, version, updated_at) VALUES
  ('7c3d4e50-0000-4000-8000-000000000001', '5a2b3c40-0000-4000-8000-000000000001', 1, 'amb-01',
   now() - interval '15 days', now() - interval '15 days' + interval '40 minutes', 'Centro, Lajeado', 'Hipoglicemia',
   4, 5, 6, 15, 'LARANJA', 'AMARELO', 'Glicose oral e observação', 'Hospital Bruno Born', 'ENCERRADO', FALSE, 1, now() - interval '15 days'),
  ('7c3d4e50-0000-4000-8000-000000000002', '5a2b3c40-0000-4000-8000-000000000002', 2, 'amb-02',
   now() - interval '14 days', now() - interval '14 days' + interval '30 minutes', 'RS-130, km 12', 'Entorse de tornozelo',
   4, 5, 6, 15, 'VERDE', 'VERDE', 'Imobilização', 'UPA Lajeado', 'ENCERRADO', FALSE, 1, now() - interval '14 days');

INSERT INTO clinical.sinal_vital (id, atendimento_id, aferido_em, pa_sistolica, pa_diastolica, fc, fr, spo2, temperatura, glicemia) VALUES
  ('9e4f5a60-0000-4000-8000-000000000001', '7c3d4e50-0000-4000-8000-000000000001', now() - interval '15 days', 130, 85, 98, 18, 97, 36.5, 52),
  ('9e4f5a60-0000-4000-8000-000000000002', '7c3d4e50-0000-4000-8000-000000000002', now() - interval '14 days', 120, 80, 88, 16, 99, 36.7, 95);

INSERT INTO clinical.medicacao_administrada (id, atendimento_id, medicamento_id, dose, unidade, via, administrado_em, profissional_id) VALUES
  ('b1c2d3e4-0000-4000-8000-000000000001', '7c3d4e50-0000-4000-8000-000000000001',
   (SELECT id FROM clinical.medicamento WHERE nome = 'Soro fisiológico 0,9%'), 500, 'mL', 'EV', now() - interval '15 days', 1);

COMMIT;

-- Passo 9 do roteiro (inserir medicamento manualmente):
-- INSERT INTO clinical.medicamento (nome, principio_ativo, apresentacao, dose_maxima, unidade, via_padrao, alertas)
-- VALUES ('Ondansetrona', 'ondansetrona', 'ampola 2 mg/mL', 8, 'mg', 'EV', NULL);
