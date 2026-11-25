package br.univates.medicalfield.clinical.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;

/** Cadastro de apoio; inserido manualmente no banco e somente lido pela API. */
@Entity
@Table(name = "medicamento")
public class Medicamento {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public String nome;
    public String principioAtivo;
    public String apresentacao;
    public BigDecimal doseMaxima;
    public String unidade;
    public String viaPadrao;
    public String alertas;
    @Column(insertable = false, updatable = false)
    public OffsetDateTime updatedAt;
}
