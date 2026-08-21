from pathlib import Path
import re

home = Path('upstream/app/src/main/java/com/deniscerri/ytdl/ui/HomeFragment.kt')
h = home.read_text()
if 'import com.google.android.material.snackbar.Snackbar' not in h:
    marker = 'import com.google.android.material.search.SearchView\n'
    if marker not in h:
        raise SystemExit('SearchView import marker missing')
    h = h.replace(marker, marker + 'import com.google.android.material.snackbar.Snackbar\n', 1)
home.write_text(h)

manifest = Path('upstream/app/src/main/AndroidManifest.xml')
m = manifest.read_text()

# Remove any duplicate scoped-media declarations introduced by the InSave patch.
for permission in (
    'android.permission.READ_MEDIA_IMAGES',
    'android.permission.READ_MEDIA_VIDEO',
    'android.permission.READ_EXTERNAL_STORAGE',
):
    pattern = re.compile(r'\s*<uses-permission(?=[^>]*android:name="' + re.escape(permission) + r'")[^>]*/>', re.S)
    matches = list(pattern.finditer(m))
    if matches:
        m = pattern.sub('', m)

anchor = '<uses-permission android:name="android.permission.INTERNET" />'
if anchor not in m:
    raise SystemExit('Manifest INTERNET permission anchor missing')
scoped = '''\n    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />\n    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />\n    <uses-permission\n        android:name="android.permission.READ_EXTERNAL_STORAGE"\n        android:maxSdkVersion="32" />'''
m = m.replace(anchor, anchor + scoped, 1)
manifest.write_text(m)

assert h.count('import com.google.android.material.snackbar.Snackbar') == 1
assert m.count('android.permission.READ_MEDIA_IMAGES') == 1
assert m.count('android.permission.READ_MEDIA_VIDEO') == 1
assert m.count('android.permission.READ_EXTERNAL_STORAGE') == 1
assert 'android.permission.MANAGE_EXTERNAL_STORAGE' not in m
print('InSave v0.16.2 import/permission normalization: PASS')
