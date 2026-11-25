package br.univates.medicalfield.clinical.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

/** Entidade sincronizável: UUID gerado no dispositivo + versão controlada pelo servidor. */
public interface Versionado {
    UUID id();
    Integer versao();
    void marcar(int versao, OffsetDateTime agora);
}
