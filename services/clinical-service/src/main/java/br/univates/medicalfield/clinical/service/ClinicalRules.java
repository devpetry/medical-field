package br.univates.medicalfield.clinical.service;

import br.univates.medicalfield.clinical.domain.Atendimento;
import br.univates.medicalfield.clinical.domain.MedicacaoAdministrada;
import br.univates.medicalfield.clinical.domain.Medicamento;
import br.univates.medicalfield.clinical.domain.Pessoa;
import br.univates.medicalfield.clinical.domain.SinalVital;
import br.univates.medicalfield.clinical.repository.MedicamentoRepository;
import br.univates.medicalfield.clinical.web.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.text.Normalizer;
import java.util.Arrays;
import java.util.Locale;
import java.util.Optional;

/** Regras de segurança clínica — as mesmas que o cliente aplica offline. */
@Component
public class ClinicalRules {

    private final MedicamentoRepository medicamentos;

    public ClinicalRules(MedicamentoRepository medicamentos) {
        this.medicamentos = medicamentos;
    }

    public void validar(Atendimento a, Pessoa pessoa) {
        if (a.glasgowOcular != null || a.glasgowVerbal != null || a.glasgowMotora != null) {
            faixa("Glasgow ocular", a.glasgowOcular, 1, 4);
            faixa("Glasgow verbal", a.glasgowVerbal, 1, 5);
            faixa("Glasgow motora", a.glasgowMotora, 1, 6);
            int total = a.glasgowOcular + a.glasgowVerbal + a.glasgowMotora;
            if (a.glasgowTotal != null && a.glasgowTotal != total) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "Glasgow total não confere com a soma");
            }
            a.glasgowTotal = total;
        }
        for (SinalVital s : a.sinaisVitais) {
            faixaOpc("PA sistólica", s.paSistolica, 40, 300);
            faixaOpc("PA diastólica", s.paDiastolica, 20, 200);
            faixaOpc("FC", s.fc, 20, 250);
            faixaOpc("FR", s.fr, 4, 80);
            faixaOpc("SpO2", s.spo2, 50, 100);
            faixaOpc("Glicemia", s.glicemia, 10, 1000);
            if (s.temperatura != null && (s.temperatura.compareTo(BigDecimal.valueOf(30)) < 0
                    || s.temperatura.compareTo(BigDecimal.valueOf(45)) > 0)) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "Temperatura fora da faixa 30–45 °C");
            }
        }
        for (MedicacaoAdministrada m : a.medicacoes) {
            Medicamento med = medicamentos.findById(m.medicamentoId).orElseThrow(() ->
                    new ApiException(HttpStatus.BAD_REQUEST, "Medicamento " + m.medicamentoId + " não cadastrado"));
            if (m.unidade != null && m.unidade.equalsIgnoreCase(med.unidade) && m.dose.compareTo(med.doseMaxima) > 0) {
                throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "Dose de " + med.nome + " acima do máximo ("
                        + med.doseMaxima.stripTrailingZeros().toPlainString() + " " + med.unidade + ")");
            }
            Optional<String> alergia = alergiaConflitante(pessoa, med);
            if (alergia.isPresent() && !Boolean.TRUE.equals(m.alertaConfirmado)) {
                throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "Paciente com alergia a " + alergia.get()
                        + ": confirme o alerta para administrar " + med.nome);
            }
        }
    }

    /** Alergia da pessoa que aparece no nome, princípio ativo ou alertas do medicamento. */
    public static Optional<String> alergiaConflitante(Pessoa p, Medicamento med) {
        if (p == null || p.alergias == null || p.alergias.isBlank()) return Optional.empty();
        String alvo = norm(med.nome + " " + med.principioAtivo + " " + (med.alertas == null ? "" : med.alertas));
        return Arrays.stream(p.alergias.split("[,;/]"))
                .map(String::trim)
                .filter(t -> t.length() >= 3 && alvo.contains(norm(t)))
                .findFirst();
    }

    static String norm(String s) {
        return Normalizer.normalize(s, Normalizer.Form.NFD).replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT);
    }

    private static void faixa(String nome, Integer v, int min, int max) {
        if (v == null || v < min || v > max) {
            throw new ApiException(HttpStatus.BAD_REQUEST, nome + " deve estar entre " + min + " e " + max);
        }
    }

    private static void faixaOpc(String nome, Integer v, int min, int max) {
        if (v != null) faixa(nome, v, min, max);
    }
}
