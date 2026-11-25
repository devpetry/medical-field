package br.univates.medicalfield.clinical.web;

import br.univates.medicalfield.clinical.domain.Atendimento;
import br.univates.medicalfield.clinical.domain.Medicamento;
import br.univates.medicalfield.clinical.domain.Pessoa;
import br.univates.medicalfield.clinical.domain.Prontuario;
import br.univates.medicalfield.clinical.repository.AtendimentoRepository;
import br.univates.medicalfield.clinical.repository.MedicamentoRepository;
import br.univates.medicalfield.clinical.repository.PessoaRepository;
import br.univates.medicalfield.clinical.repository.ProntuarioRepository;
import br.univates.medicalfield.clinical.service.CadastroService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@RestController
public class CadastroController {

    private final MedicamentoRepository medicamentos;
    private final PessoaRepository pessoas;
    private final ProntuarioRepository prontuarios;
    private final AtendimentoRepository atendimentos;
    private final CadastroService cadastro;

    public CadastroController(MedicamentoRepository medicamentos, PessoaRepository pessoas,
                              ProntuarioRepository prontuarios, AtendimentoRepository atendimentos,
                              CadastroService cadastro) {
        this.medicamentos = medicamentos;
        this.pessoas = pessoas;
        this.prontuarios = prontuarios;
        this.atendimentos = atendimentos;
        this.cadastro = cadastro;
    }

    @GetMapping("/medicamento")
    List<Medicamento> medicamentos() {
        return medicamentos.findAllByOrderByNome();
    }

    @GetMapping("/pessoa")
    List<Pessoa> pessoas() {
        return pessoas.findAllByOrderByNome();
    }

    @PostMapping("/pessoa")
    ResponseEntity<Pessoa> criarPessoa(@RequestBody Pessoa p, @AuthenticationPrincipal Jwt jwt) {
        return responder(cadastro.criarPessoa(p, Auth.profissional(jwt)));
    }

    @GetMapping("/prontuario")
    List<Prontuario> prontuarios() {
        return prontuarios.findAllByOrderByUpdatedAtDesc();
    }

    @GetMapping("/prontuario/{pessoaId}")
    Prontuario prontuario(@PathVariable UUID pessoaId) {
        return prontuarios.findByPessoaId(pessoaId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Prontuário não encontrado"));
    }

    @PostMapping("/prontuario")
    ResponseEntity<Prontuario> criarProntuario(@RequestBody Prontuario p, @AuthenticationPrincipal Jwt jwt) {
        return responder(cadastro.criarProntuario(p, Auth.profissional(jwt)));
    }

    @GetMapping("/atendimento")
    List<Atendimento> atendimentos() {
        return atendimentos.findAllByOrderByInicioDesc();
    }

    @GetMapping("/atendimento/{pessoaId}")
    List<Atendimento> atendimentosDaPessoa(@PathVariable UUID pessoaId) {
        return prontuarios.findByPessoaId(pessoaId)
                .map(p -> atendimentos.findByProntuarioIdOrderByInicioDesc(p.id))
                .orElse(List.of());
    }

    /** Atendimento completo com paciente, prontuário e medicamentos usados (para a ficha em PDF). */
    @GetMapping("/atendimento/detalhe/{atendimentoId}")
    Map<String, Object> detalhe(@PathVariable UUID atendimentoId) {
        Atendimento a = atendimentos.findById(atendimentoId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Atendimento não encontrado"));
        Prontuario pr = prontuarios.findById(a.prontuarioId).orElseThrow();
        Pessoa pe = pessoas.findById(pr.pessoaId).orElseThrow();
        var ids = a.medicacoes.stream().map(m -> m.medicamentoId).filter(Objects::nonNull).distinct().toList();
        return Map.of("atendimento", a, "prontuario", pr, "pessoa", pe,
                "medicamentos", medicamentos.findAllById(ids));
    }

    @PostMapping("/atendimento")
    ResponseEntity<Atendimento> criarAtendimento(@RequestBody Atendimento a, @AuthenticationPrincipal Jwt jwt) {
        return responder(cadastro.criarAtendimento(a, Auth.profissional(jwt)));
    }

    private static <T> ResponseEntity<T> responder(CadastroService.Resultado<T> r) {
        return ResponseEntity.status(r.criado() ? HttpStatus.CREATED : HttpStatus.OK).body(r.corpo());
    }
}
