package br.univates.medicalfield.clinical.domain;

import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "pessoa")
public class Pessoa implements Versionado {
    @Id
    public UUID id;
    public String nome;
    public String cpf;
    public LocalDate dataNascimento;
    public String sexo;
    public String tipoSanguineo;
    public String alergias;
    public String telefone;
    public String emailContato;
    public String contatoEmergencia;
    public Integer version;
    public OffsetDateTime updatedAt;
    public Long updatedBy;
    public OffsetDateTime sincronizadoEm;

    @Override public UUID id() { return id; }
    @Override public Integer versao() { return version; }
    @Override public void marcar(int versao, OffsetDateTime agora) { version = versao; sincronizadoEm = agora; }
}
