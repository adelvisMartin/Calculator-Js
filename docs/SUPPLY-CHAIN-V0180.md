# InSave v0.18 Supply-Chain & Provenance Policy

## Immutable inputs
- Android engine: `deniscerri/ytdlnis@c6084ed4f110efd4ba0c3f82bb16723b6529c8f0`.
- Embedded yt-dlp: `2026.08.19`, SHA-256 `1fa6733c37ea6fb51c99ad8fe785e7b7e5f3246c9b980230329d4fb72ed8d4d6`.
- Quality workflow actions are referenced by full commit SHA, not floating major tags.

## Pinned CI actions in v0.18 quality gate
- `actions/checkout`: `d23441a48e516b6c34aea4fa41551a30e30af803`.
- `actions/setup-java`: `b6effb05e454b25005698d916606bdc6ffcbf961`.
- `actions/upload-artifact`: `ea165f8d65b6e75b540449e92b4886f43607fa02`.
- `reactivecircus/android-emulator-runner`: `a421e43855164a8197daf9d8d40fe71c6996bb0d`.

Pins are updated only through reviewed dependency maintenance followed by the full quality gate.

## SBOM
CI captures `githubReleaseRuntimeClasspath`, parses resolved Maven coordinates and emits CycloneDX 1.6 JSON. The SBOM also records embedded runtimes that may not appear as ordinary Gradle coordinates, including yt-dlp, Python, FFmpeg, aria2c and QuickJS.

The yt-dlp file itself is SHA-256 verified while generating the SBOM. A mismatch blocks the build.

## APK provenance
Every QA artifact includes:
- version name/code;
- application ID;
- SHA-256;
- upstream SHA;
- overlay SHA/workflow head;
- workflow run/attempt;
- yt-dlp version;
- evidence manifest;
- SBOM.

## Production signing boundary
Production keystore material is not part of source provenance and must never be committed. The build reads release key path/password/alias/key password only from protected environment/CI secrets. A QA build without those secrets cannot be described as production-signed.

## Dependency updates
Dependency updates are not merged only because a newer version exists. Required process:
1. identify update and security/change reason;
2. inspect changelog/release notes;
3. update one dependency family at a time when feasible;
4. rebuild all required variants;
5. run unit/lint/security/warning gates;
6. run Android real-output/visual E2E;
7. regenerate SBOM;
8. compare warning count and artifact/runtime behavior;
9. retain rollback commit/runtime digest.

## Embedded runtime update policy
yt-dlp is expected to move more frequently than the rest of the Android app. Updating it requires:
- new version + digest;
- source-contract check;
- Provider B request check;
- real public MP3 test;
- two-job batch test;
- rollback to last known-good embedded file.

Python/FFmpeg/aria2c/QuickJS updates additionally require ABI packaging checks and media conversion validation.

## Trust statement
An action, dependency or runtime being popular is not sufficient evidence of safety. InSave's release claim depends on immutable references, artifact hashes, generated inventory and runtime tests. Third-party source authenticity remains a residual supply-chain risk and is tracked rather than hidden.
