#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
OUT="$WORKSPACE/evidence/screens"
mkdir -p "$OUT"
PKG="com.deniscerri.ytdl"
ACT="com.deniscerri.ytdl.insave.InSaveHubActivity"

adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$PKG/$ACT" >/dev/null
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
label_norm = label.casefold().strip()
for node in root.iter('node'):
    text = node.attrib.get('text', '')
    desc = node.attrib.get('content-desc', '')
    for value in (text, desc):
        norm = value.casefold().strip()
        lines = [line.strip().casefold() for line in value.splitlines() if line.strip()]
        if norm == label_norm or label_norm in lines or label_norm in norm:
            b = node.attrib.get('bounds', '')
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
            if m:
                x1,y1,x2,y2 = map(int, m.groups())
                print((x1+x2)//2, (y1+y2)//2)
                raise SystemExit(0)
raise SystemExit(2)
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
    cls = node.attrib.get('class', '')
    if cls.endswith('EditText'):
        b = node.attrib.get('bounds', '')
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
        if m:
            x1,y1,x2,y2 = map(int, m.groups())
            print((x1+x2)//2, (y1+y2)//2)
            raise SystemExit(0)
raise SystemExit(2)
PY
)"
  read -r x y <<<"$coords"
  adb shell input tap "$x" "$y"
  sleep 1
}

capture "01-inicio"
dump_ui "01-inicio"

tap_text "Estados"
capture "02-estados-whatsapp-top"
dump_ui "02-estados-whatsapp-top"

# Prove that the grid moves past the initial six visible cards.
adb shell input swipe 540 1450 540 650 650
sleep 1
capture "03-estados-whatsapp-scroll"
dump_ui "03-estados-whatsapp-scroll"

# Return to the top, search one of the later fixtures, and capture the filtered count.
adb shell input swipe 540 650 540 1550 650
sleep 1
tap_first_edittext
adb shell input text 'insave-auto-test-12'
sleep 2
capture "04-estados-whatsapp-search"
dump_ui "04-estados-whatsapp-search"
grep -q 'Mostrando' "$OUT/04-estados-whatsapp-search.xml"

# Re-open Statuses to clear the local search field, then verify Business.
tap_text "Inicio"
tap_text "Estados"
tap_text "Business"
capture "05-estados-business"
dump_ui "05-estados-business"

tap_text "Descargas"
capture "06-descargas"
dump_ui "06-descargas"

tap_text "Seguidores"
capture "07-seguidores"
dump_ui "07-seguidores"

tap_text "Ajustes"
capture "08-ajustes"
dump_ui "08-ajustes"

# Back from a subview must navigate internally to Inicio instead of terminating.
adb shell input keyevent KEYCODE_BACK
sleep 2
test -n "$(adb shell pidof "$PKG" | tr -d '\r')"
capture "09-back-to-inicio"
dump_ui "09-back-to-inicio"
grep -qi 'Inicio' "$OUT/09-back-to-inicio.xml"

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

echo "InSave visual QA screenshots: PASS"
