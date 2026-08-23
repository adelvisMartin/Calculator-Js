# InSave — Recovery Heavy

InSave is an Android media utility currently in the **Recovery Heavy** line. The recovery branch exists to restore historically useful behavior while keeping a fully local extraction runtime and adding explicit regression gates before the project is called stable.

> Current recovery target: **v0.17.2 Recovery UX**. This branch is appropriate for QA/dogfood and sideload testing. It must not be described as Production/Stable until the physical-device release gate is complete.

## Product scope

InSave combines five primary destinations:

- **Inicio** — paste a URL or search by song/artist, then choose audio/video and download.
- **Estados** — automatic WhatsApp and WhatsApp Business status discovery, Images/Videos filters, search, preview and save/share flows.
- **Descargas** — queue/history/library and local media playback.
- **Seguidores** — preserved product destination from the historical shell.
- **Ajustes** — quality, provider/runtime, diagnostics and advanced controls.

The Recovery line intentionally prioritizes functionality over APK size. The COMPLETE Universal QA artifact embeds native/runtime components required by the downloader stack and supports the configured ABIs.

## Extraction resilience

The intended provider order is:

1. **Provider A — NewPipe/BotGuard/PO-token-aware direct resolution.**
2. **Provider B — local Python + yt-dlp + QuickJS + FFmpeg.** PO tokens are generated per video where required; a failure in Provider A must not abort Provider B.
3. **Provider C — optional self-hosted Cobalt-compatible fallback.** It is disabled unless explicitly configured and must never silently route traffic through arbitrary public instances.

Playlist/Mix entries are independent jobs. One failed item must not cancel unrelated selected entries.

## Android status workflow

Automatic local discovery is the primary sideload/Recovery experience. InSave scans WhatsApp and WhatsApp Business `.Statuses` locations under shared storage, refreshes on return to the app, and keeps the Storage Access Framework picker as a fallback. The v0.17.2 UX removes arbitrary visible-item caps, adds a status search field and uses a scrollable RecyclerView.

**Distribution note:** the Recovery implementation uses broad storage access for the automatic direct-path behavior. That is a Play-policy-sensitive capability and requires a separate distribution decision; see `docs/SECURITY-PRIVACY.md`.

## Build identity

The Recovery build is reconstructed over the maintained YTDLnis engine pinned by the build pipeline, then receives InSave-specific patches and branding. The current process is reproducible but patch-driven; migrating InSave to an owned, clean multi-module source tree is a major architecture objective.

## Release rule

`assemble` is not a functional release pass. A candidate is accepted only after the required source/unit/package gates and Android functional gates have passed. The core P0 Android contract includes:

- automatic WhatsApp/Business status discovery;
- status gallery scrolling beyond the first six visible cards;
- search/filter behavior in States;
- Android Back returning from a subview to Inicio before exiting;
- real public YouTube → MP3 without login;
- Provider B dynamic per-video PO-token path;
- at least two distinct playlist entries producing independent MP3 jobs;
- downloadable media opening in a player;
- runtime payload and APK integrity verification.

Physical-phone confirmation is still required before labeling a build Stable.

## Documentation

- `docs/AUDIT-2026-08-23.md` — engineering/product audit and maturity score.
- `docs/ARCHITECTURE.md` — current architecture and target scalable architecture.
- `docs/QA-RELEASE.md` — release gates, test matrix and evidence rules.
- `docs/SECURITY-PRIVACY.md` — permissions, signing, network/runtime and supply-chain hardening.
- `docs/FODA.md` — deep SWOT/FODA and strategy matrix.
- `docs/ROADMAP-HARDENING.md` — prioritized P0/P1/P2 hardening roadmap.
- `docs/RELEASE-0.17.2.md` — v0.17.2 Recovery UX scope and QA checklist.

## Engineering principles

- Preserve working behavior before refactoring.
- Never rename an old APK and present it as a new version.
- Never treat string checks or screenshots as substitutes for functional tests.
- Keep provider failures isolated and typed.
- Do not leak cookies, API keys, signed media URLs or sensitive user paths into logs.
- Prefer privacy-friendly Android APIs where they can satisfy the product requirement.
- Keep runtime updates pinned, verifiable and reversible.
- Treat external upstream code as a dependency, not as the long-term InSave architecture.

## Status terminology

- **Recovery:** feature restoration and compatibility line.
- **QA candidate:** builds, installs and passes defined automated gates; awaits/undergoes physical-device validation.
- **Stable:** physical-device and regression matrix completed with no open P0 blocker.
- **Production-ready:** Stable plus dedicated production signing, distribution/privacy compliance, dependency/supply-chain controls, release rollback and documented support policy.
