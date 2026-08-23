# InSave QA & Release Gate

## Principle

A compiled APK is not evidence that the product works. InSave uses layered evidence: source/unit checks, package integrity, Android instrumentation/emulator behavior and physical-phone confirmation.

## Release classes

| Class | Meaning |
|---|---|
| Recovery build | Reconstructed feature line; may contain known defects. |
| QA candidate | Build + automated required gates pass. |
| Stable | QA candidate + representative physical-device P0 pass + no open P0 defect. |
| Production-ready | Stable + production signing, distribution/privacy compliance, supply-chain/security gates and rollback procedure. |

## P0 functional matrix

### Home/search

- Plain artist/song text returns search results; it is not treated as an invalid URL.
- URL paste still works.
- Audio and Video remain visible choices.
- Result index 0 is selectable.
- Selection persists through scroll/re-render.
- One selected item creates one job.

### YouTube extraction

- Provider A failure must not terminate Provider B.
- Provider B must be exercised on a currently public video, not only through string/config checks.
- Per-video PO-token generation is verified for the video being resolved.
- A real Android run must produce a playable MP3.
- Playlist/batch gate uses at least two distinct public videos and produces independent outputs/jobs.
- Provider C stays optional and off by default.

### MP3

- Explicit audio extraction and MP3 conversion.
- Quality choices remain normalized product options.
- FFmpeg exit status is checked.
- Output exists, has non-trivial size and is playable.
- Loudness normalization must not introduce clipping or conversion failure; physical listening remains a supplemental gate.

### WhatsApp/Business States

- Automatic access/discovery is the primary Recovery flow.
- WhatsApp and Business sources are distinguishable.
- Images/Videos filters work.
- QA fixture contains more than six items (current hardened fixture: 14 images) so truncation cannot hide.
- Capture before and after a real scroll gesture.
- Search a fixture outside the first visible cards and verify filtered result/count.
- Save/preview operation is verified where the test environment supports it.
- SAF manual tree remains fallback.

### Android Back

- From a secondary InSave destination, first Back returns to Inicio.
- App process remains alive after that first Back.
- Exit behavior is only exercised from the root state.

### Downloads/player

- Completed download can be opened from history/library.
- Audio and video MIME/path handling choose a compatible player intent/internal player.
- Missing/deleted file produces a clear recoverable state rather than a crash.

## Package integrity

The COMPLETE Universal QA APK must:

- pass ZIP integrity;
- include all configured ABIs: arm64-v8a, armeabi-v7a, x86, x86_64;
- contain required native runtime for ARM64 at minimum: Python, FFmpeg and QuickJS; runtime inventory should ultimately include FFprobe/aria2c verification too;
- have a recorded SHA-256;
- expose versionName/versionCode matching the declared candidate;
- install cleanly as its intended package identity.

Do not rename an old APK to satisfy a version request.

## Device matrix

Minimum Stable matrix:

| Category | Minimum |
|---|---|
| Xiaomi/MIUI/HyperOS physical device | 1 representative user device |
| Stock/near-stock Android physical device | 1 |
| API 35/36 emulator | 1 with KVM acceleration |
| Android 11/12 storage behavior | at least one test path |
| Android 14–16 storage/notification behavior | at least one current device/emulator |

Expand later with low-memory, tablet/foldable and 32-bit coverage according to actual user telemetry/support needs.

## Evidence package

Every QA candidate should publish:

- APK(s)/AAB appropriate to distribution;
- SHA-256 manifest;
- exact Git commit and upstream dependency commit;
- dependency/runtime versions;
- unit-test result;
- Android E2E result;
- P0 result summary;
- logcat excerpt for failures with secrets redacted;
- screenshots captured by test automation;
- known issues and rollback target.

Recommended screenshots for v0.17.2:

1. Inicio.
2. Estados WhatsApp — top.
3. Estados WhatsApp — after scrolling beyond first visible cards.
4. Estados WhatsApp — search/filter.
5. Estados Business.
6. Descargas.
7. Seguidores.
8. Ajustes.
9. Inicio after Back from subview.

## Failure policy

A gate is FAIL when behavior cannot be proven, not only when a crash occurs. Examples:

- NewPipe fails and test aborts without reaching B -> FAIL.
- Build passes but Universal APK was not produced -> FAIL.
- Search UI exists but plain text never reaches search repository -> FAIL.
- 14 states exist on disk but test never scrolls -> incomplete evidence.
- Screenshot contains a label but underlying action was never executed -> source/visual evidence only, not functional PASS.

## Flaky-test policy

- One automatic retry is allowed only for infrastructure/emulator startup failure.
- Provider/network failures must be categorized; repeated external-service instability is not automatically a test flake.
- A retry that passes after a functional failure is recorded as flaky/degraded, not silently green.
- Keep fixture IDs configurable because public media can become unavailable.

## Performance gates (P1)

Add measurable thresholds after the Recovery line stabilizes:

- cold/warm startup macrobenchmark;
- status scan time for 10/100/1000 media items;
- grid frame/jank benchmark;
- memory high-water mark during status gallery;
- single/batch download CPU and battery impact;
- cancellation latency;
- resume-after-process-death correctness.

## Security QA (P1)

- malformed/oversized search input;
- `file://`, `content://`, localhost/private-network and unsupported scheme validation according to policy;
- malicious endpoint configuration;
- intent extra fuzzing for exported components;
- archive traversal payloads for runtime/package ZIP handling;
- logs inspected for token/cookie/signed URL leakage;
- dependency/SBOM scan.

## Stable sign-off checklist

A release manager may mark Stable only when all P0 tests pass on the candidate binary, not merely on a nearby commit. Physical phone QA must record device/Android version and exact APK SHA-256. Any post-QA code change invalidates the Stable sign-off and requires a new candidate hash.
