#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UPSTREAM_INPUT="${1:-$ROOT/../upstream}"
UPSTREAM="$(cd "$UPSTREAM_INPUT" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"

"$ROOT/insave-build/v0181/reconstruct_v0181_heavy.sh" "$UPSTREAM"
cd "$WORKSPACE"

# Use the approved neon InSave artwork supplied by the user. This 256x256 WebP
# is a launcher-only derivative of that exact logo (symbol crop, no legacy
# YTDLnis art). It is committed as a real binary, avoiding the malformed JPEG
# and split-base64 path used by the earlier attempt.
LAUNCHER_SRC="$ROOT/insave-build/v0182/insave_launcher_256.webp"
LAUNCHER="$UPSTREAM/app/src/main/res/drawable-nodpi/insave_launcher.webp"
EXPECTED_SHA="260f8149109e566c19dd8a06e2b94684b1e9a81c4a8fca6b9e5effd798868319"
mkdir -p "$(dirname "$LAUNCHER")"
test -s "$LAUNCHER_SRC"
cp "$LAUNCHER_SRC" "$LAUNCHER"
echo "$EXPECTED_SHA  $LAUNCHER" | sha256sum -c -

# Validate the RIFF/WEBP envelope and VP8 dimensions without relying on optional
# image libraries on the CI host. Android's resource compiler will perform its
# own decode during assemble as the second independent check.
python3 - "$LAUNCHER" <<'PY'
from pathlib import Path
import struct, sys
p = Path(sys.argv[1])
b = p.read_bytes()
assert len(b) > 20, 'launcher too small'
assert b[:4] == b'RIFF' and b[8:12] == b'WEBP', 'not a WebP RIFF image'
chunk = b[12:16]
assert chunk in {b'VP8 ', b'VP8L', b'VP8X'}, f'unexpected WebP chunk {chunk!r}'
if chunk == b'VP8 ':
    # Lossy VP8 frame header: 3-byte frame tag then 9d 01 2a and 14-bit WxH.
    payload = 20
    assert b[payload+3:payload+6] == b'\x9d\x01\x2a', 'invalid VP8 key-frame signature'
    w = struct.unpack_from('<H', b, payload+6)[0] & 0x3fff
    h = struct.unpack_from('<H', b, payload+8)[0] & 0x3fff
    assert (w, h) == (256, 256), f'unexpected launcher size {w}x{h}'
print('InSave approved WebP launcher structure: PASS 256x256')
PY

python3 -m py_compile "$ROOT/insave-build/v0182/apply_v0182_launcher_logo.py"
python3 "$ROOT/insave-build/v0182/apply_v0182_launcher_logo.py"

MANIFEST="$UPSTREAM/app/src/main/AndroidManifest.xml"
BUILD="$UPSTREAM/app/build.gradle"

test -s "$LAUNCHER"
grep -q 'versionCode 18200' "$BUILD"
grep -q 'versionName "0.18.2-Launcher-Logo-QA"' "$BUILD"

for NAME in '.Default' '.DarkIcon' '.LightIcon' '.BlueIcon' '.GreenIcon'; do
  python3 - "$MANIFEST" "$NAME" <<'PY'
from pathlib import Path
import re, sys
p=Path(sys.argv[1]); name=sys.argv[2]; s=p.read_text()
m=re.search(r'<activity-alias\b(?=[^>]*android:name="'+re.escape(name)+r'")[^>]*>', s, re.S)
if not m: raise SystemExit(f'missing alias {name}')
tag=m.group(0)
assert 'android:icon="@drawable/insave_launcher"' in tag, tag
assert 'android:roundIcon="@drawable/insave_launcher"' in tag, tag
assert '@mipmap/ic_launcher' not in tag, tag
assert '@drawable/insave_logo' not in tag, tag
PY
done

grep -q 'android:icon="@drawable/insave_launcher"' "$MANIFEST"
grep -q 'android:roundIcon="@drawable/insave_launcher"' "$MANIFEST"

echo 'InSave v0.18.2 validated launcher branding reconstruction: PASS'
