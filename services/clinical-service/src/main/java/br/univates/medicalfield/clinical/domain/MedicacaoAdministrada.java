package br.univates.medicalfield.clinical.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "medicacao_administrada")
public class MedicacaoAdministrada {
    @Id
    public UUID id;
    public Long medicamentoId;
    public BigDecimal dose;
    public String unidade;
    public String via;
    public OffsetDateTime administradoEm;
    public Long profissionalId;
    public Boolean alertaConfirmado;
}
