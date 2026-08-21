# InSave recovery skill playbooks

The recovery branch uses these project-local playbooks as review gates.

- **LKG recovery:** compare every change against the historically working v0.9 behavior and preserve working modules.
- **Android status storage:** automatic WhatsApp and WhatsApp Business discovery is primary; the document-tree picker is fallback only.
- **YouTube dual engine:** NewPipe with its per-video token provider resolves a fresh direct audio stream first; yt-dlp extraction remains the fallback.
- **Media/FFmpeg:** validate the packaged runtime by converting a real public stream to MP3 inside Android, not by checking strings in the APK.
- **Regression QA:** source contract, unit tests and Android instrumented tests must pass before an RC artifact is accepted.
- **Android release:** verify installable APK structure, arm64 native libraries, signature structure and checksum.
- **Application safety:** keep URL/network validation, bounded retries, private-data redaction and non-destructive failures while preserving the local automatic-status workflow requested for this sideload build.
- **UI/accessibility:** preserve the five InSave destinations and dark/magenta product identity; review touch targets, typography, loading, empty and error states only after the P0 runtime paths pass.

## Release rule

`ASSEMBLE PASS` is not a functional pass. A recovery build is blocked unless the Android emulator proves both a real public YouTube-to-MP3 flow and automatic `.Statuses` discovery from realistic WhatsApp/Business paths. Physical-phone confirmation is still required before calling a release Stable.
