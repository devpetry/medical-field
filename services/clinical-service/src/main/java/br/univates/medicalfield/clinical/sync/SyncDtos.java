package br.univates.medicalfield.clinical.sync;

import br.univates.medicalfield.clinical.domain.Atendimento;
import br.univates.medicalfield.clinical.domain.Medicamento;
import br.univates.medicalfield.clinical.domain.Pessoa;
import br.univates.medicalfield.clinical.domain.Prontuario;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.time.OffsetDateTime;
import java.util.List;

public final class SyncDtos {
    private SyncDtos() {}

    /** chave: UUID de idempotência do item; sem ela, usa deviceId:outboxId. */
    public record PushItem(Long outboxId, String chave, String entidade, String operacao, Integer baseVersion, ObjectNode payload) {}

    public record PushRequest(String deviceId, List<PushItem> itens) {}

    public record ItemResultado(Long outboxId, String status, String vencedor, Integer versao, String mensagem) {}

    public record PushResponse(List<ItemResultado> resultados, OffsetDateTime serverTime) {}

    public record PullResponse(List<Medicamento> medicamentos, List<Pessoa> pessoas, List<Prontuario> prontuarios,
                               List<Atendimento> atendimentos, OffsetDateTime serverTime) {}
}
