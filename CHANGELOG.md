# Changelog

This changelog summarizes the maintained public Recovery line. Detailed QA and historical evidence remain in `docs/` and the build-status/run artifacts.

## [0.18.2] — 2026-08-24

### Fixed

- Applied the approved InSave launcher artwork to the application and all launcher activity aliases (`Default`, `DarkIcon`, `LightIcon`, `BlueIcon`, `GreenIcon`) so Android no longer falls back to legacy launcher branding.
- Replaced the malformed legacy launcher-image path with a validated WebP derivative of the approved InSave logo.
- Added build-time verification that the exact launcher resource is present in the final Heavy Universal APK.

### Verified

- source reconstruction;
- unit tests;
- Heavy Universal Android build;
- security contracts;
- launcher/application branding contract;
- APK ZIP/package integrity;
- required ABIs and heavy runtime payload.

### Status

QA candidate. Not described as production-signed or Stable solely on the basis of automated packaging.

## [0.18.1] — 2026-08-24

### Added

- top-level **Descargas sociales** entry point;
- separate Instagram and Facebook paste/download shortcuts;
- platform URL classification and normalization;
- Facebook support for `facebook.com` / `fb.watch` public URLs through the existing maintained download route.

### Security/privacy

- removed sensitive cookie clipboard logging inherited from upstream;
- hardened generic cookie WebView behavior;
- preserved bounded provider fallback and input/redaction gates from v0.18.0.

## [0.18.0] — 2026-08-23/24

### Hardening

- centralized URL/search input policy;
- private/literal-local host rejection at trust boundaries;
- sensitive diagnostic redaction;
- classified bounded YouTube fallback strategy;
- native hardened PO-token WebView helper;
- release-signing policy and Play-vs-sideload manifest separation;
- SBOM generation;
- critical warning ratchet;
- static security gate and Android API-level QA workflow structure.

## [0.17.2] — 2026-08-23

### Recovery UX

- WhatsApp + WhatsApp Business status discovery improvements;
- status scrolling beyond six items;
- Images/Videos tabs and status search/count;
- free-text song search route;
- internal Android Back navigation;
- downloaded-media open/play behavior;
- MP3 loudness normalization/boost;
- InSave branding resource integration;
- Provider A → B → C resilience;
- Provider B local yt-dlp `mweb` dynamic per-video PO-token flow;
- independent playlist MP3 jobs;
- Heavy Universal runtime packaging.

## Older Recovery builds

Versions before 0.17.2 are retained as historical recovery/build evidence and should not be treated as the current supported public line.
