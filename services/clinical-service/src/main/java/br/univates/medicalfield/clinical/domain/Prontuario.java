package br.univates.medicalfield.clinical.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "prontuario")
public class Prontuario implements Versionado {
    @Id
    public UUID id;
    public UUID pessoaId;
    public String comorbidades;
    public String usoContinuo;
    public String observacoes;
    public Integer version;
    public OffsetDateTime updatedAt;
    public Long updatedBy;
    public OffsetDateTime sincronizadoEm;

    @Override public UUID id() { return id; }
    @Override public Integer versao() { return version; }
    @Override public void marcar(int versao, OffsetDateTime agora) { version = versao; sincronizadoEm = agora; }
}
