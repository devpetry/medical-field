package br.univates.medicalfield.clinical.repository;

import br.univates.medicalfield.clinical.domain.Pessoa;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

public interface PessoaRepository extends JpaRepository<Pessoa, UUID> {
    List<Pessoa> findAllByOrderByNome();
    List<Pessoa> findBySincronizadoEmAfter(OffsetDateTime since);
}
