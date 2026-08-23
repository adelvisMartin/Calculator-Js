# InSave v0.18 — Engineering Skill Playbooks

The project treats a “skill” as a reusable engineering procedure with inputs, outputs and gates. Skills do not modify the runtime merely by being documented.

## Recovery-to-Canonical Skill
1. Reconstruct from pinned YTDLnis + ordered InSave overlays.
2. Run source/security/build/runtime gates.
3. Materialize the generated Android tree as `canonical-source/` only after green automation.
4. Store upstream SHA, overlay SHA, yt-dlp digest and tree digest in a lock file.
5. Build the materialized tree directly and compare behavior/artifact structure against reconstruction.
6. Future product changes target canonical source; reconstruction remains a reproducibility/rollback recipe.

## YouTube Resilience Skill
1. Keep the public path anonymous-first.
2. Generate fresh per-video PO token for Provider B primary `mweb` request.
3. Classify failure before retry.
4. Only bot/403/no-format/transient-network classes can enter the anonymous fallback ladder.
5. Try bounded explicit clients (`web_embedded`, `android_vr`) without reusing an incompatible mweb PO token.
6. Provider C is last, optional and explicitly self-hosted/configured.
7. Private, members-only, age/auth-required, removed or copyrighted-unavailable content is surfaced honestly instead of routed through bypass logic.
8. Candidate-pool E2E prevents one temporarily challenged public video from creating a false product-wide regression while still requiring real MP3 output.

## Android Status Storage Skill
1. Sideload/Recovery: automatic local WhatsApp + Business discovery is primary.
2. QA creates at least fourteen WhatsApp fixtures plus one Business fixture.
3. Test repository count, visual initial set, changed set after scroll and late-item search.
4. Play flavor removes All Files Access and other nonessential special permissions in its merged manifest.
5. SAF/MediaStore becomes the policy-compliant fallback/product flow for Play distribution.
6. Physical Xiaomi/MIUI behavior remains a mandatory Stable gate.

## Secure Input Boundary Skill
1. Treat exported Intents, paste/search text and configured provider endpoints as untrusted.
2. Normalize only HTTP/HTTPS downloader URLs.
3. Reject file/content/javascript/custom schemes, embedded credentials, control characters and obvious loopback/private literal targets.
4. Bound URL and search lengths.
5. Validate Provider C source, endpoint and returned tunnel/redirect URL separately.
6. Unit-test the boundary independently of UI.

## Secret-Safe Observability Skill
1. Centralize runtime redaction.
2. Redact cookies, Authorization/Bearer, PO tokens, visitor data, API/access/refresh tokens and signed URL parameters.
3. Keep provider name, failure class, HTTP category, retry decision and non-secret diagnostic lines.
4. Scan logcat in Android E2E for token-like leaks.
5. Never log full incoming Intents.

## Native WebView Hardening Skill
1. Prefer platform WebView over abandoned wrapper dependencies.
2. Safe Browsing on where supported.
3. Mixed content never.
4. File/content access disabled unless specifically required.
5. Validate redirects/navigation URLs.
6. Destroy/pause WebView explicitly when the token helper finishes.

## Release Signing Skill
1. Debug key may sign debug QA only.
2. Release block must never reference `signingConfigs.debug`.
3. Production keystore path/password/alias/key password arrive through CI secrets/environment only.
4. Never commit keystore or passwords.
5. Production artifact is blocked when production signing credentials are absent.
6. QA artifact may remain debug-signed/unsigned and must be labelled QA, not production.

## Dependency/Supply-Chain Skill
1. Pin upstream source commit.
2. Pin GitHub Actions by full commit SHA for release/quality workflows.
3. Verify embedded yt-dlp SHA-256.
4. Emit resolved Gradle dependency graph and CycloneDX SBOM.
5. Use automated dependency update tooling only with gates; never mass-upgrade dependencies without regression proof.
6. Record rollback version for every runtime upgrade.

## Warning Ratchet Skill
1. Structural warnings are blockers: missing Gradle modules, abandoned WebView dependency, Room query mismatch without explicit intent, removed Gradle APIs, build failure.
2. Remaining low-risk upstream Android/Kotlin deprecations are counted, not hidden.
3. New code cannot increase the warning baseline without review.
4. Incrementally replace deprecated Android APIs behind characterization tests.

## Heavy APK Packaging Skill
1. Functionality takes priority over size during Recovery.
2. Universal QA APK must contain all configured ABIs.
3. Verify Python, FFmpeg, FFprobe, aria2c and QuickJS native payloads.
4. ZIP integrity + SHA-256 are mandatory.
5. Production distribution should prefer App Bundle/ABI delivery once functionality and policy gates are stable.

## Evidence-Driven 9/10 Skill
Each quality domain has ten observable criteria. A domain is >=9 only when at least nine criteria have evidence and no critical blocker exists. “9/10” written in documentation is never evidence. Stable status additionally requires the exact automated candidate to pass physical-phone QA.
