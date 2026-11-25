package br.univates.medicalfield.clinical.web;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.sql.Timestamp;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

/** Recebe os logs locais gerados offline e expõe a auditoria ao portal. */
@RestController
@RequestMapping("/log")
public class LogController {

    public record LogLocal(OffsetDateTime dataHora, String acao, String entidade, String entidadeId, Long profissionalId) {}

    public record LogRequest(String deviceId, List<LogLocal> logs) {}

    private final JdbcTemplate jdbc;

    public LogController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    Map<String, Integer> receber(@RequestBody LogRequest req, HttpServletRequest http, @AuthenticationPrincipal Jwt jwt) {
        String xff = http.getHeader("X-Forwarded-For");
        String ip = xff != null && !xff.isBlank() ? xff.split(",")[0].trim() : http.getRemoteAddr();
        List<LogLocal> logs = req.logs() == null ? List.of() : req.logs();
        for (LogLocal l : logs) {
            if (l.dataHora() == null || l.acao() == null) throw new ApiException(HttpStatus.BAD_REQUEST, "Log sem dataHora ou acao");
            String rota = l.acao() + (l.entidade() == null ? "" : " " + l.entidade() + "/" + l.entidadeId());
            jdbc.update("""
                    INSERT INTO audit.access_log (data_hora, servico, ip_cliente, profissional_id, metodo, rota, origem, device_id)
                    VALUES (?, 'cliente', ?, ?, 'LOCAL', ?, 'OFFLINE', ?)""",
                    Timestamp.from(l.dataHora().toInstant()), ip,
                    l.profissionalId() != null ? l.profissionalId() : Auth.profissional(jwt), rota, req.deviceId());
        }
        return Map.of("recebidos", logs.size());
    }

    @GetMapping
    List<Map<String, Object>> consultar(@RequestParam(defaultValue = "acesso") String tipo,
                                        @RequestParam(defaultValue = "200") int limite, @AuthenticationPrincipal Jwt jwt) {
        if (!"ADMIN".equals(jwt.getClaimAsString("perfil"))) {
            throw new ApiException(HttpStatus.FORBIDDEN, "Acesso restrito a administradores");
        }
        int n = Math.max(1, Math.min(limite, 1000));
        if ("sync".equals(tipo)) {
            return jdbc.queryForList("""
                    SELECT id, data_hora, device_id, profissional_id, entidade, entidade_id, operacao, status,
                           versao_cliente, versao_servidor, estrategia, vencedor, antes::text AS antes, depois::text AS depois
                    FROM audit.sync_evento ORDER BY data_hora DESC, id DESC LIMIT ?""", n);
        }
        return jdbc.queryForList("""
                SELECT id, data_hora, servico, ip_cliente, profissional_id, metodo, rota, status_code, tempo_ms,
                       origem, device_id
                FROM audit.access_log ORDER BY data_hora DESC, id DESC LIMIT ?""", n);
    }
}
