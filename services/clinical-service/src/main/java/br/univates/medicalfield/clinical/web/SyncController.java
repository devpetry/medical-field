package br.univates.medicalfield.clinical.web;

import br.univates.medicalfield.clinical.sync.SyncDtos.PullResponse;
import br.univates.medicalfield.clinical.sync.SyncDtos.PushRequest;
import br.univates.medicalfield.clinical.sync.SyncDtos.PushResponse;
import br.univates.medicalfield.clinical.sync.SyncService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.time.OffsetDateTime;

@RestController
@RequestMapping("/sync")
public class SyncController {

    private final SyncService sync;

    public SyncController(SyncService sync) {
        this.sync = sync;
    }

    @GetMapping("/pull")
    PullResponse pull(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) OffsetDateTime since) {
        return sync.pull(since);
    }

    @PostMapping("/push")
    PushResponse push(@RequestBody PushRequest req, @AuthenticationPrincipal Jwt jwt) {
        return sync.push(req, Auth.profissional(jwt));
    }
}
