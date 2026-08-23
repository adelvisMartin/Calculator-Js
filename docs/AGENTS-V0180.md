# InSave v0.18 — Senior Review Agents

These agents are engineering review roles and evidence owners. They are not runtime bots and no score is granted because a role exists. A role only contributes when its gate produces reproducible evidence.

## 1. Android Architecture Agent
Owns package/module boundaries, dependency direction, lifecycle/state management, storage abstractions, upstream isolation and the migration from patch-only Recovery to materialized InSave source. Blocks circular feature dependencies and direct extractor calls from UI code.

Evidence: architecture map, canonical-source lock, direct canonical build, dependency boundaries, reproducible reconstruction comparison.

## 2. Extraction Resilience Agent
Owns Provider A/B/C strategy and YouTube churn. Provider B is a bounded strategy ladder: primary local `mweb` with fresh per-video PO tokens, then explicit anonymous fallback clients only for recoverable challenge/network/format failures, then optional self-hosted Provider C. Authentication/private-content errors never trigger silent bypass behavior.

Evidence: request-contract tests, real public MP3 conversion, independent batch jobs, classified failure logs, no cookies required for the anonymous public path.

## 3. Android Storage/OEM Agent
Owns `.Statuses` discovery, Android 7–16 storage behavior, WhatsApp and WhatsApp Business paths, MediaStore/SAF fallback, Xiaomi/MIUI behavior, notification/background limits and physical-phone regressions.

Evidence: 14+ status fixture test, visual scroll/search proof, Play merged-manifest permission gate, physical-device QA checklist.

## 4. Security & Privacy Agent
Owns exported-component boundaries, Intent/URL validation, SSRF protections, WebView policy, logging redaction, cleartext policy, secrets, signing and user-data minimization.

Evidence: static security gate, unit tests for input policy/redaction, logcat secret scan, merged manifests, release-signing configuration review.

## 5. Supply-Chain Agent
Owns pinned CI actions, upstream commit locks, yt-dlp/runtime hashes, dependency inventory, SBOM, update cadence and rollback metadata. It rejects floating CI actions for release gates.

Evidence: exact action SHAs, CycloneDX SBOM, upstream lock, yt-dlp SHA-256, dependency graph and release provenance.

## 6. Backend/Provider Agent
Owns network timeouts, retry/fallback semantics, Provider C endpoint policy, response validation, error taxonomy, cancellation propagation and idempotent per-item jobs.

Evidence: failure-classifier unit tests, endpoint validation tests, independent playlist job results, bounded retries and provider-order logs.

## 7. Frontend/UX Agent
Owns five-destination InSave shell, search/paste entry, audio-first workflow, status gallery, states, empty/loading/error feedback, navigation/back behavior, accessibility and responsive phone layouts.

Evidence: nine-screen screenshot set, UI XML assertions, search of a late status fixture, process-alive Back gate and manual physical QA.

## 8. Media Runtime Agent
Owns Python, yt-dlp, FFmpeg/FFprobe, aria2c and QuickJS packaging; conversion correctness; MP3 presets; loudness normalization; ABI compatibility and runtime update rollback.

Evidence: four-ABI APK inspection, native library inventory, yt-dlp hash, real MP3 header/size checks and two independent output files.

## 9. QA/SDET Agent
Owns unit, lint, source contracts, instrumented Android tests, visual automation, failure evidence, flaky-test analysis, test-video candidate pools and gate reproducibility.

Evidence: GitHub Actions logs, screenshots, Android test reports, warning ratchet and failure artifacts.

## 10. Release Engineering Agent
Owns version identity, signing separation, QA vs production artifacts, Play vs sideload flavors, checksums, artifact provenance and release blocking rules.

Evidence: APK SHA-256, signing contract, flavor manifests, build logs and release manifest.

## 11. Performance/Reliability Agent
Owns startup, download queue independence, memory/process survival, cancellation, timeout behavior and large status/playlist data sets.

Evidence: cold-start measurement, process-alive navigation evidence, independent job tests and future macrobenchmarks.

## 12. Documentation/Knowledge Agent
Owns architecture decisions, threat model, quality rubric, release history, rollback procedure, known limitations and evidence links. Documentation cannot say `PASS` until the corresponding automation or physical QA has passed.

## Cross-agent release rule
A v0.18 artifact may be called **QA Candidate** only after automated gates pass. It may be called **Stable** only after the same artifact passes physical-phone QA. A numerical score never overrides a critical blocker, signing failure, secret exposure, broken extraction, broken status discovery or broken navigation.
