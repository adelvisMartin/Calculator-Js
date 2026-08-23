# InSave v0.18 Threat Model

## Protected assets
- user-selected URLs and search queries;
- local WhatsApp/WhatsApp Business status media;
- download history and destination paths;
- cookies when the user explicitly configures them;
- dynamic PO/visitor token material;
- optional Provider C API key;
- production signing key and passwords;
- embedded runtime integrity (yt-dlp/Python/FFmpeg/aria2c/QuickJS);
- diagnostic logs/screenshots/artifacts.

## Trust boundaries

### Boundary A — Android external Intents
`ShareActivity` is intentionally exported for ACTION_SEND/ACTION_VIEW. All incoming URI/text is untrusted. The value must pass `InSaveInputPolicy` before it reaches result/extractor logic. Internal Activities are not exported.

Threats: Intent injection, file/content scheme exposure, local-network probe URL, oversized/control-character input, accidental sensitive Intent logging.

Controls: scheme restriction, URL length bound, credentials rejection, loopback/private literal rejection, no full Intent logging, internal Activity export reduction.

### Boundary B — User paste/search
Search is allowed, but it is not treated as a URL or shell command. Non-HTTP URI-looking strings are rejected; ordinary search text is whitespace-normalized and bounded.

Threats: shell-like input reaching runtime options, malformed URI, denial by huge input.

Controls: typed URL/Search classification, no raw concatenation into shell, 256-character search bound, 4096-character URL bound.

### Boundary C — Provider C endpoint
Provider C is optional and explicitly configured. A source URL, endpoint and returned media URL are three separate untrusted values.

Threats: SSRF/local service access, cleartext API-key disclosure, malicious redirect/tunnel URL, credential-bearing URL.

Controls: public HTTPS endpoint in release, local HTTP only for explicit debug emulator use, source validation, response URL validation, bounded timeouts, Provider C last in chain.

### Boundary D — YouTube dynamic challenge material
PO tokens/visitor data are transient secret-like runtime values even when not account credentials.

Threats: token reuse across videos, leaking in logcat/artifacts, incompatible token reuse with fallback clients.

Controls: per-video token generation, B2/B3 clear mweb PO material, redacted debug logging, logcat leak scan.

### Boundary E — Local storage
Recovery sideload has broad local storage visibility to discover WhatsApp statuses. This is high privilege even when the feature is legitimate.

Threats: unnecessary read scope, accidental upload of local files, Play policy incompatibility.

Controls: no server dependency for status discovery, Provider C never receives status files, explicit sideload vs Play flavor separation, Play merged-manifest gate removes All Files Access.

### Boundary F — WebView token helper
A user-visible WebView exists only as a fallback/manual helper.

Threats: file/content access, mixed-content downgrade, arbitrary redirect, abandoned wrapper dependency.

Controls: platform WebView, `allowFileAccess=false`, `allowContentAccess=false`, mixed-content never, Safe Browsing where supported, URL validation, explicit destruction.

### Boundary G — Native/embedded runtimes
Heavy APK contains powerful parsing/execution components.

Threats: stale vulnerable runtime, tampered yt-dlp payload, ABI packaging error, untrusted command composition.

Controls: pinned yt-dlp digest, SBOM, native library inventory, four-ABI APK inspection, request-object API instead of shell concatenation, update/rollback documentation.

### Boundary H — CI/release
Build pipeline can produce distributable binaries and handles future signing secrets.

Threats: mutable third-party actions, secret exfiltration, debug key mistaken for production, unproven artifact promotion.

Controls: full-SHA action pinning, job-scoped permissions, production signing through environment secrets only, SHA-256 artifacts, provenance/evidence manifest, physical-phone gate before Stable.

## Explicit non-goals
InSave does not attempt to bypass access controls for private, members-only, paid, removed or authentication-required content. The anonymous fallback ladder is only for public-content extraction failures classified as bot challenge, 403, no-format or transient-network conditions.

## Logging policy
Permitted: provider identifier, failure class, retry decision, FFmpeg exit/error category, destination state, non-secret extractor text.

Redacted: Authorization/Bearer, cookies, PO tokens, visitor data, API/access/refresh token values and signature/token query parameters in signed URLs.

Forbidden: production signing secrets, private key contents, full raw incoming Intents.

## Residual risk requiring physical QA
- OEM storage permission presentation/behavior;
- MIUI background restrictions;
- real WhatsApp/Business path variations;
- system file-picker behavior on policy-compliant Play flavor;
- device-specific media opening and notification handling.

These are release risks and cannot be converted into an automated PASS merely because emulator tests are green.
