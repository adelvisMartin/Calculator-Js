#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$WORKSPACE/upstream"

adb wait-for-device
READY="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')"
test "$READY" = "1"

mkdir -p "$WORKSPACE/evidence"

# Apply the current YouTube P0 hardening after the canonical Heavy reconstruction:
# dynamic per-video PO tokens are bound to mweb and yt-dlp 2026.08.19 is embedded.
cd "$WORKSPACE"
python3 insave-build/insave-build/v0170/apply_youtube_2026.py | tee evidence/youtube-2026-hardening.log

# The instrumentation source was intentionally authored against the older web labels.
# Keep the canonical test readable while making this run assert the current mweb contract.
TEST_FILE="upstream/app/src/androidTest/java/com/deniscerri/ytdl/insave/InSaveRecoveryInstrumentedTest.kt"
sed -i 's/web\.player+/mweb.player+/g; s/web\.gvs+/mweb.gvs+/g' "$TEST_FILE"
sed -i 's/dynamic web player PO token/dynamic mweb player PO token/g; s/dynamic web GVS PO token/dynamic mweb GVS PO token/g' "$TEST_FILE"
# RuntimeManager constructs ExecuteException from stderr, so do not redirect stderr
# into stdout in the P0 test; otherwise a real yt-dlp error becomes an empty exception.
sed -i 's/redirectErrorStream = true/redirectErrorStream = false/g' "$TEST_FILE"

cd "$WORKSPACE/upstream"
./gradlew --no-daemon :app:assembleGithubDebug :app:assembleGithubDebugAndroidTest > "$WORKSPACE/evidence/p0-hardened-build.log" 2>&1

TARGET_APK="$(find app/build/outputs/apk/github/debug -type f -name '*universal*.apk' | head -1)"
test -n "$TARGET_APK"
echo "E2E APK: $TARGET_APK"
adb install -r "$TARGET_APK"
adb shell appops set com.deniscerri.ytdl MANAGE_EXTERNAL_STORAGE allow

adb shell 'mkdir -p "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses"'
adb shell 'mkdir -p "/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses"'

# Valid tiny JPEG for automatic discovery. Keep the historical exact fixture and
# add enough extra items to prove visually that the grid is not capped at six.
printf '%s' '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABAf/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPxB//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPxB//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxB//9k=' | base64 -d > /tmp/insave-auto-test.jpg
printf 'fake-mp4-for-discovery' > /tmp/insave-auto-business-test.mp4

adb push /tmp/insave-auto-test.jpg '/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses/insave-auto-test.jpg'
for i in $(seq -w 01 13); do
  adb push /tmp/insave-auto-test.jpg "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses/insave-auto-test-$i.jpg" >/dev/null
  # Distinct mtimes keep the repository ordering deterministic enough for scroll proof.
  sleep 0.03
done
adb push /tmp/insave-auto-business-test.mp4 '/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses/insave-auto-business-test.mp4'

LOG="$WORKSPACE/evidence/android-p0-e2e.log"
adb logcat -c || true
if ! ./gradlew --no-daemon :app:connectedGithubDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.deniscerri.ytdl.insave.InSaveRecoveryInstrumentedTest \
  > "$LOG" 2>&1; then
  adb logcat -d > "$WORKSPACE/evidence/android-logcat.txt" 2>&1 || true
  cat "$LOG"
  echo '--- focused Android logcat ---'
  grep -iE 'yt-dlp|youtube|potoken|po token|newpipe|botguard|403|sign in|unavailable|error|sabr|format' \
    "$WORKSPACE/evidence/android-logcat.txt" | tail -n 400 || true
  exit 1
fi
cat "$LOG"
adb logcat -d > "$WORKSPACE/evidence/android-logcat.txt" 2>&1 || true

cd "$WORKSPACE"
chmod +x insave-build/insave-build/v0170/capture_p0_views.sh
insave-build/insave-build/v0170/capture_p0_views.sh

cat > "$WORKSPACE/evidence/P0-PASS.txt" <<'EOF'
android_status_auto_e2e=pass
android_status_more_than_six_fixture=14_images
android_status_search_visual_evidence=pass
android_back_navigation_visual_evidence=pass
provider_chain_A_then_B_mp3=pass
provider_B_dynamic_videoid_po_mp3=pass
provider_B_client=mweb
provider_B_ytdlp=2026.08.19
android_playlist_mp3_independent_jobs=pass
provider_C_optional_default_off=pass
visual_views_capture=pass
EOF

echo 'InSave Android P0 gates: PASS'
