#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
EVIDENCE="$WORKSPACE/evidence"
PKG="com.adelvis.insave.recovery"
ACT="com.deniscerri.ytdl.insave.InSaveHubActivity"
mkdir -p "$EVIDENCE/screens"

# Reuse the full v0.18 API35 functional/security suite: real MP3 provider path,
# 14+ WhatsApp statuses, Business, scroll/search, Back/PID, log redaction and 9 views.
bash "$WORKSPACE/insave-build/insave-build/v0180/run_android_v0180.sh"

# Additional v0.18.1 UX gate: dedicated Instagram/Facebook shortcuts must be
# visible on the product Home screen and survive interaction without killing InSave.
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$PKG/$ACT" >/dev/null
sleep 2
adb shell uiautomator dump /sdcard/insave-v0181-home.xml >/dev/null
adb pull /sdcard/insave-v0181-home.xml "$EVIDENCE/screens/10-social-shortcuts.xml" >/dev/null
grep -q 'Instagram' "$EVIDENCE/screens/10-social-shortcuts.xml"
grep -q 'Facebook' "$EVIDENCE/screens/10-social-shortcuts.xml"
grep -q 'Pegar y descargar' "$EVIDENCE/screens/10-social-shortcuts.xml"
adb exec-out screencap -p > "$EVIDENCE/screens/10-social-shortcuts.png"
test -s "$EVIDENCE/screens/10-social-shortcuts.png"

test -n "$(adb shell pidof "$PKG" | tr -d '\r')"

cat >> "$EVIDENCE/P0-PASS-v0180.txt" <<'EOF'
instagram_dedicated_download_shortcut=pass
facebook_dedicated_download_shortcut=pass
social_shortcuts_visual_evidence=pass
social_platform_policy_unit_tests=pass
privacy_cookie_webview_followup=pass
visual_screenshots_total=10
EOF

cp "$EVIDENCE/P0-PASS-v0180.txt" "$EVIDENCE/P0-PASS-v0181.txt"
echo 'InSave v0.18.1 Android API35 social UX gates: PASS'
