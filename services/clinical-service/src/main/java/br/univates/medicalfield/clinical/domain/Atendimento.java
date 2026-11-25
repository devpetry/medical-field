package br.univates.medicalfield.clinical.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import org.hibernate.annotations.Fetch;
import org.hibernate.annotations.FetchMode;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "atendimento")
public class Atendimento implements Versionado {
    @Id
    public UUID id;
    public UUID prontuarioId;
    public Long profissionalId;
    public String deviceId;
    public OffsetDateTime inicio;
    public OffsetDateTime fim;
    public String local;
    public String queixaPrincipal;
    @JsonIgnore public Integer glasgowOcular;
    @JsonIgnore public Integer glasgowVerbal;
    @JsonIgnore public Integer glasgowMotora;
    @JsonIgnore public Integer glasgowTotal;
    public String triagemManchester;
    public String triagemStart;
    public String conduta;
    public String destino;
    public String status;
    public Boolean criadoOffline;
    public Integer version;
    public OffsetDateTime updatedAt;
    public OffsetDateTime sincronizadoEm;

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    @JoinColumn(name = "atendimento_id", nullable = false)
    @Fetch(FetchMode.SUBSELECT)
    @OrderBy("aferidoEm")
    public List<SinalVital> sinaisVitais = new ArrayList<>();

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    @JoinColumn(name = "atendimento_id", nullable = false)
    @Fetch(FetchMode.SUBSELECT)
    @OrderBy("administradoEm")
    public List<MedicacaoAdministrada> medicacoes = new ArrayList<>();

    public record Glasgow(Integer ocular, Integer verbal, Integer motora, Integer total) {}

    @JsonProperty("glasgow")
    public Glasgow getGlasgow() {
        return new Glasgow(glasgowOcular, glasgowVerbal, glasgowMotora, glasgowTotal);
    }

    @JsonProperty("glasgow")
    public void setGlasgow(Glasgow g) {
        if (g == null) return;
        glasgowOcular = g.ocular();
        glasgowVerbal = g.verbal();
        glasgowMotora = g.motora();
        glasgowTotal = g.total();
    }

    @Override public UUID id() { return id; }
    @Override public Integer versao() { return version; }
    @Override public void marcar(int versao, OffsetDateTime agora) { version = versao; sincronizadoEm = agora; }
}
