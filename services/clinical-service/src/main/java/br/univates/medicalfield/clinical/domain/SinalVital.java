package br.univates.medicalfield.clinical.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "sinal_vital")
public class SinalVital {
    @Id
    public UUID id;
    public OffsetDateTime aferidoEm;
    public Integer paSistolica;
    public Integer paDiastolica;
    public Integer fc;
    public Integer fr;
    public Integer spo2;
    public BigDecimal temperatura;
    public Integer glicemia;
}
