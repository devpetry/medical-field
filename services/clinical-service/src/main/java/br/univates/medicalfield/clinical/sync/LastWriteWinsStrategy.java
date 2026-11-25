package br.univates.medicalfield.clinical.sync;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.stereotype.Component;

import java.time.OffsetDateTime;

/** Vence o registro com o updated_at mais recente gravado pelo profissional. */
@Component
public class LastWriteWinsStrategy implements MergeStrategy {

    @Override
    public String nome() {
        return "LastWriteWins";
    }

    @Override
    public Resultado mesclar(ObjectNode servidor, ObjectNode cliente) {
        return clienteMaisRecente(servidor, cliente)
                ? new Resultado(cliente.deepCopy(), "CLIENTE")
                : new Resultado(servidor.deepCopy(), "SERVIDOR");
    }

    static boolean clienteMaisRecente(ObjectNode servidor, ObjectNode cliente) {
        OffsetDateTime s = data(servidor), c = data(cliente);
        if (c == null) return false;
        return s == null || !c.isBefore(s);
    }

    private static OffsetDateTime data(ObjectNode n) {
        var v = n.get("updatedAt");
        return v == null || v.isNull() ? null : OffsetDateTime.parse(v.asText());
    }
}
