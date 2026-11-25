package br.univates.medicalfield.clinical.sync;

import org.springframework.stereotype.Component;

/** Escolhe a estratégia de merge de cada entidade. */
@Component
public class MergeStrategyFactory {

    private final LastWriteWinsStrategy lastWriteWins;
    private final AppendOnlyMergeStrategy appendOnly;
    private final ServerWinsStrategy serverWins;

    public MergeStrategyFactory(LastWriteWinsStrategy lastWriteWins, AppendOnlyMergeStrategy appendOnly,
                                ServerWinsStrategy serverWins) {
        this.lastWriteWins = lastWriteWins;
        this.appendOnly = appendOnly;
        this.serverWins = serverWins;
    }

    public MergeStrategy para(Entidade entidade) {
        return switch (entidade) {
            case PESSOA, PRONTUARIO -> lastWriteWins;
            case ATENDIMENTO -> appendOnly;
            case MEDICAMENTO -> serverWins;
        };
    }
}
