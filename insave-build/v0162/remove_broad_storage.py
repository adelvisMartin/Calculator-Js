from pathlib import Path
import re

manifest = Path('upstream/app/src/main/AndroidManifest.xml')
text = manifest.read_text()
text, count = re.subn(
    r'\s*<uses-permission[^>]*android:name="android\.permission\.MANAGE_EXTERNAL_STORAGE"[^>]*/>',
    '',
    text,
)
manifest.write_text(text)
print(f'InSave broad storage permission removed: {count}')
