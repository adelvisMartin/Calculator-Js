#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$WORKSPACE/upstream"

adb wait-for-device
READY="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')"
test "$READY" = "1"

TARGET_APK="$(find app/build/outputs/apk/github/debug -type f -name '*universal*.apk' | head -1)"
test -n "$TARGET_APK"
echo "E2E APK: $TARGET_APK"
adb install -r "$TARGET_APK"
adb shell appops set com.deniscerri.ytdl MANAGE_EXTERNAL_STORAGE allow

adb shell mkdir -p '/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses'
adb shell mkdir -p '/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses'
printf 'fake-jpeg-for-discovery' > /tmp/insave-auto-test.jpg
printf 'fake-mp4-for-discovery' > /tmp/insave-auto-business-test.mp4
adb push /tmp/insave-auto-test.jpg '/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses/insave-auto-test.jpg'
adb push /tmp/insave-auto-business-test.mp4 '/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses/insave-auto-business-test.mp4'

mkdir -p "$WORKSPACE/evidence"
LOG="$WORKSPACE/evidence/android-p0-e2e.log"
if ! ./gradlew --no-daemon :app:connectedGithubDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.deniscerri.ytdl.insave.InSaveRecoveryInstrumentedTest \
  > "$LOG" 2>&1; then
  cat "$LOG"
  exit 1
fi
cat "$LOG"

cat > "$WORKSPACE/evidence/P0-PASS.txt" <<'EOF'
android_status_auto_e2e=pass
android_youtube_mp3_e2e=pass
android_playlist_mp3_e2e=pass
EOF

echo 'InSave Android P0 gates: PASS'
