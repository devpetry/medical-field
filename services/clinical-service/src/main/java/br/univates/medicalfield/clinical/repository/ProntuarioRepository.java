package br.univates.medicalfield.clinical.repository;

import br.univates.medicalfield.clinical.domain.Prontuario;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ProntuarioRepository extends JpaRepository<Prontuario, UUID> {
    Optional<Prontuario> findByPessoaId(UUID pessoaId);
    List<Prontuario> findAllByOrderByUpdatedAtDesc();
    List<Prontuario> findBySincronizadoEmAfter(OffsetDateTime since);
}
