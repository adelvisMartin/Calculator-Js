# Competitive Research — Iteration 2 (TubeMate / VidMate / music clients)

Date: 2026-08-21

## TubeMate

Sources:
- https://tubemate.net/w3/
- https://tubemate.net/rel_note.jsp?from=690&lang=en&to=99999

Relevant 2026 release pattern:
- Repeated YouTube parsing/download fixes throughout 2026.
- July 2026 introduced an alternate mode specifically for users with YouTube download problems.
- August 2026 stabilized that alternate mode.
- Playlist parsing has its own regression/fix history.

InSave decision:
- A single extraction engine is not acceptable as the only P0 path.
- Recovery keeps Local Engine A: NewPipe/PO-token direct-stream.
- Local Engine B: yt-dlp/youtubedl-android.
- Provider C: optional self-hosted Cobalt-compatible resolver, never mandatory and never silently tied to a public instance.
- Engine selection/failover must be observable in diagnostics and invisible in the normal user flow unless all engines fail.

## VidMate

Source:
- https://www.vidmate.com/

Observed product pattern:
- One product combines video/audio downloads, MP3 selection, player/list management and WhatsApp Status saving.
- WhatsApp Status is presented as a normal first-class feature rather than a storage configuration utility.
- Quality/format choice stays close to the download action.

InSave decision:
- Restore the five InSave destinations rather than exposing upstream engine navigation.
- Statuses must open as a gallery, not a file manager.
- Audio must remain first-class and default to the music-focused path.
- Saved downloads should be playable and manageable inside InSave without requiring a second app.

## YouMusic / RiMusic pattern

Sources:
- https://github.com/TeamYouDown/YouMusic
- https://github.com/Project-Elixir/RiMusic

Observed pattern:
- Search, playlists, persistent queue, offline songs, local library and background playback are treated as one music workflow.
- Audio normalization/equalization belongs to playback/post-processing settings, not the basic extraction gate.

InSave decision:
- Keep loudness processing OUT of the P0 download path until clean MP3 conversion is stable.
- Persistent queue/library is part of the product; extractor technical state is secondary.

## Recovery runtime policy

- APK size is not a release optimization target during recovery.
- Bundle/retain Python + yt-dlp runtime, FFmpeg and aria2c.
- Align youtubedl-android `library`, `ffmpeg` and `aria2c` to the same tested version.
- Disable minification/resource shrinking for Recovery builds.
- Only optimize size after physical-device P0 flows pass repeatedly.

## New blocking regression cases

1. Search -> first checkbox -> scroll -> more selections -> return -> all remain checked.
2. Playlist -> selected MP3 batch -> every item has distinct URL/job -> independent success/failure.
3. YouTube primary engine failure -> alternate local engine is attempted automatically.
4. WhatsApp -> Statuses -> automatic gallery with no picker after authorization.
5. WhatsApp Business -> same behavior independently.
6. Package/runtime update UI must not interrupt normal Home/Download flow.
7. No build may be called Stable because `assemble` passed.
