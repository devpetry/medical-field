package br.univates.medicalfield.clinical.sync;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.stereotype.Component;

/** Cadastros de apoio (medicamentos): prevalece sempre o dado do servidor. */
@Component
public class ServerWinsStrategy implements MergeStrategy {

    @Override
    public String nome() {
        return "ServerWins";
    }

    @Override
    public Resultado mesclar(ObjectNode servidor, ObjectNode cliente) {
        return new Resultado(servidor.deepCopy(), "SERVIDOR");
    }
}
