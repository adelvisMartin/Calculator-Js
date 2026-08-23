# InSave v0.18 — Evidence-Based 9/10 Quality Model

## Purpose
This rubric exists specifically to prevent a cosmetic score. Each domain has ten independently observable criteria. One point is awarded only when the named evidence exists and passes. Critical blockers cap the domain below 9 regardless of point count.

A **9/10 engineering score** means at least 9/10 verified criteria. It does **not** mean “perfect” and it does not automatically mean “Stable”. Stable additionally requires the exact QA artifact to pass physical-phone QA.

## Critical blockers
Any of these blocks Stable and caps the relevant domain below 9:
- build/unit/instrumentation failure;
- real public MP3 path unavailable across the bounded candidate pool;
- status discovery/scroll/search regression;
- secret/token leak;
- release still signed with debug key;
- Play flavor still contains disallowed special storage permission;
- corrupted/missing Heavy native runtime;
- destructive navigation/process termination regression;
- canonical source cannot build directly after promotion.

## Architecture — 10 criteria
1. Upstream engine pinned to immutable SHA.
2. Ordered reconstruction is deterministic.
3. Phantom Gradle modules removed.
4. InSave security/resilience code has explicit package boundary.
5. Provider A/B/C orchestration separated from UI decisions.
6. Storage/status repository separated from shell UI.
7. Materialized `canonical-source/` exists.
8. Canonical lock contains upstream/overlay/runtime provenance.
9. Canonical source builds directly without replaying patch scripts.
10. Reconstruction/canonical equivalence is checked.

Architecture cannot score 9 until criteria 7–9 pass.

## Functional Reliability — 10 criteria
1. App launches.
2. Back from subview returns Home and process remains alive.
3. Automatic WhatsApp statuses load.
4. WhatsApp Business statuses load.
5. More than six statuses remain reachable.
6. Late status is searchable.
7. Provider B primary mweb request carries dynamic per-video PO token.
8. At least one real public candidate produces MP3.
9. Two selected jobs produce two independent MP3 files.
10. Provider fallback is bounded and classified.

## QA/SDET — 10 criteria
1. Unit tests pass.
2. Android instrumented tests pass.
3. Lint task passes.
4. Static source contracts pass.
5. Security gate passes.
6. Critical-warning ratchet passes.
7. Nine-screen visual evidence exists.
8. UI XML proves status set changed after scroll.
9. Failure artifacts/logcat are retained on failure.
10. Physical-phone QA passes exact artifact.

Automated QA can reach 9/10 before physical testing; 10/10 requires physical-phone evidence.

## Security & Privacy — 10 criteria
1. Release build never references debug signing key.
2. Production signing comes only from external secrets.
3. Cleartext traffic disabled by default.
4. Exported Share boundary validates inbound URL.
5. Internal activities are not exported unnecessarily.
6. Provider C source/endpoint/response URLs are validated.
7. WebView file/content access disabled and mixed content blocked.
8. Runtime logs are redacted centrally.
9. PO/visitor token values are absent from debug logs/logcat.
10. Static secret scan passes.

## Supply Chain — 10 criteria
1. Upstream engine SHA pinned.
2. yt-dlp digest verified.
3. CI checkout action pinned by full SHA.
4. CI Java action pinned by full SHA.
5. Artifact action pinned by full SHA.
6. Emulator action pinned by full SHA.
7. Resolved Gradle graph captured.
8. CycloneDX SBOM generated.
9. Dependency update automation configured with review gates.
10. Canonical lock/provenance emitted.

## Build/Release Engineering — 10 criteria
1. Debug build succeeds.
2. Release assemble succeeds.
3. Play debug flavor succeeds.
4. Android test APK succeeds.
5. Universal APK ZIP integrity passes.
6. Four ABI payloads present.
7. Python/FFmpeg/FFprobe/aria2c/QuickJS present.
8. APK SHA-256 generated.
9. Play merged manifest removes special storage/alarm permissions.
10. Production signing gate is documented/enforced without committing private keys.

## Maintainability — 10 criteria
1. Critical Gradle structural warnings are zero.
2. Abandoned Accompanist WebView removed.
3. Room query mismatch is explicit/intentional.
4. Input policy is unit-tested centrally.
5. Redaction is unit-tested centrally.
6. Provider failure classification is unit-tested centrally.
7. Warning counts are measured.
8. Low-risk deprecation debt has a ratchet instead of suppression-by-default.
9. Canonical source is directly editable/buildable.
10. Contributor/ADR/quality documentation names ownership and DoD.

## Scalability — 10 criteria
1. Status repository does not cap at six/180 arbitrary items.
2. RecyclerView virtualizes status rendering.
3. Search is debounced.
4. Playlist batch limit is explicit (50 per InSave batch).
5. Each selected item is independent.
6. Provider failure of one item does not cancel unrelated jobs.
7. Provider strategy is extensible by bounded client/provider entry.
8. Heavy runtime can later move to ABI/App Bundle delivery without changing feature contracts.
9. Canonical source separates product ownership from upstream patch replay.
10. Large-set/queue performance evidence exists.

## Observability — 10 criteria
1. Provider path is identified.
2. Failure class is identified.
3. Fallback client is identified without secrets.
4. FFmpeg/yt-dlp errors remain available after redaction.
5. Logcat is retained on failure.
6. Build log retained.
7. Screenshot/UI XML retained.
8. Cold-start metric retained.
9. Artifact/provenance manifest retained.
10. No secret-like PO material appears in evidence.

## UX/Accessibility — 10 criteria
1. Five InSave destinations remain accessible.
2. Home supports song/artist text and URL input.
3. MP3 is a primary flow.
4. Status gallery opens without file picker in sideload Recovery.
5. Status search is visible.
6. Status scroll exposes later content.
7. Business status source is reachable.
8. Downloaded media can be opened.
9. Back navigation is internal/predictable.
10. Physical-phone accessibility/responsive review passes.

## Performance/Compatibility — 10 criteria
1. API 35 emulator boots with KVM acceleration.
2. Universal APK includes ARM64.
3. Universal APK includes ARMv7.
4. Universal APK includes x86.
5. Universal APK includes x86_64.
6. App cold-start TotalTime is measured and remains below pathological 10s emulator threshold.
7. Status list scroll changes visible item set.
8. Two independent media conversions complete without process death.
9. Legacy Android compatibility job passes.
10. Physical Xiaomi/MIUI QA passes.

## Release labels
- **Development**: any critical blocker remains.
- **QA Candidate**: automated critical gates pass and every core domain is >=9/10 where physical-device evidence is not the only missing criterion.
- **Stable Candidate**: automated gates + canonical direct build pass; awaiting physical phone.
- **Stable**: exact artifact also passes physical-phone checklist.

The scoring script must link every point to an evidence file or a repository fact. Missing evidence scores zero; it is never inferred from intent or documentation.
