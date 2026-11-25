package br.univates.medicalfield.clinical.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.sql.Timestamp;
import java.time.Instant;

/**
 * Primeiro elo da cadeia (Chain of Responsibility): mede cada requisição e grava
 * data/hora, IP, profissional, método, rota, status e tempo em audit.access_log.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class AccessLogFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger("access");
    private final JdbcTemplate jdbc;
    private final JwtDecoder jwtDecoder;

    public AccessLogFilter(JdbcTemplate jdbc, JwtDecoder jwtDecoder) {
        this.jdbc = jdbc;
        this.jwtDecoder = jwtDecoder;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        Instant inicio = Instant.now();
        long t0 = System.nanoTime();
        try {
            chain.doFilter(req, res);
        } finally {
            long ms = (System.nanoTime() - t0) / 1_000_000;
            String ip = ipCliente(req);
            Long profissional = profissional(req);
            String device = req.getHeader("X-Device-Id");
            log.info("{} {} {} {} {}ms prof={} ip={}", req.getMethod(), req.getRequestURI(), res.getStatus(),
                    device == null ? "-" : device, ms, profissional, ip);
            try {
                jdbc.update("""
                        INSERT INTO audit.access_log
                          (data_hora, servico, ip_cliente, profissional_id, metodo, rota, status_code, tempo_ms, origem, device_id)
                        VALUES (?, 'clinical', ?, ?, ?, ?, ?, ?, 'ONLINE', ?)""",
                        Timestamp.from(inicio), ip, profissional, req.getMethod(), req.getRequestURI(),
                        res.getStatus(), ms, device);
            } catch (Exception e) {
                log.warn("falha ao gravar access_log: {}", e.getMessage());
            }
        }
    }

    static String ipCliente(HttpServletRequest req) {
        String xff = req.getHeader("X-Forwarded-For");
        if (xff != null && !xff.isBlank()) return xff.split(",")[0].trim();
        return req.getRemoteAddr();
    }

    private Long profissional(HttpServletRequest req) {
        String h = req.getHeader("Authorization");
        if (h == null || !h.startsWith("Bearer ")) return null;
        try {
            return Long.valueOf(jwtDecoder.decode(h.substring(7)).getSubject());
        } catch (Exception e) {
            return null;
        }
    }
}
