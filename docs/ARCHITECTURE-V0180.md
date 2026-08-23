# InSave v0.18 Architecture

## Architectural objective
v0.18 converts the Recovery line from a collection of successful patches into an owned, testable Android product without throwing away the proven YTDLnis runtime. The migration is evolutionary: first make reconstruction deterministic and green, then materialize that generated tree as InSave canonical source, then refactor behind characterization tests.

## Current runtime layers

### Product shell
`InSaveHubActivity` owns the five top-level destinations and user-level flows: Inicio, Estados, Descargas, Seguidores and Ajustes. It is an internal Activity; the launcher alias may target it, but arbitrary third-party applications cannot launch it directly.

### External boundary
`ShareActivity` remains the explicit exported SEND/VIEW entry point. It validates and normalizes shared HTTP/HTTPS URLs through `InSaveInputPolicy` before any extractor sees the value. Full incoming Intents are not logged.

### Status data layer
`AutomaticStatusRepository` owns local WhatsApp and WhatsApp Business `.Statuses` discovery. Sideload/Recovery can use All Files Access for the automatic gallery. Play uses a dedicated manifest overlay that removes this permission and other nonessential special-access permissions.

### Extraction layer
Provider ordering is intentionally explicit:

1. **Provider A** — NewPipe direct resolution where supported.
2. **Provider B1** — local yt-dlp using current `mweb` client + fresh per-video PO token material.
3. **Provider B2** — bounded `web_embedded` retry only for classified recoverable failures.
4. **Provider B3** — bounded `android_vr` retry only for classified recoverable failures.
5. **Provider C** — optional explicitly configured self-hosted Cobalt-compatible endpoint.

The fallback classifier prevents authentication/private-content/cancelled failures from being silently treated as bot/network failures.

### Media runtime layer
Python, yt-dlp, FFmpeg, FFprobe, aria2c and QuickJS are release payloads for the Heavy Recovery line. They are verified structurally in the universal APK and functionally through real MP3 conversion tests.

### Security/observability layer
- `InSaveInputPolicy`: URL/search/provider boundary.
- `InSaveProviderFailureClassifier`: deterministic error taxonomy.
- `InSaveRedactor`: secret-safe diagnostics.
- native WebView manual token helper: mixed-content blocked, file/content access disabled.

## Build flavors

### `github`
Heavy sideload/Recovery QA. Retains the special storage capability required for automatic `.Statuses` discovery on current Android storage layouts. This artifact is not claimed Play-policy compatible.

### `play`
Policy-oriented build. Its source manifest removes `MANAGE_EXTERNAL_STORAGE`, battery-optimization special request and exact alarm permission. CI must inspect the **merged** Play manifest; checking only source XML is insufficient.

### `foss`
Maintained upstream flavor preserved during Recovery compatibility. Product decisions for its future InSave role require a separate ADR.

## Signing architecture
Debug QA and production signing are separated. Release code no longer references `signingConfigs.debug`. Production credentials are read only from `INSAVE_KEYSTORE_PATH`, `INSAVE_KEYSTORE_PASSWORD`, `INSAVE_KEY_ALIAS` and `INSAVE_KEY_PASSWORD`. Their absence blocks a claim of production-signed readiness; no private key is invented or committed for QA.

## Canonical-source migration
Patch replay is retained as a reproducibility mechanism but must stop being the only editable source of truth.

Promotion sequence:
1. reconstruct pinned upstream + overlays;
2. pass unit/lint/security/Android E2E;
3. remove `.git`, build outputs and caches from generated tree;
4. materialize as `canonical-source/`;
5. write `UPSTREAM_LOCK.json` with exact upstream SHA, overlay SHA, yt-dlp hash and tree hash;
6. build `canonical-source/` directly;
7. verify direct-build runtime/manifest/APK contracts;
8. future InSave feature changes target canonical source while the Recovery recipe remains a reproducible reference/rollback path.

Until steps 4–7 are green, the Architecture domain is intentionally capped below 9/10 by the quality model.

## Refactoring direction after canonical promotion
The first safe modularization boundary is not a rewrite. It is a sequence of extraction moves behind existing tests:

- `core-security` — input policy, redaction, endpoint policy;
- `core-runtime` — RuntimeManager adapters and packaged binary contracts;
- `data-status` — automatic status discovery/storage abstraction;
- `data-download` — queue/history/repositories;
- `provider-youtube-newpipe`;
- `provider-youtube-ytdlp`;
- `provider-cobalt`;
- `feature-home`;
- `feature-statuses`;
- `feature-downloads`;
- `feature-settings`;
- `app` composition root.

Module creation is deferred until canonical-source direct build is proven; otherwise structural refactoring would multiply variables during Recovery.

## Dependency rule
UI may depend on domain/data/provider interfaces, but provider/runtime code must never depend on screen widgets or Activity state. Provider routing must be testable without rendering UI. Status repository must be testable without launching the shell.

## Versioning rule
`0.18.0-Hardening-QA` is an engineering QA line. A successful assemble does not make it Stable. Automated gates create a QA Candidate; direct canonical build plus exact physical-phone QA create the Stable decision.
