package br.univates.medicalfield.clinical.web;

import org.springframework.security.oauth2.jwt.Jwt;

final class Auth {
    private Auth() {}

    static Long profissional(Jwt jwt) {
        return Long.valueOf(jwt.getSubject());
    }
}
