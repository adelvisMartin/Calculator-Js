# Additional Recovery Review Agents

These profiles complement `AGENTS.md`; they are evidence responsibilities, not runtime bots.

## Competitive Intelligence Agent
Continuously compares InSave interaction patterns against maintained Android downloaders/status savers (Snaptube, TubeMate, VidMate, Seal, current Status Saver apps). May extract interaction ideas but must not copy proprietary branding/assets/code. Every adopted pattern needs an InSave regression gate.

## Extraction Resilience Agent
Maintains the three-engine matrix and automatic failover policy:
1. NewPipe + per-video PO-token direct stream.
2. Local yt-dlp/youtubedl-android full extractor.
3. Optional self-hosted Cobalt-compatible endpoint.
No single engine may silently become a hard dependency.

## Runtime Packaging Agent
Verifies Python/yt-dlp, QuickJS/runtime payload, FFmpeg and aria2c are present and version-compatible. During LKG recovery, APK size optimization is prohibited if it removes or weakens runtime payloads.

## Android OEM Compatibility Agent
Checks MIUI/Xiaomi behavior, Android 11–16 storage differences, Special App Access, MediaStore, background workers and notification restrictions. Redmi-class physical behavior takes precedence over generic emulator assumptions.

## Observability/Diagnostics Agent
Ensures each failed job records provider attempted, yt-dlp/NewPipe/Cobalt error category, FFmpeg exit, destination/storage state and retry decision without leaking cookies, API keys, signed media URLs or user-sensitive values.

## UX Regression Agent
Blocks any release where Statuses lands in a file picker, MP3 is hidden behind video-first UI, the first checkbox cannot be selected, selection disappears during scroll, or technical package-update dialogs interrupt the normal user journey.
