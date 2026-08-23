#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
OUT="$WORKSPACE/evidence/screens"
mkdir -p "$OUT"
PKG="com.adelvis.insave.recovery"
ACT="com.deniscerri.ytdl.insave.InSaveHubActivity"

adb shell am force-stop "$PKG" || true
START_OUTPUT="$(adb shell am start -W -n "$PKG/$ACT")"
printf '%s\n' "$START_OUTPUT" | tee "$WORKSPACE/evidence/cold-start.txt"
sleep 2

capture() {
  local name="$1"
  adb exec-out screencap -p > "$OUT/$name.png"
  test -s "$OUT/$name.png"
}

dump_ui() {
  local name="$1"
  adb shell uiautomator dump /sdcard/insave-window.xml >/dev/null
  adb pull /sdcard/insave-window.xml "$OUT/$name.xml" >/dev/null
  test -s "$OUT/$name.xml"
}

tap_text() {
  local label="$1"
  local xml="/tmp/insave-window.xml"
  adb shell uiautomator dump /sdcard/insave-window.xml >/dev/null
  adb pull /sdcard/insave-window.xml "$xml" >/dev/null
  local coords
  coords="$(python3 - "$xml" "$label" <<'PY'
import re, sys, xml.etree.ElementTree as ET
path, label = sys.argv[1], sys.argv[2]
root = ET.parse(path).getroot()
needle = label.casefold().strip()
for node in root.iter('node'):
    values = [node.attrib.get('text', ''), node.attrib.get('content-desc', '')]
    for value in values:
        norm = value.casefold().strip()
        lines = [line.strip().casefold() for line in value.splitlines() if line.strip()]
        if norm == needle or needle in lines or needle in norm:
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.attrib.get('bounds', ''))
            if m:
                x1,y1,x2,y2 = map(int, m.groups())
                print((x1+x2)//2, (y1+y2)//2)
                raise SystemExit(0)
raise SystemExit(f'UI label not found: {label}')
PY
)"
  read -r x y <<<"$coords"
  adb shell input tap "$x" "$y"
  sleep 2
}

tap_first_edittext() {
  local xml="/tmp/insave-window.xml"
  adb shell uiautomator dump /sdcard/insave-window.xml >/dev/null
  adb pull /sdcard/insave-window.xml "$xml" >/dev/null
  local coords
  coords="$(python3 - "$xml" <<'PY'
import re, sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
for node in root.iter('node'):
    if node.attrib.get('class', '').endswith('EditText'):
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.attrib.get('bounds', ''))
        if m:
            x1,y1,x2,y2 = map(int, m.groups())
            print((x1+x2)//2, (y1+y2)//2)
            raise SystemExit(0)
raise SystemExit('no EditText found')
PY
)"
  read -r x y <<<"$coords"
  adb shell input tap "$x" "$y"
  sleep 1
}

capture "01-inicio"
dump_ui "01-inicio"
grep -qi 'Inicio' "$OUT/01-inicio.xml"

tap_text "Estados"
capture "02-estados-whatsapp-top"
dump_ui "02-estados-whatsapp-top"
grep -qi 'Buscar estados' "$OUT/02-estados-whatsapp-top.xml"
grep -qi 'insave-auto-test' "$OUT/02-estados-whatsapp-top.xml"

# Capture the concrete visible fixture set before and after scroll. The scroll passes only
# when the RecyclerView exposes a different set, not merely because a swipe event occurred.
python3 - "$OUT/02-estados-whatsapp-top.xml" > "$OUT/top-status-items.txt" <<'PY'
import re, sys
s=open(sys.argv[1], encoding='utf-8').read()
for x in sorted(set(re.findall(r'insave-auto-test(?:-\d+)?\.jpg', s))): print(x)
PY
test -s "$OUT/top-status-items.txt"

adb shell input swipe 540 1500 540 600 700
sleep 1
capture "03-estados-whatsapp-scroll"
dump_ui "03-estados-whatsapp-scroll"
python3 - "$OUT/03-estados-whatsapp-scroll.xml" > "$OUT/scrolled-status-items.txt" <<'PY'
import re, sys
s=open(sys.argv[1], encoding='utf-8').read()
for x in sorted(set(re.findall(r'insave-auto-test(?:-\d+)?\.jpg', s))): print(x)
PY
test -s "$OUT/scrolled-status-items.txt"
if cmp -s "$OUT/top-status-items.txt" "$OUT/scrolled-status-items.txt"; then
  echo 'Status RecyclerView did not expose a different item set after scroll' >&2
  exit 1
fi

# Search a known fixture outside the first visual page. This proves the full backing set remains searchable.
adb shell input swipe 540 650 540 1550 650
sleep 1
tap_first_edittext
adb shell input text 'insave-auto-test-12'
sleep 2
capture "04-estados-whatsapp-search"
dump_ui "04-estados-whatsapp-search"
grep -qi 'insave-auto-test-12' "$OUT/04-estados-whatsapp-search.xml"
grep -qi 'Mostrando' "$OUT/04-estados-whatsapp-search.xml"

# IME consumes first Back; close it before bottom navigation.
adb shell input keyevent KEYCODE_BACK
sleep 1

tap_text "Inicio"
tap_text "Estados"
tap_text "Business"
capture "05-estados-business"
dump_ui "05-estados-business"
grep -qi 'insave-auto-business-test' "$OUT/05-estados-business.xml"

tap_text "Descargas"
capture "06-descargas"
dump_ui "06-descargas"

tap_text "Seguidores"
capture "07-seguidores"
dump_ui "07-seguidores"

tap_text "Ajustes"
capture "08-ajustes"
dump_ui "08-ajustes"

# App-level back: process must stay alive and the shell must navigate back to Inicio.
PID_BEFORE="$(adb shell pidof "$PKG" | tr -d '\r')"
test -n "$PID_BEFORE"
adb shell input keyevent KEYCODE_BACK
sleep 2
PID_AFTER="$(adb shell pidof "$PKG" | tr -d '\r')"
test -n "$PID_AFTER"
capture "09-back-to-inicio"
dump_ui "09-back-to-inicio"
grep -qi 'Inicio' "$OUT/09-back-to-inicio.xml"
printf 'pid_before=%s\npid_after=%s\n' "$PID_BEFORE" "$PID_AFTER" > "$WORKSPACE/evidence/back-navigation-process.txt"

# Emulator startup is noisy, so record it as a measured quality metric. A pathological 10s+
# cold launch is still a hard regression and must block this QA line.
TOTAL_TIME="$(printf '%s\n' "$START_OUTPUT" | sed -n 's/.*TotalTime: \([0-9][0-9]*\).*/\1/p' | tail -1)"
if [ -n "$TOTAL_TIME" ]; then
  echo "cold_start_total_ms=$TOTAL_TIME" >> "$WORKSPACE/evidence/cold-start.txt"
  test "$TOTAL_TIME" -lt 10000
fi

printf '%s\n' \
  '01-inicio.png' \
  '02-estados-whatsapp-top.png' \
  '03-estados-whatsapp-scroll.png' \
  '04-estados-whatsapp-search.png' \
  '05-estados-business.png' \
  '06-descargas.png' \
  '07-seguidores.png' \
  '08-ajustes.png' \
  '09-back-to-inicio.png' > "$OUT/manifest.txt"

echo 'InSave v0.18 visual QA screenshots/navigation: PASS'
