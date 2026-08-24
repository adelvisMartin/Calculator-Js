#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UPSTREAM_INPUT="${1:-$ROOT/../upstream}"
UPSTREAM="$(cd "$UPSTREAM_INPUT" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"

"$ROOT/insave-build/v0181/reconstruct_v0181_heavy.sh" "$UPSTREAM"
cd "$WORKSPACE"

# v0.17.2 carried a compact derivative that was accepted by aapt but is not a
# fully decodable JPEG. Reconstruct the exact approved full artwork from its
# original split base64 source before wiring it to Android launcher aliases.
LOGO="$UPSTREAM/app/src/main/res/drawable-nodpi/insave_logo.jpg"
mkdir -p "$(dirname "$LOGO")"
cat \
  "$ROOT/insave-build/v0172/insave_app_icon.jpg.b64" \
  "$ROOT/insave-build/v0172/insave_app_icon.jpg.b64.01" \
  "$ROOT/insave-build/v0172/insave_app_icon.jpg.b64.02" \
  "$ROOT/insave-build/v0172/insave_app_icon.jpg.b64.03" \
  | tr -d '\r\n' | base64 -d > "$LOGO"

# Validate actual decode, not only JPEG magic bytes. JDK ImageIO is available in
# the same environment used for Android compilation and catches malformed SOS/
# SOF structures that the previous lightweight check missed.
cat > /tmp/InSaveLogoCheck.java <<'JAVA'
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
public final class InSaveLogoCheck {
  public static void main(String[] args) throws Exception {
    BufferedImage image = ImageIO.read(new File(args[0]));
    if (image == null) throw new IllegalStateException("InSave logo is not decodable");
    if (image.getWidth() < 192 || image.getHeight() < 192) {
      throw new IllegalStateException("InSave logo is too small: " + image.getWidth() + "x" + image.getHeight());
    }
    System.out.println("InSave approved logo decode: PASS " + image.getWidth() + "x" + image.getHeight());
  }
}
JAVA
javac /tmp/InSaveLogoCheck.java
java -cp /tmp InSaveLogoCheck "$LOGO"

python3 -m py_compile "$ROOT/insave-build/v0182/apply_v0182_launcher_logo.py"
python3 "$ROOT/insave-build/v0182/apply_v0182_launcher_logo.py"

MANIFEST="$UPSTREAM/app/src/main/AndroidManifest.xml"
BUILD="$UPSTREAM/app/build.gradle"

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
