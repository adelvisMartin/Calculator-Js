# InSave Recovery — Competitive UX/Runtime Research (2026-08-21)

Purpose: recover proven interaction patterns without copying proprietary branding or layouts. The goal is to make InSave faster and clearer than the rejected 0.16.x shell while keeping its own dark/magenta identity.

## Snaptube — behavior to learn from

Sources reviewed:
- https://www.snaptube.io/
- https://www.snaptube.io/snaptube-app/
- https://www.snaptube.io/snaptube-original/
- https://origin.snaptube.com/

Observed product patterns:
- No account/login as a prerequisite for normal public downloads.
- Search/paste is the primary entry point; format selection follows immediately.
- Audio and video are first-class choices, not hidden advanced settings.
- Batch and playlist downloads are a normal flow.
- High-quality audio is explicitly marketed (MP3/M4A); users can choose quality.
- Background downloading and an offline local library/player reduce context switching.
- Multi-platform support is presented as one coherent product rather than separate technical extractors.

InSave recovery decisions:
- Default to Audio / MP3 for the user's primary music workflow.
- MP3 quality selector remains visible: 320 / 256 / 192 kbps.
- Keep M4A/Opus available later as an advanced high-fidelity/source-preserving option.
- Playlist selection must expose real checkboxes, persistent selection and selected-count action.
- Normal public YouTube flow must not ask for login/cookies.
- Keep downloads in background and expose simple Queue / Saved states rather than upstream technical tabs as the primary UI.
- No Python/package-update modal in the normal download journey.

## Seal — runtime and UI lessons

Source reviewed:
- https://github.com/JunkFood02/Seal

Observed patterns:
- Full local yt-dlp-based engine is acceptable on Android.
- Embedded aria2c, media metadata processing and playlist support are normal product features.
- Material 3 can provide a clean shell while a heavy extraction runtime stays below it.
- General mode must remain simple; terminal/custom-command functionality is secondary.

InSave recovery decisions:
- Do not optimize away extraction/runtime components merely to reduce APK size.
- Align youtubedl-android library / FFmpeg / aria2c versions.
- Keep advanced extractor/terminal diagnostics behind Ajustes/Diagnóstico.
- InSave's five-destination navigation remains the product shell.

## WhatsApp Status Saver apps — behavior to restore

Sources reviewed:
- https://play.google.com/store/apps/details?id=com.statusvideo.statussaver
- https://play.google.com/store/apps/details?id=com.ocdeveloper.statussaver
- https://play.google.com/store/apps/details?id=winter.whatsapp.status.save.statussaver
- https://play.google.com/store/apps/details?id=com.app.nativex.statussaver

Repeated interaction pattern across current apps:
1. User views a status in WhatsApp/WhatsApp Business so media exists locally.
2. User opens the status saver.
3. Active statuses load automatically into an in-app gallery.
4. Images/videos can be previewed and saved with one tap.
5. Many apps support WhatsApp + Business, multi-select/bulk save and auto-detection.

InSave recovery decisions:
- Automatic local discovery is the primary flow for the local/sideload build.
- WhatsApp and WhatsApp Business remain separate source tabs.
- Images and Videos remain separate filters with counts.
- Full-screen preview + save/share actions stay inside InSave.
- SAF folder picker is fallback only, never the default landing experience.
- Remove arbitrary item-count caps from status discovery.

## Cobalt — optional third-engine/API architecture

Sources reviewed:
- https://github.com/imputnet/cobalt
- https://github.com/imputnet/cobalt/blob/main/api/README.md

Key finding:
- Cobalt explicitly recommends self-hosting an API instance for reliable project integration; public instances should not be treated as a guaranteed backend.
- Its API model supports audio mode, MP3 and configurable audio bitrate, plus multiple social sources.

InSave recovery decision:
- Core P0 functionality remains local and must work without a server.
- Introduce a provider interface that can later use a SELF-HOSTED Cobalt-compatible endpoint as a third fallback after local NewPipe and local yt-dlp.
- Never hard-code or silently depend on a community/public Cobalt instance.
- Endpoint failure must not disable the local engines.

## Product contract derived from comparison

### Home / Search
- Paste/search first.
- Public download anonymous-first.
- Initial 6 results; expand to 30.
- Visible checkbox on every result, including index 0.
- Selection survives scroll/re-render/expand-collapse.

### Audio
- MP3 is primary action.
- 320 kbps target is a conversion target, not a claim that source audio contains 320 kbps of unique information.
- First stabilize clean conversion; loudness normalization stays outside P0.
- One selected item = one immutable source URL/job.
- Batch jobs fail independently.

### Statuses
- Open Statuses -> automatic scan -> gallery.
- No file explorer unless automatic access cannot be granted and user chooses fallback.
- Re-scan on resume.
- WhatsApp/Business + Images/Videos + preview + one-tap save.

### Diagnostics
- User-facing error first: clear cause and retry action.
- Full yt-dlp/NewPipe/FFmpeg logs retained for QA.
- Package/runtime update controls stay in Settings, not modal interruptions.

## Gate rule

No competitive-research finding counts as implemented until an automated or physical-device regression gate proves the resulting behavior. `compile`, `assemble`, screenshots, or strings in the APK are not substitutes for runtime verification.
