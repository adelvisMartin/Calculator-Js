# InSave Hardening Roadmap

This roadmap deliberately prioritizes reliability and ownership before feature expansion.

## P0 — block Stable/Production

### P0.1 v0.17.2 candidate validation

- Produce the COMPLETE Universal v0.17.2 APK from the exact recovery commit.
- Verify four ABI payloads and native runtime inventory.
- Run Android functional P0 against that source/candidate line.
- Prove >6 Status items using the 14-item fixture and a real scroll gesture.
- Prove status search, WhatsApp Business and app-level Back behavior.
- Confirm plain song/artist search reaches the maintained search engine.
- Reconfirm Provider B dynamic per-video PO-token -> MP3.
- Reconfirm two distinct selected videos -> independent MP3 jobs.
- Physical-phone QA using exact SHA-256.

### P0.2 Production signing

- Create dedicated upload/release key.
- Remove release dependency on debug signing.
- Store secrets in CI secret management.
- Document fingerprint, backup and recovery.
- If Play distribution is selected, enroll in Play App Signing.

### P0.3 Distribution/privacy decision

- Define `recoverySideload`, `productionSideload` and `play` capability profiles.
- Decide whether Play build can implement States without `MANAGE_EXTERNAL_STORAGE`.
- Document permission rationale and denial behavior.
- No Production claim until channel policy is resolved.

### P0.4 Data-loss safety

- Verify failed updates/retries never delete user downloads/history.
- Atomic temp -> final media transition.
- Database migrations tested across supported prior versions.
- Runtime update rollback preserved.

## P1 — architecture and security

### P1.1 Materialize an owned InSave source tree

Goal: stop growing the patch-script architecture.

- Create dedicated InSave Android repository/fork from current known-good engine commit.
- Apply Recovery transformations as normal commits.
- Preserve current reconstruction branch as disaster-recovery reference.
- Add CODEOWNERS and branch protection.
- Require PR review and CI.

### P1.2 Provider abstraction

- Introduce `MediaProvider`, `ProviderRouter`, typed provider failures.
- Move NewPipe, yt-dlp and Cobalt into isolated provider implementations.
- Centralize retry/backoff/circuit-breaker policy.
- Add provider contract tests.
- Make public-video fixtures configurable and easy to replace.

### P1.3 Status repository abstraction

- Move filesystem paths out of Activity/UI code.
- Add Direct/SAF/MediaStore data-source implementations.
- Cache scan results.
- Filter/search cached list rather than rescanning on every keystroke.
- Add 10/100/1000 item performance tests.

### P1.4 Download source of truth

- Persist immutable download jobs in Room.
- WorkManager unique work per job UUID.
- Idempotent resume/cancel/retry.
- Explicit job state machine.
- Separate aggregate playlist state from per-item execution.

### P1.5 Security hardening

- Exported component audit.
- Intent validation/fuzzing.
- Runtime update SHA-256 + signed manifest + rollback.
- URL scheme/host validation.
- Redaction tests for cookies/tokens/signed URLs.
- Archive/path traversal tests.
- TLS-only remote provider endpoints.

### P1.6 Supply chain

- Gradle version catalog.
- Dependabot/Renovate.
- GitHub dependency review.
- OSV/CVE scanner.
- CycloneDX/SPDX SBOM per candidate.
- Third-party license NOTICE.
- Align youtubedl runtime package versions where compatible.
- Replace deprecated Accompanist WebView path.

### P1.7 Gradle/toolchain debt

- Remove deprecated Groovy assignment syntax.
- Remove `archivesBaseName`/BasePluginConvention dependency.
- Resolve/declare missing `common`, `library`, `ffmpeg` project directories correctly.
- Treat new compiler warnings as CI failures.
- Burn down existing Kotlin/Android deprecation warnings module by module.

## P2 — product quality

### P2.1 UI architecture

- ViewModel + StateFlow/UDF for InSave features.
- Shared design tokens and reusable components.
- Standard loading/empty/error states.
- Preserve dark/magenta identity.
- Advanced extractor options remain outside the normal flow.

### P2.2 Accessibility

- TalkBack/content descriptions.
- 48dp minimum interactive targets.
- Dynamic font-size testing.
- Contrast audit.
- Keyboard/focus handling where applicable.
- Avoid using color alone to communicate status.

### P2.3 Adaptive/responsive UX

- Small phones and Xiaomi display cutouts.
- Landscape.
- Tablet/foldable layouts if usage justifies them.
- Edge-to-edge modern APIs replacing deprecated system UI flags.

### P2.4 Performance

- Startup baseline profile/macrobenchmark.
- Status gallery jank/memory benchmark.
- Thumbnail cache policy.
- WorkManager CPU/battery measurement.
- Avoid loading full media payloads into memory.
- Benchmark Universal only for QA; production uses optimized delivery.

### P2.5 Observability

Create a local Diagnostics bundle containing only redacted data:

- InSave version/hash;
- Android/device model;
- provider/runtime versions;
- typed failure timeline;
- permission/capability state;
- FFmpeg exit category;
- worker status;
- optional sanitized log excerpt.

No telemetry server is required to obtain this benefit.

## P3 — distribution and growth

### P3.1 AAB/optimized packages

- AAB for Play.
- ABI-specific sideload releases.
- Keep COMPLETE Universal as QA/recovery artifact.
- Publish checksums and signing fingerprints.

### P3.2 Update strategy

Separate three update channels:

1. Android application update.
2. Extractor/runtime update.
3. Provider configuration/fixture update.

Each needs its own version, integrity gate and rollback policy.

### P3.3 Feature growth rule

A new platform/provider is accepted only when it implements the provider contract, has fixtures/tests, documents limitations and does not require weakening global security/privacy behavior.

## Suggested milestones

### M1 — Recovery v0.17.2 QA

Exit criteria: complete APK + automated P0 + physical-phone QA.

### M2 — InSave 0.18 Architecture Foundation

Exit criteria: owned source repo, production signing, provider interfaces, status repository abstraction, clean CI.

### M3 — InSave 0.19 Production Candidate

Exit criteria: distribution flavor, SBOM/security gates, device matrix, AAB/optimized delivery, migration tests.

### M4 — InSave 1.0

Exit criteria: no Recovery scripts required for normal builds, documented support/update lifecycle, stable product architecture, reproducible signed release and rollback.

## Definition of done for hardening tickets

A ticket is not done when code is merely present. It is done when:

- behavior has an automated test or explicitly justified physical-only test;
- relevant docs/changelog updated;
- no secret/sensitive data introduced;
- rollback/migration behavior considered;
- source is formatted/linted;
- no unrelated feature regression;
- release evidence can identify the exact commit and artifact hash.
