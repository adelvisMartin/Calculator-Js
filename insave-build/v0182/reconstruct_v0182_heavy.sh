#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UPSTREAM_INPUT="${1:-$ROOT/../upstream}"
UPSTREAM="$(cd "$UPSTREAM_INPUT" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"

"$ROOT/insave-build/v0181/reconstruct_v0181_heavy.sh" "$UPSTREAM"
cd "$WORKSPACE"

# Use the real approved neon InSave artwork supplied for this project. This
# 512x512 launcher derivative was generated from that source, not from the old
# YTDLnis launcher icon. Keep it as a binary asset in the overlay so no fragile
# split-base64 reconstruction can corrupt it again.
LAUNCHER_SRC="$ROOT/insave-build/v0182/insave_launcher_512.jpg"
LAUNCHER="$UPSTREAM/app/src/main/res/drawable-nodpi/insave_launcher.jpg"
mkdir -p "$(dirname "$LAUNCHER")"
test -s "$LAUNCHER_SRC"
cp "$LAUNCHER_SRC" "$LAUNCHER"

# Decode the exact file before Android compilation. This rejects malformed JPEG
# structures even when a resource packager would otherwise accept raw bytes.
cat > /tmp/InSaveLogoCheck.java <<'JAVA'
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
public final class InSaveLogoCheck {
  public static void main(String[] args) throws Exception {
    BufferedImage image = ImageIO.read(new File(args[0]));
    if (image == null) throw new IllegalStateException("InSave launcher is not decodable");
    if (image.getWidth() != 512 || image.getHeight() != 512) {
      throw new IllegalStateException("Unexpected InSave launcher size: " + image.getWidth() + "x" + image.getHeight());
    }
    System.out.println("InSave approved launcher decode: PASS " + image.getWidth() + "x" + image.getHeight());
  }
}
JAVA
javac /tmp/InSaveLogoCheck.java
java -cp /tmp InSaveLogoCheck "$LAUNCHER"

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
