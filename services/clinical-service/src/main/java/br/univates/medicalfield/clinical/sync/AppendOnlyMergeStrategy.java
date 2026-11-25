package br.univates.medicalfield.clinical.sync;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Atendimento: campos simples seguem LastWriteWins; as listas de sinais vitais e
 * medicações são unidas pelo id, sem apagar nenhum item.
 */
@Component
public class AppendOnlyMergeStrategy implements MergeStrategy {

    private static final Map<String, String> LISTAS = Map.of(
            "sinaisVitais", "aferidoEm",
            "medicacoes", "administradoEm");

    @Override
    public String nome() {
        return "AppendOnlyMerge";
    }

    @Override
    public Resultado mesclar(ObjectNode servidor, ObjectNode cliente) {
        boolean clienteVence = LastWriteWinsStrategy.clienteMaisRecente(servidor, cliente);
        ObjectNode vencedor = clienteVence ? cliente : servidor;
        ObjectNode perdedor = clienteVence ? servidor : cliente;
        ObjectNode resultado = vencedor.deepCopy();
        LISTAS.forEach((campo, ordem) -> resultado.set(campo, unir(perdedor.get(campo), vencedor.get(campo), ordem)));
        return new Resultado(resultado, "MESCLA");
    }

    private static ArrayNode unir(JsonNode perdedor, JsonNode vencedor, String ordem) {
        Map<String, JsonNode> porId = new LinkedHashMap<>();
        for (JsonNode lista : new JsonNode[]{perdedor, vencedor}) {
            if (lista != null && lista.isArray()) lista.forEach(i -> porId.put(i.path("id").asText(), i));
        }
        var itens = new ArrayList<>(porId.values());
        itens.sort(Comparator.comparing(i -> i.path(ordem).asText()));
        var out = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        itens.forEach(out::add);
        return out;
    }
}
