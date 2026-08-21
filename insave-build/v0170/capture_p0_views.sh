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
for node in root.iter('node'):
    text = node.attrib.get('text', '')
    desc = node.attrib.get('content-desc', '')
    if text == label or desc == label:
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

capture "01-inicio"
tap_text "Estados"
capture "02-estados-whatsapp"
tap_text "Business"
capture "03-estados-business"
tap_text "Descargas"
capture "04-descargas"
tap_text "Seguidores"
capture "05-seguidores"
tap_text "Ajustes"
capture "06-ajustes"

printf '%s\n' \
  '01-inicio.png' \
  '02-estados-whatsapp.png' \
  '03-estados-business.png' \
  '04-descargas.png' \
  '05-seguidores.png' \
  '06-ajustes.png' > "$OUT/manifest.txt"

echo "InSave visual QA screenshots: PASS"
