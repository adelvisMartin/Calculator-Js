# InSave v0.18.2 — Launcher Logo QA

## Purpose

v0.18.2 is a corrective QA candidate over v0.18.1. Its principal release-level change is the launcher branding fix: the official InSave logo must be the resource Android actually resolves for every launcher alias, not merely the application-level fallback icon.

## Included functional baseline

v0.18.2 preserves the v0.18.1/v0.18.0 baseline, including:

- WhatsApp + WhatsApp Business status discovery and scrolling;
- Images/Videos filters and status search;
- free-text song/artist search route;
- internal Android Back navigation;
- downloaded media open/play behavior;
- MP3 loudness normalization/boost;
- Provider A → B → optional C strategy;
- Provider B local yt-dlp path with dynamic per-video PO-token handling;
- bounded `web_embedded` / `android_vr` classified fallback behavior;
- independent playlist/batch MP3 jobs;
- Instagram and Facebook top-level social download shortcuts;
- input validation, secret redaction and WebView/privacy hardening;
- Heavy Universal runtime packaging.

## Launcher correction

The upstream Android manifest exposes multiple launcher aliases. An alias-level `android:icon` overrides the application icon, which is why earlier branding work could still display legacy artwork on-device.

v0.18.2 applies `@drawable/insave_launcher` to:

- application icon;
- application round icon;
- `.Default` launcher alias;
- `.DarkIcon` launcher alias;
- `.LightIcon` launcher alias;
- `.BlueIcon` launcher alias;
- `.GreenIcon` launcher alias.

The launcher resource is a validated WebP derivative of the approved InSave neon logo and is checked by hash before packaging and again after extraction from the completed APK.

## Build identity

- versionCode: `18200`
- versionName: `0.18.2-Launcher-Logo-QA`
- QA application ID: `com.adelvis.insave.recovery`
- build family: Heavy Universal / GitHub Debug QA
- pinned Android upstream: `deniscerri/ytdlnis@c6084ed4f110efd4ba0c3f82bb16723b6529c8f0`

## Packaging gate result

The successful v0.18.2 phone-package workflow passed:

- reconstruction;
- unit tests;
- Heavy Universal build;
- security contracts;
- exact launcher icon/alias contract;
- APK ZIP integrity;
- required ABI presence;
- required Heavy runtime payload;
- final artifact upload.

This automated success does **not** by itself convert the build into a production-signed Stable release.

## Physical-device check

For launcher validation on a real phone:

1. uninstall the prior QA build when signature/cache behavior makes an in-place update unreliable;
2. install the exact v0.18.2 APK;
3. confirm the launcher displays the approved InSave icon;
4. open the app and confirm the process starts normally;
5. verify core status/download/navigation flows on the physical device;
6. record any device-specific launcher cache anomaly separately from an APK resource defect.

## Licensing / distribution

This candidate is GPL-derived software and must be distributed consistently with `LICENSE`, `THIRD_PARTY_NOTICES.md` and `docs/LEGAL-DISTRIBUTION.md`.

The official InSave name/logo/launcher artwork are governed separately by `TRADEMARKS.md` and `BRAND-ASSETS-LICENSE.md`. Modified redistributed forks should be renamed/rebranded and clearly identified as unofficial while retaining all GPL/third-party obligations.
