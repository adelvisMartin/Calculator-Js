# InSave v0.17.2 Recovery UX — Release Notes / QA Candidate

## Objective

v0.17.2 addresses defects observed during physical-phone testing of the v0.17.1 Recovery Heavy line while preserving the extraction P0 behavior already recovered.

## User-visible corrections targeted

### States

- Remove the historical visible-item/truncation behavior that made only the first items appear usable.
- Scrollable RecyclerView for the gallery.
- Automatic WhatsApp and WhatsApp Business discovery remains primary.
- Images/Videos source filters preserved.
- Add `Buscar estados` field.
- Filter by status filename without case sensitivity.
- Display the number of currently shown results.
- Keep SAF/manual folder access as fallback.

### Home/search

- Keep URL paste support.
- Plain song/artist text is no longer rejected as if every input had to be a URL.
- Shell sends `insave_query` and MainActivity bridges the query into HomeFragment using the existing `url` navigation argument.
- Search repository retains a `ytsearch10:` fallback for plain search queries.
- Audio/video selection remains available after result resolution.

### Android Back

- Remove the behavior that immediately terminates the application from a secondary view.
- First Back from an InSave subview returns to Inicio.
- Root-state exit remains Android-standard behavior.

### Download playback

- History/download item opens the playable local path using the maintained file-opening flow instead of treating the action as only Share.
- Missing files must be handled as recoverable state during further hardening.

### MP3 loudness

- Recovery pipeline includes FFmpeg loudness normalization target `loudnorm=I=-9:TP=-1.0:LRA=7` for the relevant MP3 path.
- QA must confirm audible improvement without clipping/conversion regressions on a physical device.

### Branding

- New InSave logo payload is integrated into Android resources/manifest branding.
- Product name remains InSave.

## Extraction behavior preserved from v0.17.1/P0 work

- Provider order A -> B -> optional C.
- Provider A failure must not abort the chain.
- Provider B uses the local yt-dlp runtime.
- yt-dlp Recovery payload is pinned to the 2026.08.19 hardening line used by the Recovery gate.
- YouTube client hardening uses `mweb` in the P0 path.
- Player/GVS PO-token behavior remains video-aware rather than a single global manual token.
- Playlist jobs remain independent.
- Provider C is optional and not a required external dependency.

## Hardened v0.17.2 visual QA

The test environment creates at least **14 WhatsApp image fixtures** so a six-item regression cannot pass accidentally.

Expected evidence:

1. Inicio.
2. WhatsApp States at top of gallery.
3. WhatsApp States after a real scroll gesture.
4. Status search targeting a later fixture.
5. WhatsApp Business.
6. Descargas.
7. Seguidores.
8. Ajustes.
9. Inicio after pressing Android Back from a secondary view, with app process still alive.

Visual evidence supplements functional tests; it does not replace YouTube/MP3 E2E.

## Complete Universal artifact contract

User QA requested the **complete**, not lightweight, APK. The v0.17.2 packaging workflow therefore publishes a `heavy-COMPLETE-universal` candidate and verifies the four configured ABI directories:

- arm64-v8a
- armeabi-v7a
- x86
- x86_64

It also checks presence of core native runtime on ARM64, ZIP integrity and SHA-256 generation.

## Candidate status

This file describes the intended v0.17.2 candidate. Do not mark **Stable** until:

- current complete Universal workflow succeeds;
- Android P0 is executed on the current recovery source/candidate line;
- exact candidate SHA-256 is tested on a physical phone;
- no P0 regression is observed.

## Manual physical-phone QA script

1. Install the complete Universal APK as the intended test package.
2. Record phone model, Android/MIUI/HyperOS version and APK SHA-256.
3. Open States; grant required Recovery access when prompted.
4. Confirm more than six current WhatsApp image statuses can be reached by scrolling.
5. Switch to Videos and WhatsApp Business.
6. Use status search.
7. Return to Inicio and search a song by name, not URL.
8. Download one item as MP3.
9. Download a list/playlist selection with at least two distinct items.
10. Open downloaded audio from Descargas/history and play it.
11. Compare loudness with the previous Recovery build at the same system volume; listen for clipping/distortion.
12. Enter Ajustes, press Android Back once and verify InSave returns internally rather than closing immediately.
13. Restart app and confirm completed downloads/history remain usable.
14. Report any failure with screen recording/screenshot, exact action and visible message; do not share private cookies/tokens.

## Known production blockers unrelated to v0.17.2 UX

- Dedicated production signing still required.
- Recovery patch-driven source needs migration to an owned InSave codebase.
- Play distribution/storage permission strategy must be resolved.
- Dependency/SBOM/license and Gradle deprecation hardening remain P1.

See the audit and roadmap for the complete production-readiness plan.
