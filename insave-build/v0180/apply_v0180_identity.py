from pathlib import Path
import re

upstream = (Path.cwd() / "upstream").resolve()
build_path = upstream / "app/build.gradle"
manifest_path = upstream / "app/src/main/AndroidManifest.xml"
strings_path = upstream / "app/src/main/res/values/strings.xml"
theme_path = upstream / "app/src/main/java/com/deniscerri/ytdl/util/ThemeUtil.kt"

build = build_path.read_text()
build = build.replace('applicationId "com.deniscerri.ytdl"', 'applicationId "com.adelvis.insave.recovery"')
build = build.replace(
    'versionCode versionMajor * 1000000 + versionMinor * 10000 + versionPatch * 100 + versionBuild',
    'versionCode 18000',
)
build = build.replace(
    'versionName "${versionMajor}.${versionMinor}.${versionPatch}${versionExt}"',
    'versionName "0.18.0-Hardening-QA"',
)
build_path.write_text(build)

strings = strings_path.read_text()
strings = re.sub(r'<string name="app_name">.*?</string>', '<string name="app_name">InSave</string>', strings, count=1)
strings_path.write_text(strings)

theme = theme_path.read_text().replace('>YTDL</span>nis', '>In</span>Save')
theme_path.write_text(theme)

manifest = manifest_path.read_text().replace('android:label="YTDLnis"', 'android:label="InSave"', 1)
# Ensure the product shell exists and the exported launcher alias, not the Activity itself,
# is the external entry point.
if '.insave.InSaveHubActivity' not in manifest:
    marker = '        <activity\n            android:name=".MainActivity"'
    insert = '''        <activity\n            android:name=".insave.InSaveHubActivity"\n            android:exported="false"\n            android:launchMode="singleTask"\n            android:theme="@style/BaseTheme" />\n\n        <activity\n            android:name=".MainActivity"'''
    if marker not in manifest:
        raise SystemExit('MainActivity manifest marker missing')
    manifest = manifest.replace(marker, insert, 1)
else:
    hub_pattern = re.compile(r'(<activity\b[^>]*android:name="\.insave\.InSaveHubActivity"[^>]*)(>)', re.DOTALL)
    m = hub_pattern.search(manifest)
    if m:
        tag = re.sub(r'android:exported="(?:true|false)"', 'android:exported="false"', m.group(1), count=1)
        manifest = manifest[:m.start()] + tag + m.group(2) + manifest[m.end():]
manifest = manifest.replace('android:targetActivity=".MainActivity"', 'android:targetActivity=".insave.InSaveHubActivity"')
manifest_path.write_text(manifest)

checks = {
    'application id': 'applicationId "com.adelvis.insave.recovery"' in build,
    'version code': 'versionCode 18000' in build,
    'version name': 'versionName "0.18.0-Hardening-QA"' in build,
    'app name': '<string name="app_name">InSave</string>' in strings,
    'hub internal': '.insave.InSaveHubActivity' in manifest and 'android:exported="false"' in manifest,
    'launcher alias': 'android:targetActivity=".insave.InSaveHubActivity"' in manifest,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    raise SystemExit('v0.18 identity contract failed: ' + ', '.join(failed))
print('InSave v0.18 QA identity: PASS')
