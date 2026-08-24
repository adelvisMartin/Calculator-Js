# Repository Structure and Hygiene

## Purpose

The current GitHub repository has a historical slug and contains both legacy root material and the active InSave Android Recovery line. Until a dedicated InSave repository or canonical-source migration is completed, this document defines what is maintained, generated and historical.

## Maintained product areas

### `insave-build/`

Primary InSave-owned Recovery overlays and build logic:

- source patches and generated Kotlin used to reconstruct the current candidate;
- provider/runtime hardening;
- status/media policies;
- security/privacy gates;
- Android tests and build scripts;
- current branding assets required by the official QA build.

New product work should go into the newest maintained version directory or, preferably, the emerging canonical source tree once ADR-0001 is executed.

### `.github/workflows/`

CI/release automation. Workflows should:

- pin important external actions/revisions where practical;
- fail loudly on missing reconstruction anchors;
- separate inherited upstream debt from InSave-owned release blockers;
- never print secrets;
- upload APKs/evidence as Actions artifacts rather than committing large binaries.

### `docs/`

Architecture, QA, audit, security, legal, roadmap and release documentation. `docs/INDEX.md` is the entry point.

## Historical/generated areas

### `insave-build-status*/`

These directories contain historical run locators, logs, hashes and Recovery evidence. They are retained for traceability but are not maintained source code.

Rules:

- do not add large new build logs unless they are genuinely required for an audit trail;
- prefer GitHub Actions artifacts for bulky evidence;
- keep only compact run IDs, checksums and decisive PASS/FAIL summaries in Git when practical;
- do not use historical status files as the current truth for release status.

`.gitattributes` marks these paths as generated for GitHub language statistics.

## Legacy root material

Files such as the historical web demo/root assets may pre-date InSave. They should not be silently deleted while the repository is still serving as the Recovery container because unrelated history may depend on them.

A future repository migration should either:

1. create a dedicated `InSave-Android` repository with a clean history/import; or
2. archive legacy material under a clearly named `legacy/` directory after validating that no workflow or deployment depends on it.

Do not perform a destructive cleanup merely to make the root look cleaner.

## Binary policy

Do not commit generated distribution binaries to normal source history:

- APK/AAB/APKS;
- keystores/signing files;
- build directories;
- local emulator/device captures unless intentionally curated as small documentation evidence.

Use GitHub Actions artifacts/releases for build outputs. `.gitignore` enforces the normal local rule.

Small source-controlled brand assets needed to reproduce the official launcher/icon are an intentional exception.

## Secret policy

Never commit:

- `.env` secrets;
- private API keys;
- cookies/session tokens;
- PO tokens captured from users;
- production signing material;
- database/service credentials;
- private user media or logs containing personal paths/data.

If a secret reaches Git history, rotate it. Removing the latest file does not erase historical exposure.

## Naming and versioning

- release source changes require a new version code/name when distributed as a new candidate;
- never rename an existing APK to simulate a new version;
- current release docs and CI artifact names must agree;
- QA, Stable and Production-ready are distinct labels and must not be conflated.

## Branch discipline

- do not develop directly on the protected/default branch when a feature/fix branch is appropriate;
- one branch should have one principal purpose;
- preserve the last-known-good reconstruction path until its replacement passes equivalent gates;
- merge documentation/legal changes independently from risky runtime changes when possible.

## Recommended future repository cleanup

When InSave moves to a dedicated canonical repository:

1. promote owned source so normal builds do not depend on replaying historical patches;
2. move Recovery scripts under `tools/recovery/` or archive them;
3. move historical run records under `docs/history/` or external release evidence;
4. keep only current workflows active;
5. preserve Git tags/checksums for released artifacts;
6. retain license provenance and third-party notices through the migration;
7. keep InSave branding separate from GPL software licensing boundaries.
