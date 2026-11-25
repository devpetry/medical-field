package br.univates.medicalfield.clinical.repository;

import br.univates.medicalfield.clinical.domain.Medicamento;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.OffsetDateTime;
import java.util.List;

public interface MedicamentoRepository extends JpaRepository<Medicamento, Long> {
    List<Medicamento> findAllByOrderByNome();
    List<Medicamento> findByUpdatedAtAfter(OffsetDateTime since);
}
