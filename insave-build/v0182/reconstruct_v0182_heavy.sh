#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UPSTREAM_INPUT="${1:-$ROOT/../upstream}"
UPSTREAM="$(cd "$UPSTREAM_INPUT" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"

"$ROOT/insave-build/v0181/reconstruct_v0181_heavy.sh" "$UPSTREAM"
cd "$WORKSPACE"
python3 -m py_compile "$ROOT/insave-build/v0182/apply_v0182_launcher_logo.py"
python3 "$ROOT/insave-build/v0182/apply_v0182_launcher_logo.py"

MANIFEST="$UPSTREAM/app/src/main/AndroidManifest.xml"
BUILD="$UPSTREAM/app/build.gradle"
LOGO="$UPSTREAM/app/src/main/res/drawable-nodpi/insave_logo.jpg"

test -s "$LOGO"
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
assert 'android:icon="@drawable/insave_logo"' in tag, tag
assert 'android:roundIcon="@drawable/insave_logo"' in tag, tag
assert '@mipmap/ic_launcher' not in tag, tag
PY
done

grep -q 'android:icon="@drawable/insave_logo"' "$MANIFEST"
grep -q 'android:roundIcon="@drawable/insave_logo"' "$MANIFEST"

echo 'InSave v0.18.2 launcher branding reconstruction: PASS'
