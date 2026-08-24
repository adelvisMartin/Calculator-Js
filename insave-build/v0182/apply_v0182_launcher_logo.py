from pathlib import Path
import re

root = Path.cwd()
upstream = root / "upstream"
manifest_path = upstream / "app/src/main/AndroidManifest.xml"
build_path = upstream / "app/build.gradle"
logo_path = upstream / "app/src/main/res/drawable-nodpi/insave_logo.jpg"

manifest = manifest_path.read_text()
build = build_path.read_text()

if not logo_path.exists() or logo_path.stat().st_size <= 4000:
    raise SystemExit("approved InSave logo resource missing")

# The previous release changed only <application android:icon>. YTDLnis uses
# launcher activity-alias entries (.Default/.DarkIcon/.LightIcon/.BlueIcon/
# .GreenIcon), and an alias icon overrides the application icon. Therefore the
# old mipmap artwork was still what Android Launcher displayed.
launcher_aliases = [".Default", ".DarkIcon", ".LightIcon", ".BlueIcon", ".GreenIcon"]

for alias in launcher_aliases:
    pattern = re.compile(
        r'(<activity-alias\b(?=[^>]*android:name="' + re.escape(alias) + r'")[^>]*>)',
        re.S,
    )
    match = pattern.search(manifest)
    if not match:
        raise SystemExit(f"launcher alias missing: {alias}")
    tag = match.group(1)
    if 'android:icon=' in tag:
        tag = re.sub(r'android:icon="[^"]+"', 'android:icon="@drawable/insave_logo"', tag, count=1)
    else:
        tag = tag[:-1] + '\n            android:icon="@drawable/insave_logo">'
    if 'android:roundIcon=' in tag:
        tag = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/insave_logo"', tag, count=1)
    else:
        tag = tag[:-1] + '\n            android:roundIcon="@drawable/insave_logo">'
    manifest = manifest[:match.start()] + tag + manifest[match.end():]

# Also brand application + quick-download share alias so every user-visible
# surface uses the same approved InSave artwork.
manifest = re.sub(r'android:icon="@mipmap/ic_launcher(?:_[^"]+)?"', 'android:icon="@drawable/insave_logo"', manifest)
manifest = re.sub(r'android:roundIcon="@mipmap/ic_launcher_round(?:_[^"]+)?"', 'android:roundIcon="@drawable/insave_logo"', manifest)

# Application label/icon are explicit even if a future upstream patch changes them.
app_match = re.search(r'<application\b[^>]*>', manifest, re.S)
if not app_match:
    raise SystemExit("application tag missing")
app_tag = app_match.group(0)
app_tag = re.sub(r'android:icon="[^"]+"', 'android:icon="@drawable/insave_logo"', app_tag, count=1)
app_tag = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/insave_logo"', app_tag, count=1)
manifest = manifest[:app_match.start()] + app_tag + manifest[app_match.end():]

build = build.replace('versionCode 18100', 'versionCode 18200')
build = build.replace('versionName "0.18.1-Social-UX-QA"', 'versionName "0.18.2-Launcher-Logo-QA"')

manifest_path.write_text(manifest)
build_path.write_text(build)

# Hard gate: every launchable alias must resolve to the approved artwork and no
# old launcher mipmap may remain on those aliases.
for alias in launcher_aliases:
    m = re.search(r'<activity-alias\b(?=[^>]*android:name="' + re.escape(alias) + r'")[^>]*>', manifest, re.S)
    tag = m.group(0) if m else ""
    if tag.count('android:icon="@drawable/insave_logo"') != 1:
        raise SystemExit(f"{alias} icon not branded")
    if tag.count('android:roundIcon="@drawable/insave_logo"') != 1:
        raise SystemExit(f"{alias} round icon not branded")
    if '@mipmap/ic_launcher' in tag:
        raise SystemExit(f"{alias} still references old launcher mipmap")

if 'versionCode 18200' not in build or 'versionName "0.18.2-Launcher-Logo-QA"' not in build:
    raise SystemExit("v0.18.2 identity not applied")

print("InSave v0.18.2 approved launcher logo across all aliases: PASS")
