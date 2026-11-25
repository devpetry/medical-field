package br.univates.medicalfield.clinical.repository;

import br.univates.medicalfield.clinical.domain.Atendimento;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

public interface AtendimentoRepository extends JpaRepository<Atendimento, UUID> {
    List<Atendimento> findAllByOrderByInicioDesc();
    List<Atendimento> findByProntuarioIdOrderByInicioDesc(UUID prontuarioId);
    List<Atendimento> findBySincronizadoEmAfter(OffsetDateTime since);
}
