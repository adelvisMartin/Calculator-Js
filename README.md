# InSave — Android Recovery Heavy

InSave is an Android media utility in an active **Recovery / QA** line. The project restores and hardens historically useful behavior while keeping the heavy extraction runtime local, adding explicit regression gates, documenting security/privacy decisions and preserving reproducible build evidence.

> Current public QA target: **v0.18.2 Launcher Logo QA**.
>
> The v0.18.2 Heavy Universal candidate passed reconstruction, unit/build, security-contract, launcher-branding and package-integrity gates. Physical-device validation remains part of the path to a Stable label. A QA artifact must not be represented as production-signed merely because it builds successfully.

## What InSave currently covers

- **Inicio** — paste a supported public URL or search by song/artist, choose audio/video and download.
- **Descargas sociales** — dedicated Instagram and Facebook entry points for public post/Reel/video URLs routed through the existing maintained download flow.
- **Estados** — WhatsApp and WhatsApp Business status discovery, Images/Videos filters, search, preview and save/share behavior.
- **Descargas** — queue/history/library and local media playback.
- **Seguidores** — preserved destination from the historical shell while the product scope is evaluated.
- **Ajustes** — quality, provider/runtime, diagnostics and advanced controls.

The Heavy line intentionally prioritizes functionality and compatibility over APK size. Universal QA artifacts package the native/runtime stack needed by the downloader pipeline for the configured ABIs.

## Extraction strategy

The intended failure-isolated provider order is:

1. **Provider A — direct/NewPipe/BotGuard/PO-token-aware resolution.**
2. **Provider B — local Python + yt-dlp + QuickJS + FFmpeg.** Dynamic per-video PO-token handling is used where required. Failure in Provider A must not prevent Provider B from running.
3. **Provider C — optional self-hosted Cobalt-compatible fallback.** Disabled unless explicitly configured; InSave must not silently route user traffic through arbitrary public instances.

Playlist/Mix entries are independent jobs. One failed item must not cancel unrelated selected entries.

## Android status workflow

Automatic local discovery is the primary sideload/Recovery experience. InSave scans WhatsApp and WhatsApp Business `.Statuses` locations, refreshes when the app resumes and keeps the Storage Access Framework picker as a fallback. The recovered UX supports more than six visible statuses, scrolling, search, Images/Videos filtering and independent save/open behavior.

**Distribution note:** storage permissions and distribution policy are flavor-sensitive. See `docs/SECURITY-PRIVACY.md` and the Play-vs-sideload ADR before changing permission behavior.

## Current build identity

The current Recovery build is reconstructed over the maintained YTDLnis engine pinned at:

`deniscerri/ytdlnis@c6084ed4f110efd4ba0c3f82bb16723b6529c8f0`

InSave overlays then apply product behavior, provider hardening, security/privacy changes, tests, branding and packaging rules. The system is reproducible but still patch-driven; promoting InSave to a clean owned source tree remains a major architecture objective.

Current QA identity:

- `versionCode`: `18200`
- `versionName`: `0.18.2-Launcher-Logo-QA`
- Android application ID used by the Recovery line: `com.adelvis.insave.recovery`

## Release rule

`assemble` is **not** a release pass. A candidate is accepted only after the required source, unit, package and Android-functional gates for that release have passed.

Core P0 expectations include:

- WhatsApp + WhatsApp Business status discovery;
- status gallery scrolling beyond the first six visible cards;
- search/filter behavior in States;
- Android Back returning from an internal destination before exiting;
- public media → MP3 path without unnecessary login prompts;
- Provider B dynamic per-video PO-token path;
- independent playlist/batch jobs;
- downloaded media opening in a player;
- runtime payload and APK integrity verification;
- no sensitive cookie/token/signed-URL logging;
- exact launcher branding verification for the official InSave QA build.

## Repository layout

- `insave-build/` — InSave source overlays, reconstruction scripts, runtime policy, tests and hardening logic.
- `docs/` — architecture, QA, audit, security/privacy, threat model, roadmap and legal/distribution documentation.
- `.github/workflows/` — reproducible Android build/QA/package workflows.
- `insave-build-status*/` — historical CI/run locators and evidence from the Recovery process. Treat these as generated/audit material, not maintained product source.
- legacy root web files may remain from the historical repository slug; the maintained product work is the InSave Android line described above.

See `docs/REPOSITORY-STRUCTURE.md` for the public-repository hygiene policy.

## Public repository and licensing

This repository is public **for source visibility and collaboration**, but public does not mean “without license”.

### Software

The Android work is derived from GPL-3.0 YTDLnis. Therefore the GPL-covered software portions of InSave are distributed under **GNU GPL v3.0 only** unless a specific third-party component states another applicable license.

See:

- `LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `NOTICE`

### InSave name, logo and visual identity

The GPL grants software copyright permissions; it does **not** grant permission to present a fork or modified APK as an official InSave release.

The InSave name, launcher artwork, logo and original brand identity are governed separately by:

- `TRADEMARKS.md`
- `BRAND-ASSETS-LICENSE.md`

A redistributed modified fork should be clearly renamed/rebranded and must still preserve all GPL and third-party license obligations.

## Security and responsible disclosure

Never put real credentials, cookies, API keys, session data, signing material or private user data in issues, CI logs or test fixtures.

Security-sensitive reports must follow `SECURITY.md` rather than publishing exploit details in a public issue.

## Documentation index

Start at `docs/INDEX.md`.

Key documents include:

- `docs/ARCHITECTURE.md` — current and target architecture.
- `docs/AUDIT-2026-08-23.md` — engineering/product audit and maturity assessment.
- `docs/QA-RELEASE.md` — release gates, evidence rules and regression matrix.
- `docs/SECURITY-PRIVACY.md` — permissions, WebView, logging, signing and privacy hardening.
- `docs/THREAT-MODEL-V0180.md` — trust boundaries and threat analysis.
- `docs/SUPPLY-CHAIN-V0180.md` — dependency/runtime provenance rules.
- `docs/FODA.md` — product/engineering SWOT/FODA.
- `docs/ROADMAP-HARDENING.md` — prioritized hardening work.
- `docs/LEGAL-DISTRIBUTION.md` — licensing, trademark and APK distribution checklist.
- `docs/REPOSITORY-STRUCTURE.md` — repository hygiene and ownership boundaries.

## Contributing

Read `docs/CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `LICENSE` and `TRADEMARKS.md` before opening a substantial change.

Engineering principles:

- preserve working behavior before refactoring;
- never rename an old APK and present it as a new release;
- do not treat screenshots/string checks as substitutes for functional tests;
- isolate provider failures and bound retries;
- validate untrusted input at the boundary;
- never log secrets/cookies/tokens/signed URLs;
- keep runtime updates pinned, verifiable and reversible;
- treat upstream code as a dependency, not as the long-term InSave architecture;
- regenerate the APK, checksum and QA evidence after any source change.

## Status terminology

- **Recovery:** feature-restoration and compatibility line.
- **QA candidate:** builds and passes the defined automated gates for that candidate; still subject to physical-device validation where required.
- **Stable:** physical-device and regression matrix completed with no open P0 blocker.
- **Production-ready:** Stable plus dedicated production signing, distribution/privacy compliance, release rollback, dependency/supply-chain controls and documented support policy.

## Disclaimer

InSave is an independent project. References to YouTube, WhatsApp, Instagram, Facebook or other services describe interoperability targets only and do not imply sponsorship, endorsement or affiliation. Users are responsible for complying with applicable law, service terms and rights in the content they access or download.
