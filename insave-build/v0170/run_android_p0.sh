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

adb shell 'mkdir -p "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses"'
adb shell 'mkdir -p "/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses"'

# Valid tiny JPEG for visual/status discovery instead of an invalid placeholder.
printf '%s' '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABAf/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPxB//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPxB//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxB//9k=' | base64 -d > /tmp/insave-auto-test.jpg
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

cd "$WORKSPACE"
chmod +x insave-build/insave-build/v0170/capture_p0_views.sh
insave-build/insave-build/v0170/capture_p0_views.sh

cat > "$WORKSPACE/evidence/P0-PASS.txt" <<'EOF'
android_status_auto_e2e=pass
provider_chain_A_then_B_mp3=pass
provider_B_dynamic_videoid_po_mp3=pass
android_playlist_mp3_independent_jobs=pass
provider_C_optional_default_off=pass
visual_views_capture=pass
EOF

echo 'InSave Android P0 gates: PASS'
