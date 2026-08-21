# InSave recovery skill playbooks

The recovery branch uses these project-local playbooks as review and release gates. They are engineering playbooks, not runtime dependencies.

- **LKG recovery:** compare every change against the historically working v0.9 behavior and preserve working modules instead of replacing them with a new shell.
- **Android status storage:** automatic WhatsApp and WhatsApp Business discovery is primary; the document-tree picker is fallback only.
- **YouTube provider routing:** Provider A resolves a fresh public stream with NewPipe/BotGuard/PO-token-aware logic; Provider B is the fully local Python/yt-dlp runtime; Provider C is an optional self-hosted Cobalt endpoint. Failure of one provider must not invalidate the other paths.
- **Per-video PO-token awareness:** never assume that one YouTube token can safely serve a whole playlist. Playlist/Mix entries are modeled and retried as independent jobs.
- **Playlist batch orchestration:** preserve visible selection, select-all/invert/clear behavior, cap one InSave batch at 50 distinct entries, keep stable playlist ordering and allow one failed item without cancelling unrelated jobs.
- **MP3 quality contract:** Audio mode must explicitly request `-x`, `--audio-format mp3` and one normalized CBR preset (`320K`, `256K`, `192K`). Do not rely on an implicit container conversion path.
- **Media/FFmpeg validation:** validate the packaged runtime by converting a real public stream to MP3 inside Android, not by checking strings in the APK. Batch QA must create at least two distinct real MP3 outputs.
- **Runtime packaging:** Python, yt-dlp runtime, FFmpeg, FFprobe, aria2c and QuickJS are release payloads, not optional size optimizations. APK size is secondary to functionality for the Recovery line.
- **Retry/resilience:** use bounded network retries, fragment retries, socket timeouts and retry backoff. Retry policy is per job; a batch is not one all-or-nothing transaction.
- **Fallback endpoint safety:** Cobalt integration is disabled unless an explicitly configured self-hosted endpoint exists. Do not silently route user URLs through arbitrary public instances.
- **Android KVM E2E:** GitHub-hosted Ubuntu instrumented tests must verify `/dev/kvm` read/write access and run with VM acceleration enabled before Android functional results are trusted.
- **Regression QA:** source contract, unit tests, embedded-runtime checks and Android instrumented tests must pass before a Recovery artifact is accepted.
- **Android release:** verify installable APK structure, ARM64 native runtime libraries, ZIP integrity and SHA-256 checksum.
- **Application safety:** keep URL/network validation, bounded retries, private-data redaction and non-destructive failures while preserving the local automatic-status workflow requested for this sideload build.
- **UI/accessibility:** preserve the five InSave destinations and dark/magenta product identity; make MP3, playlist selection and status saving primary user flows rather than exposing technical downloader configuration.
- **Competitive regression review:** periodically compare current Snaptube/TubeMate/VidMate/Seal/Status-Saver patterns for workflow regressions, while never copying proprietary code, brand assets or protected UI.

## Release rule

`ASSEMBLE PASS` is not a functional pass. A Recovery build is blocked unless Android proves all required P0 gates: automatic `.Statuses` discovery, a real public YouTube-to-MP3 conversion without login, and multiple independent MP3 jobs representing selected playlist entries. Physical-phone confirmation is still required before calling a release Stable.
