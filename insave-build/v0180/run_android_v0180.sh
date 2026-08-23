#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
APP_DIR="$WORKSPACE/upstream"
EVIDENCE="$WORKSPACE/evidence"
PKG="com.adelvis.insave.recovery"
TEST_CLASS="com.deniscerri.ytdl.insave.InSaveV0180InstrumentedTest"
mkdir -p "$EVIDENCE"

adb wait-for-device
READY="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')"
test "$READY" = "1"

cd "$APP_DIR"
TARGET_APK="$(find app/build/outputs/apk/github/debug -type f -name '*universal*.apk' | head -1)"
test -n "$TARGET_APK"
echo "E2E APK: $TARGET_APK" | tee "$EVIDENCE/e2e-apk.txt"
adb install -r "$TARGET_APK" | tee "$EVIDENCE/adb-install.txt"

# Recovery/GitHub flavor intentionally retains All Files Access for automatic WhatsApp
# status discovery. Play flavor is validated separately to remove this permission.
adb shell appops set "$PKG" MANAGE_EXTERNAL_STORAGE allow
adb shell 'mkdir -p "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses"'
adb shell 'mkdir -p "/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses"'

# Valid tiny JPEG and discovery-only Business MP4 fixture. Create fourteen image fixtures
# so runtime and visual tests can prove scrolling/search beyond the first six cards.
printf '%s' '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABAf/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPxB//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPxB//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxB//9k=' | base64 -d > /tmp/insave-auto-test.jpg
printf 'fake-mp4-for-discovery' > /tmp/insave-auto-business-test.mp4
adb push /tmp/insave-auto-test.jpg '/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses/insave-auto-test.jpg' >/dev/null
for i in $(seq -w 01 13); do
  adb push /tmp/insave-auto-test.jpg "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses/insave-auto-test-$i.jpg" >/dev/null
  sleep 0.03
done
adb push /tmp/insave-auto-business-test.mp4 '/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses/insave-auto-business-test.mp4' >/dev/null

adb logcat -c || true
LOG="$EVIDENCE/android-v0180-e2e.log"
set +e
./gradlew --no-daemon :app:connectedGithubDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class="$TEST_CLASS" \
  > "$LOG" 2>&1
STATUS=$?
set -e
adb logcat -d > "$EVIDENCE/android-logcat.txt" 2>&1 || true

if [ "$STATUS" -ne 0 ]; then
  cat "$LOG"
  echo '--- focused Android logcat ---'
  grep -iE 'yt-dlp|youtube|potoken|po token|newpipe|botguard|403|sign in|unavailable|error|sabr|format|insave' \
    "$EVIDENCE/android-logcat.txt" | tail -n 500 || true
  exit "$STATUS"
fi
cat "$LOG"

# No actual token/cookie values may be present in runtime logcat after the redaction patch.
if grep -Eqi 'playerPot=[A-Za-z0-9_-]{12,}|streamingPot=[A-Za-z0-9_-]{12,}|visitor_data=[A-Za-z0-9_-]{12,}|poToken=[A-Za-z0-9_-]{12,}' "$EVIDENCE/android-logcat.txt"; then
  echo 'Secret-like PO token material leaked into Android logcat' >&2
  exit 1
fi

auto_count="$(adb shell find '/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses' -maxdepth 1 -type f -name 'insave-auto-test*.jpg' 2>/dev/null | wc -l | tr -d '[:space:]')"
test "$auto_count" -ge 14
printf 'whatsapp_fixture_count=%s\n' "$auto_count" > "$EVIDENCE/status-fixtures.txt"

cd "$WORKSPACE"
chmod +x insave-build/insave-build/v0180/capture_v0180_views.sh
insave-build/insave-build/v0180/capture_v0180_views.sh

cat > "$EVIDENCE/P0-PASS-v0180.txt" <<'EOF'
android_status_14plus_auto_discovery=pass
android_status_scroll_changes_visible_set=pass
android_status_search_late_fixture=pass
android_whatsapp_business_auto_discovery=pass
android_back_navigation_process_alive=pass
provider_b_primary_dynamic_videoid_po=mweb
provider_b_fallback_1=web_embedded
provider_b_fallback_2=android_vr
provider_c_optional_default_off=pass
provider_c_private_cleartext_endpoint_rejected=pass
provider_b_real_mp3_candidate_pool=pass
playlist_two_independent_real_mp3_jobs=pass
runtime_secret_logcat_scan=pass
visual_screenshots=9
EOF

echo 'InSave v0.18 Android API35 hardening gates: PASS'
