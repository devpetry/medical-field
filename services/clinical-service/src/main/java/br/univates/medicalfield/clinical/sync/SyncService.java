package br.univates.medicalfield.clinical.sync;

import br.univates.medicalfield.clinical.domain.Atendimento;
import br.univates.medicalfield.clinical.domain.Pessoa;
import br.univates.medicalfield.clinical.domain.Prontuario;
import br.univates.medicalfield.clinical.domain.Versionado;
import br.univates.medicalfield.clinical.repository.AtendimentoRepository;
import br.univates.medicalfield.clinical.repository.MedicamentoRepository;
import br.univates.medicalfield.clinical.repository.PessoaRepository;
import br.univates.medicalfield.clinical.repository.ProntuarioRepository;
import br.univates.medicalfield.clinical.service.CadastroService;
import br.univates.medicalfield.clinical.service.ClinicalRules;
import br.univates.medicalfield.clinical.sync.SyncDtos.*;
import br.univates.medicalfield.clinical.web.ApiException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;

/**
 * Push: aplica cada item da Outbox numa transação própria, com idempotência
 * (deviceId:outboxId), resolução de conflito por Strategy e registro em
 * audit.sync_evento. Pull: devolve o que mudou desde a última sincronização.
 */
@Service
public class SyncService {

    private final ObjectMapper mapper;
    private final PessoaRepository pessoas;
    private final ProntuarioRepository prontuarios;
    private final AtendimentoRepository atendimentos;
    private final MedicamentoRepository medicamentos;
    private final ClinicalRules regras;
    private final MergeStrategyFactory estrategias;
    private final JdbcTemplate jdbc;
    private final TransactionTemplate tx;

    public SyncService(ObjectMapper mapper, PessoaRepository pessoas, ProntuarioRepository prontuarios,
                       AtendimentoRepository atendimentos, MedicamentoRepository medicamentos, ClinicalRules regras,
                       MergeStrategyFactory estrategias, JdbcTemplate jdbc, TransactionTemplate tx) {
        this.mapper = mapper;
        this.pessoas = pessoas;
        this.prontuarios = prontuarios;
        this.atendimentos = atendimentos;
        this.medicamentos = medicamentos;
        this.regras = regras;
        this.estrategias = estrategias;
        this.jdbc = jdbc;
        this.tx = tx;
    }

    // ------------------------------------------------------------------ push
    public PushResponse push(PushRequest req, Long profissional) {
        if (req.deviceId() == null || req.deviceId().isBlank()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "deviceId é obrigatório");
        }
        List<ItemResultado> resultados = new ArrayList<>();
        for (PushItem item : req.itens() == null ? List.<PushItem>of() : req.itens()) {
            resultados.add(processar(req.deviceId(), item, profissional));
        }
        return new PushResponse(resultados, agora());
    }

    private ItemResultado processar(String device, PushItem item, Long profissional) {
        try {
            if (item.outboxId() == null || item.payload() == null) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "Item sem outboxId ou payload");
            }
            Entidade ent = entidade(item.entidade());
            return tx.execute(st -> aplicar(device, ent, item, profissional));
        } catch (ApiException e) {
            return erro(device, item, profissional, e.getMessage());
        } catch (RuntimeException e) {
            // Erro inesperado (ex.: restrição do banco) vira ERRO só neste item, sem travar o resto da Outbox.
            return erro(device, item, profissional, "Falha ao aplicar o item: " + e.getClass().getSimpleName());
        }
    }

    private ItemResultado erro(String device, PushItem item, Long profissional, String mensagem) {
        evento(device, profissional, item.entidade(), item.payload() == null ? "?" : item.payload().path("id").asText(),
                item.operacao(), "ERRO", null, null, null, null, item.payload());
        return new ItemResultado(item.outboxId(), "ERRO", null, null, mensagem);
    }

    private ItemResultado aplicar(String device, Entidade ent, PushItem item, Long profissional) {
        String chave = item.chave() != null && !item.chave().isBlank() ? item.chave() : device + ":" + item.outboxId();
        String hash = sha256(item.payload().toString());
        UUID id = uuid(item.payload());

        var anterior = jdbc.queryForList("SELECT payload_hash FROM clinical.idempotencia WHERE chave = ?", String.class, chave);
        if (!anterior.isEmpty()) {
            if (!anterior.get(0).equals(hash)) {
                throw new ApiException(HttpStatus.CONFLICT, "Chave de idempotência " + chave + " reutilizada com outro conteúdo");
            }
            Versionado atual = buscar(ent, id);
            return new ItemResultado(item.outboxId(), "DUPLICADO", null, atual == null ? null : atual.versao(), null);
        }
        if (ent == Entidade.MEDICAMENTO) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "Medicamentos são cadastrados apenas no servidor");
        }

        Versionado atual = buscar(ent, id);
        ObjectNode antes = atual == null ? null : mapper.valueToTree(atual);
        ObjectNode novo;
        String status, vencedor = null, estrategia = null;
        int versao;
        if (atual == null) {
            novo = item.payload();
            status = "APLICADO";
            versao = 1;
        } else if (item.baseVersion() != null && item.baseVersion().equals(atual.versao())) {
            novo = item.payload();
            status = "APLICADO";
            versao = atual.versao() + 1;
        } else {
            MergeStrategy s = estrategias.para(ent);
            var r = s.mesclar(antes, item.payload());
            novo = r.registro();
            vencedor = r.vencedor();
            estrategia = s.nome();
            status = "CONFLITO_RESOLVIDO";
            versao = atual.versao() + 1;
        }
        Versionado salvo = salvar(ent, novo, profissional, versao, device);
        jdbc.update("INSERT INTO clinical.idempotencia (chave, entidade, payload_hash, resultado) VALUES (?, ?, ?, ?)",
                chave, ent.name(), hash, status);
        evento(device, profissional, ent.name(), id.toString(), item.operacao(), status,
                item.payload().path("version").isInt() ? item.payload().get("version").asInt() : null,
                atual == null ? null : atual.versao(), estrategia, vencedor, antes, mapper.valueToTree(salvo));
        return new ItemResultado(item.outboxId(), status, vencedor, versao, null);
    }

    private Versionado salvar(Entidade ent, ObjectNode json, Long profissional, int versao, String device) {
        OffsetDateTime agora = agora();
        switch (ent) {
            case PESSOA -> {
                Pessoa p = ler(json, Pessoa.class);
                if (p.nome == null || p.nome.isBlank()) throw new ApiException(HttpStatus.BAD_REQUEST, "Nome é obrigatório");
                if (p.updatedAt == null) p.updatedAt = agora;
                if (p.updatedBy == null) p.updatedBy = profissional;
                p.marcar(versao, agora);
                return pessoas.save(p);
            }
            case PRONTUARIO -> {
                Prontuario p = ler(json, Prontuario.class);
                if (p.pessoaId == null || !pessoas.existsById(p.pessoaId)) {
                    throw new ApiException(HttpStatus.BAD_REQUEST, "Pessoa do prontuário ainda não existe no servidor");
                }
                prontuarios.findByPessoaId(p.pessoaId).filter(o -> !o.id.equals(p.id)).ifPresent(o -> {
                    throw new ApiException(HttpStatus.CONFLICT, "Esta pessoa já tem outro prontuário");
                });
                if (p.updatedAt == null) p.updatedAt = agora;
                if (p.updatedBy == null) p.updatedBy = profissional;
                p.marcar(versao, agora);
                return prontuarios.save(p);
            }
            case ATENDIMENTO -> {
                Atendimento a = ler(json, Atendimento.class);
                Prontuario pr = a.prontuarioId == null ? null : prontuarios.findById(a.prontuarioId).orElse(null);
                if (pr == null) throw new ApiException(HttpStatus.BAD_REQUEST, "Prontuário do atendimento ainda não existe no servidor");
                if (a.deviceId == null) a.deviceId = device;
                CadastroService.preparar(a, profissional);
                regras.validar(a, pessoas.findById(pr.pessoaId).orElse(null));
                a.marcar(versao, agora);
                return atendimentos.save(a);
            }
            default -> throw new ApiException(HttpStatus.BAD_REQUEST, "Entidade não suportada");
        }
    }

    private Versionado buscar(Entidade ent, UUID id) {
        return switch (ent) {
            case PESSOA -> pessoas.findById(id).orElse(null);
            case PRONTUARIO -> prontuarios.findById(id).orElse(null);
            case ATENDIMENTO -> atendimentos.findById(id).orElse(null);
            case MEDICAMENTO -> null;
        };
    }

    // ------------------------------------------------------------------ pull
    public PullResponse pull(OffsetDateTime since) {
        OffsetDateTime servidor = agora();
        if (since == null) {
            return new PullResponse(medicamentos.findAllByOrderByNome(), pessoas.findAllByOrderByNome(),
                    prontuarios.findAll(), atendimentos.findAllByOrderByInicioDesc(), servidor);
        }
        // Margem de 30 s: cobre uma gravação que começou antes do pull anterior e só terminou depois.
        // Receber de novo um registro não faz mal, porque o cliente grava por upsert.
        OffsetDateTime desde = since.minusSeconds(30);
        return new PullResponse(medicamentos.findByUpdatedAtAfter(desde), pessoas.findBySincronizadoEmAfter(desde),
                prontuarios.findBySincronizadoEmAfter(desde), atendimentos.findBySincronizadoEmAfter(desde), servidor);
    }

    // ------------------------------------------------------------------ apoio
    private void evento(String device, Long profissional, String entidade, String entidadeId, String operacao,
                        String status, Integer versaoCliente, Integer versaoServidor, String estrategia,
                        String vencedor, ObjectNode antes, ObjectNode depois) {
        jdbc.update("""
                INSERT INTO audit.sync_evento (device_id, profissional_id, entidade, entidade_id, operacao, status,
                  versao_cliente, versao_servidor, estrategia, vencedor, antes, depois)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?::jsonb)""",
                device, profissional, entidade == null ? "?" : entidade, entidadeId,
                operacao == null ? "CREATE" : operacao, status, versaoCliente, versaoServidor, estrategia, vencedor,
                antes == null ? null : antes.toString(), depois == null ? null : depois.toString());
    }

    private void evento(String device, Long profissional, String entidade, String entidadeId, String operacao,
                        String status, Integer versaoCliente, Integer versaoServidor, String estrategia,
                        String vencedor, ObjectNode antes) {
        evento(device, profissional, entidade, entidadeId, operacao, status, versaoCliente, versaoServidor,
                estrategia, vencedor, null, antes);
    }

    private <T> T ler(ObjectNode json, Class<T> tipo) {
        try {
            return mapper.treeToValue(json, tipo);
        } catch (JsonProcessingException | IllegalArgumentException e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Payload inválido para " + tipo.getSimpleName());
        }
    }

    private static Entidade entidade(String nome) {
        try {
            return Entidade.valueOf(nome);
        } catch (Exception e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Entidade desconhecida: " + nome);
        }
    }

    private static UUID uuid(ObjectNode payload) {
        try {
            return UUID.fromString(payload.path("id").asText());
        } catch (IllegalArgumentException e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Payload sem UUID válido em \"id\"");
        }
    }

    private static String sha256(String s) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private static OffsetDateTime agora() {
        return OffsetDateTime.now(ZoneOffset.UTC);
    }
}
