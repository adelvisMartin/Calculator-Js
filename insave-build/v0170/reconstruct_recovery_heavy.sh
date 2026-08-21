#!/usr/bin/env bash
set -euo pipefail

# Script lives at <overlay>/insave-build/v0170/. Two parents up is the overlay repo root.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OVERLAY="$ROOT"
UPSTREAM_INPUT="${1:-$ROOT/../upstream}"
UPSTREAM="$(cd "$UPSTREAM_INPUT" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"

chmod +x "$UPSTREAM/gradlew"
touch "$UPSTREAM/local.properties" "$UPSTREAM/keystore.properties"
mkdir -p "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave"
cat "$OVERLAY"/insave-build/v0161/InSaveHubActivity.part* > "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt"

cd "$WORKSPACE"
python3 "$OVERLAY/insave-build/v0162/remove_broad_storage.py"
for f in "$OVERLAY"/insave-build/v0162/apply_v0162.py.b64.*; do base64 -d "$f"; done > /tmp/apply_v0162.py
python3 -m py_compile /tmp/apply_v0162.py
python3 /tmp/apply_v0162.py
python3 "$OVERLAY/insave-build/v0162/normalize_after_patch.py"

# Provider B dynamic per-video PO token support. This reuses the maintained
# NewPipe/BotGuard provider but injects the freshly generated Player/GVS tokens
# into yt-dlp itself, without making cookies/login mandatory.
python3 -m py_compile "$OVERLAY/insave-build/v0163/apply_v0163.py"
python3 "$OVERLAY/insave-build/v0163/apply_v0163.py"

python3 "$OVERLAY/insave-build/v0170/normalize_status_function.py"
cp "$OVERLAY/insave-build/v0170/AutomaticStatusRepository.kt" "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/"
python3 -m py_compile "$OVERLAY/insave-build/v0170/apply_v0170.py" "$OVERLAY/insave-build/v0170/post_v0170_compile_fixes.py"
python3 "$OVERLAY/insave-build/v0170/apply_v0170.py"
python3 "$OVERLAY/insave-build/v0170/post_v0170_compile_fixes.py"

cp "$OVERLAY/insave-build/v0170/InSaveCobaltResolver.kt" "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/"
python3 -m py_compile "$OVERLAY/insave-build/v0170/apply_remote_fallback.py"
python3 "$OVERLAY/insave-build/v0170/apply_remote_fallback.py"

cp "$OVERLAY/insave-build/v0170/InSavePlaylistPolicy.kt" "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/"
python3 -m py_compile "$OVERLAY/insave-build/v0170/apply_playlist_mp3.py"
python3 "$OVERLAY/insave-build/v0170/apply_playlist_mp3.py"

# Final P0 provider order correction: A(NewPipe) -> B(local yt-dlp + dynamic PO)
# -> C(optional self-hosted Cobalt only after B throws).
python3 -m py_compile "$OVERLAY/insave-build/v0170/apply_youtube_p0.py"
python3 "$OVERLAY/insave-build/v0170/apply_youtube_p0.py"

python3 -m py_compile "$OVERLAY/insave-build/v0170/apply_provider_settings.py"
python3 "$OVERLAY/insave-build/v0170/apply_provider_settings.py"
python3 -m py_compile "$OVERLAY/insave-build/v0170/apply_brand_paths.py"
python3 "$OVERLAY/insave-build/v0170/apply_brand_paths.py"

python3 - "$UPSTREAM/app/build.gradle" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
s=s.replace('implementation "io.github.junkfood02.youtubedl-android:ffmpeg:0.17.2"', 'implementation "io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1"')
s=s.replace('//implementation "io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1"', 'implementation "io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1"')
s=s.replace('minifyEnabled true', 'minifyEnabled false', 1)
s=s.replace('shrinkResources true', 'shrinkResources false', 1)
# Recovery Heavy intentionally keeps all four ABIs plus universal APK.
s=s.replace("include 'arm64-v8a'", "include 'x86', 'x86_64', 'armeabi-v7a', 'arm64-v8a'")
s=s.replace('universalApk false', 'universalApk true')
p.write_text(s)
PY

# Contract gates: heavy runtime + product recovery + playlist MP3 + branded storage.
grep -q 'library:0.18.1' "$UPSTREAM/app/build.gradle"
grep -q 'ffmpeg:0.18.1' "$UPSTREAM/app/build.gradle"
grep -q 'aria2c:0.18.1' "$UPSTREAM/app/build.gradle"
grep -q "include 'x86', 'x86_64', 'armeabi-v7a', 'arm64-v8a'" "$UPSTREAM/app/build.gradle"
grep -q 'universalApk true' "$UPSTREAM/app/build.gradle"
grep -q 'minifyEnabled false' "$UPSTREAM/app/build.gradle"
grep -q 'shrinkResources false' "$UPSTREAM/app/build.gradle"
grep -q 'MANAGE_EXTERNAL_STORAGE' "$UPSTREAM/app/src/main/AndroidManifest.xml"
grep -q 'AutomaticStatusRepository().scan' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt"
grep -q 'resolveInSaveYoutubeAudioDirectUrl' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'getWebClientPoToken(videoId)' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'web.player+' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'web.gvs+' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
! grep -q 'poTokens.isNotEmpty() && sharedPreferences.getBoolean("use_cookies"' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'resolveInSaveCobaltFallbackUrl' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'recoverCatching { providerBError' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/work/download/DownloadWorker.kt"
grep -q 'Provider B failed; retrying optional Provider C' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/work/download/DownloadWorker.kt"
grep -q 'MAX_BATCH_ITEMS = 50' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/InSavePlaylistPolicy.kt"
grep -q 'request.addOption("--audio-format", "mp3")' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'normalizedAudioBitrate' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'InSave/Audio' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/FileUtil.kt"
grep -q 'InSave/Video' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/FileUtil.kt"
! grep -q 'YTDLnis/Audio' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/FileUtil.kt"
! grep -q 'YTDLnis/Video' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/FileUtil.kt"
! grep -R -q 'loudnorm=I=-11' "$UPSTREAM/app/src/main/java"

echo 'InSave Recovery Heavy canonical reconstruction: PASS'
