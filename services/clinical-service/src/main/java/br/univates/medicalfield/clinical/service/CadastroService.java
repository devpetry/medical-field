package br.univates.medicalfield.clinical.service;

import br.univates.medicalfield.clinical.domain.Atendimento;
import br.univates.medicalfield.clinical.domain.Pessoa;
import br.univates.medicalfield.clinical.domain.Prontuario;
import br.univates.medicalfield.clinical.repository.AtendimentoRepository;
import br.univates.medicalfield.clinical.repository.PessoaRepository;
import br.univates.medicalfield.clinical.repository.ProntuarioRepository;
import br.univates.medicalfield.clinical.web.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;

/**
 * Cadastro via REST (Postman/portal). Os POST são idempotentes: o UUID vem do
 * cliente e um id repetido devolve o registro existente (200) em vez de duplicar.
 */
@Service
public class CadastroService {

    public record Resultado<T>(T corpo, boolean criado) {}

    private final PessoaRepository pessoas;
    private final ProntuarioRepository prontuarios;
    private final AtendimentoRepository atendimentos;
    private final ClinicalRules regras;

    public CadastroService(PessoaRepository pessoas, ProntuarioRepository prontuarios,
                           AtendimentoRepository atendimentos, ClinicalRules regras) {
        this.pessoas = pessoas;
        this.prontuarios = prontuarios;
        this.atendimentos = atendimentos;
        this.regras = regras;
    }

    @Transactional
    public Resultado<Pessoa> criarPessoa(Pessoa p, Long profissional) {
        exigirId(p.id);
        var existente = pessoas.findById(p.id);
        if (existente.isPresent()) return new Resultado<>(existente.get(), false);
        if (p.nome == null || p.nome.isBlank()) throw new ApiException(HttpStatus.BAD_REQUEST, "Nome é obrigatório");
        p.updatedAt = p.updatedAt == null ? agora() : p.updatedAt;
        p.updatedBy = profissional;
        p.marcar(1, agora());
        return new Resultado<>(pessoas.save(p), true);
    }

    @Transactional
    public Resultado<Prontuario> criarProntuario(Prontuario p, Long profissional) {
        exigirId(p.id);
        var existente = prontuarios.findById(p.id);
        if (existente.isPresent()) return new Resultado<>(existente.get(), false);
        if (p.pessoaId == null || !pessoas.existsById(p.pessoaId)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Pessoa do prontuário não encontrada");
        }
        if (prontuarios.findByPessoaId(p.pessoaId).isPresent()) {
            throw new ApiException(HttpStatus.CONFLICT, "Esta pessoa já tem prontuário");
        }
        p.updatedAt = p.updatedAt == null ? agora() : p.updatedAt;
        p.updatedBy = profissional;
        p.marcar(1, agora());
        return new Resultado<>(prontuarios.save(p), true);
    }

    @Transactional
    public Resultado<Atendimento> criarAtendimento(Atendimento a, Long profissional) {
        exigirId(a.id);
        var existente = atendimentos.findById(a.id);
        if (existente.isPresent()) return new Resultado<>(existente.get(), false);
        Prontuario pr = a.prontuarioId == null ? null : prontuarios.findById(a.prontuarioId).orElse(null);
        if (pr == null) throw new ApiException(HttpStatus.BAD_REQUEST, "Prontuário do atendimento não encontrado");
        preparar(a, profissional);
        regras.validar(a, pessoas.findById(pr.pessoaId).orElse(null));
        a.marcar(1, agora());
        return new Resultado<>(atendimentos.save(a), true);
    }

    public static void preparar(Atendimento a, Long profissional) {
        if (a.profissionalId == null) a.profissionalId = profissional;
        if (a.inicio == null) a.inicio = agora();
        if (a.status == null) a.status = "ABERTO";
        if (a.criadoOffline == null) a.criadoOffline = false;
        if (a.updatedAt == null) a.updatedAt = agora();
        a.medicacoes.forEach(m -> {
            if (m.profissionalId == null) m.profissionalId = a.profissionalId;
            if (m.alertaConfirmado == null) m.alertaConfirmado = false;
        });
    }

    private static void exigirId(Object id) {
        if (id == null) throw new ApiException(HttpStatus.BAD_REQUEST, "O id (UUID gerado no dispositivo) é obrigatório");
    }

    static OffsetDateTime agora() {
        return OffsetDateTime.now(ZoneOffset.UTC);
    }
}
