# InSave Security & Privacy Baseline

## Security posture

InSave processes untrusted URLs, remote metadata, local media files, Android intents and embedded executable/runtime components. The Recovery line is therefore security-sensitive even though it does not require an account for normal public downloads.

This document separates **current Recovery behavior** from **production requirements**. A Recovery QA build is not automatically a production-secure distribution.

## 1. Storage permissions

### Recovery/sideload behavior

Automatic WhatsApp/WhatsApp Business discovery reads `.Statuses` media under shared storage. The Recovery approach uses Android special broad storage access where required in order to reproduce the historical automatic experience.

### Production concern

`MANAGE_EXTERNAL_STORAGE` exposes substantially more shared storage than InSave needs for the status feature alone and is restricted by Google Play policy. It must not be treated as a harmless ordinary permission.

### Required distribution strategy

Create separate capabilities/flavors:

- **Recovery/sideload:** automatic direct discovery may request broad access after an explicit explanation and user action.
- **Play:** prefer SAF/MediaStore or another privacy-minimized implementation. If broad access is ever proposed for Play, policy eligibility must be reviewed and documented before release.

The app must work safely when the user denies broad access. No crash, repeated coercive prompt or silent permission escalation.

## 2. Signing and keys

### Current blocker

The pinned upstream Gradle release configuration uses a signing configuration named `debug` for the release build. This is acceptable only for Recovery QA and is a production blocker.

### Production requirements

- Dedicated upload/release keystore.
- Key/password values from CI secrets or a secure key-management service, never committed to Git.
- Documented offline backup and recovery.
- Separate debug and production certificates.
- Play App Signing when distributing through Google Play.
- Release pipeline records certificate SHA-256 fingerprint.
- No production artifact may be signed with the Android debug key.

## 3. Exported Android components

Every Activity, Service, Receiver and Provider must explicitly define whether it is exported.

The Recovery build currently injects an exported InSave hub activity. Before Production:

1. determine whether external apps genuinely need to launch it;
2. set `android:exported="false"` if they do not;
3. if external entry is required, constrain intent filters and validate action/data/extras;
4. protect privileged family-app IPC with signature permissions when applicable;
5. never redirect a caller-controlled nested Intent without sanitization.

Incoming query/URL extras are untrusted input.

## 4. URL and network validation

Supported URL input must be parsed, not validated with ad-hoc substring checks.

Requirements:

- allow only explicitly supported schemes (`https` by default; other schemes only for a documented local use case);
- normalize hostnames safely;
- reject malformed control characters and oversized input;
- apply an allow/deny policy before sending data to configurable remote Provider C;
- do not silently send a user URL to a public third-party fallback;
- enforce HTTPS for remote extraction endpoints unless a local-development switch explicitly allows otherwise;
- use bounded connect/read/write/call timeouts;
- cap retries and apply backoff;
- never disable TLS certificate validation for convenience.

If future self-hosted Cobalt endpoints are supported, display the configured host in Settings and diagnostics.

## 5. PO tokens, cookies and signed media URLs

Treat the following as sensitive transient values:

- cookies/session material;
- PO tokens;
- signed media URLs;
- authorization headers;
- API keys;
- private self-hosted endpoint credentials.

Rules:

- never store them in plain diagnostic files unless strictly necessary and explicitly protected;
- redact them from logcat, crash reports and uploaded QA artifacts;
- use the narrowest lifetime possible;
- do not reuse video-bound tokens globally;
- do not include secrets in analytics events.

## 6. Runtime and updater supply chain

InSave embeds/interacts with executable runtime components such as Python/yt-dlp, QuickJS, FFmpeg/FFprobe and aria2c. Runtime updates are equivalent to code updates and need stronger controls than ordinary content downloads.

Production requirements:

- only trusted HTTPS origins;
- version manifest with SHA-256 for every payload;
- verify payload hash before activation;
- ideally sign the update manifest and verify its public-key signature in-app;
- atomic installation: download -> verify -> stage -> activate;
- retain last-known-good runtime for rollback;
- reject downgrade unless explicitly allowed for recovery;
- record runtime version with every failure report;
- never execute an unverified arbitrary file supplied by a URL or user-controlled path.

## 7. FFmpeg/process input safety

Use typed process argument arrays; do not build shell command strings from untrusted titles, filenames, query text or metadata.

- sanitize generated filenames separately from process arguments;
- protect against path traversal (`../`, encoded traversal, absolute-path overwrite);
- constrain temporary/output directories;
- never extract archives without validating final canonical paths;
- cap metadata lengths passed into post-processing;
- check exit codes and output existence before marking Completed.

## 8. Local files and playback

- Prefer `content://` URIs/FileProvider when sharing files externally.
- Apply least-privilege URI grants.
- Validate that a history item still maps to an intended media file before opening it.
- Deleted/moved media should become a recoverable UI state.
- Never expose private app-internal file paths to another application without FileProvider.

## 9. Logging and observability

Diagnostics are valuable only when privacy-safe.

Allowed examples:

- provider ID;
- typed error category;
- HTTP status category where useful;
- extractor/runtime version;
- attempt count and duration;
- redacted host;
- FFmpeg exit code;
- storage permission/capability state.

Redact/omit:

- cookies;
- PO tokens;
- signed full stream URLs/query strings;
- credentials/API keys;
- full personal filesystem paths when not necessary;
- clipboard contents;
- raw private endpoint tokens.

Add automated tests that feed sentinel secrets and fail if the sentinel appears in generated diagnostic output.

## 10. Dependency security

Required production controls:

- Dependabot/Renovate for Gradle and GitHub Actions.
- Dependency review on pull requests.
- OSV/another vulnerability scanner in CI.
- Generate an SBOM (CycloneDX or SPDX) for each release.
- Store dependency and native runtime versions in release evidence.
- Maintain third-party license/NOTICE documentation.
- Remove dead/duplicate dependencies and replace abandoned libraries when feasible.

The current dependency graph includes a deprecated Accompanist WebView path and version differences among youtubedl-android runtime packages; these are maintenance risks that need review, not proof by themselves of exploitable vulnerabilities.

## 11. Data minimization

InSave's normal public download experience should remain account-free and local-first.

- Do not add authentication merely to solve extractor failures.
- Do not collect a user's download history remotely by default.
- Do not upload WhatsApp status media.
- Remote Provider C must be opt-in/configured and clearly disclosed.
- Analytics, if ever introduced, must be optional/minimal and never include media URLs or filenames by default.

## 12. Abuse and lawful-use boundary

InSave should document that users are responsible for downloading and saving content they are authorized to access and for complying with applicable law and platform terms. Do not market the app as bypassing paid access, DRM or authentication controls.

## 13. Security release blockers

Production release is blocked by any of the following:

- debug signing or exposed private signing key;
- unreviewed broad storage permission in the target distribution channel;
- unvalidated exported component accepting privileged actions;
- credentials/tokens in source or QA artifacts;
- runtime update executed without integrity verification;
- critical/high known dependency vulnerability without explicit mitigation/acceptance;
- path traversal/arbitrary overwrite in runtime/archive/media handling;
- TLS verification disabled;
- unresolved data-loss bug.

## 14. Incident/rollback baseline

For every production release retain:

- previous stable APK/AAB/source tag;
- release SHA-256 and signing fingerprint;
- dependency/SBOM artifact;
- runtime manifest;
- known-good provider configuration.

If an extractor/runtime update breaks downloads, roll back the runtime independently when possible. If application code or storage behavior is implicated, ship a signed hotfix and never delete user download/history data as a recovery mechanism.
