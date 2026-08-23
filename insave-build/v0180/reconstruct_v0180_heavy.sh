#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UPSTREAM_INPUT="${1:-$ROOT/../upstream}"
UPSTREAM="$(cd "$UPSTREAM_INPUT" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"

"$ROOT/insave-build/v0170/reconstruct_recovery_heavy.sh" "$UPSTREAM"

cd "$WORKSPACE"
python3 -m py_compile "$ROOT/insave-build/v0180/apply_v0180_hardening.py"
python3 "$ROOT/insave-build/v0180/apply_v0180_hardening.py"

# v0.18 hardening contracts. Runtime behavior is validated separately by Android E2E.
grep -q "include ':app'" "$UPSTREAM/settings.gradle"
! grep -q "':common'" "$UPSTREAM/settings.gradle"
! grep -q 'accompanist-webview' "$UPSTREAM/app/build.gradle"
grep -q 'INSAVE_KEYSTORE_PATH' "$UPSTREAM/app/build.gradle"
grep -q 'signingConfigs.insaveRelease' "$UPSTREAM/app/build.gradle"
! sed -n '/release {/,/debug {/p' "$UPSTREAM/app/build.gradle" | grep -q 'signingConfigs.debug'
grep -q 'play {' "$UPSTREAM/app/build.gradle"
grep -q 'tools:node="remove"' "$UPSTREAM/app/src/play/AndroidManifest.xml"
grep -q 'MANAGE_EXTERNAL_STORAGE' "$UPSTREAM/app/src/play/AndroidManifest.xml"
grep -q 'android:usesCleartextTraffic="false"' "$UPSTREAM/app/src/main/AndroidManifest.xml"
grep -q 'InSaveInputPolicy.classify(rawInput)' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt"
grep -q 'InSaveInputPolicy.normalizeHttpUrl(extractedUrl)' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/receiver/ShareActivity.kt"
grep -q 'anonymousYoutubeFallbackClients' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/work/download/DownloadWorker.kt"
grep -q 'inSaveYoutubeClientOverride' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt"
grep -q 'InSaveRedactor.redact(line)' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/work/download/DownloadWorker.kt"
! grep -q 'playerPot=\$playerPot' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/newpipe/potoken/NewPipePoTokenGenerator.kt"
! grep -q 'poToken=\$poToken' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/util/extractors/newpipe/potoken/PoTokenWebView.kt"
grep -q 'webview_native' "$UPSTREAM/app/src/main/res/layout/webview_potoken_activity.xml"
grep -q 'RoomWarnings.QUERY_MISMATCH' "$UPSTREAM/app/src/main/java/com/deniscerri/ytdl/database/dao/TerminalDao.kt"

echo 'InSave v0.18.0 hardened reconstruction: PASS'
