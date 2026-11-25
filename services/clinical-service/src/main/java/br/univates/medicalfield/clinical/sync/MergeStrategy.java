package br.univates.medicalfield.clinical.sync;

import com.fasterxml.jackson.databind.node.ObjectNode;

/** Strategy: algoritmo de resolução de conflito entre a versão do servidor e a do cliente. */
public interface MergeStrategy {

    record Resultado(ObjectNode registro, String vencedor) {}

    String nome();

    Resultado mesclar(ObjectNode servidor, ObjectNode cliente);
}
