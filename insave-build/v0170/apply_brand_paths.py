from pathlib import Path

hub_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
file_util_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/util/FileUtil.kt')

hub = hub_path.read_text()
file_util = file_util_path.read_text()

# Keep all user-visible public download destinations under Downloads/InSave.
default_anchor = '''            .putString("audio_format", "mp3")
'''
default_insert = '''            .putString("audio_format", "mp3")
            .putString("music_path", Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).absolutePath + "/InSave/Audio")
            .putString("video_path", Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).absolutePath + "/InSave/Video")
            .putString("command_path", Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).absolutePath + "/InSave/Command")
'''
if '.putString("music_path", Environment.getExternalStoragePublicDirectory' not in hub:
    if default_anchor not in hub:
        raise SystemExit('Hub audio-format default anchor missing')
    hub = hub.replace(default_anchor, default_insert, 1)

# Eliminate upstream YTDLnis naming from fallback/default public paths as well.
file_util = file_util.replace('"YTDLnis/Audio"', '"InSave/Audio"')
file_util = file_util.replace('"YTDLnis/Video"', '"InSave/Video"')
file_util = file_util.replace('"YTDLnis/Command"', '"InSave/Command"')
file_util = file_util.replace('"YTDLnis/Apks"', '"InSave/Apks"')
file_util = file_util.replace('File.separator + "YTDLnis"', 'File.separator + "InSave"')
file_util = file_util.replace('"YTDLnis/TERMINAL_CACHE"', '"InSave/TERMINAL_CACHE"')

hub_path.write_text(hub)
file_util_path.write_text(file_util)

checks = {
    'audio path': '"/InSave/Audio"' in hub and '"InSave/Audio"' in file_util,
    'video path': '"/InSave/Video"' in hub and '"InSave/Video"' in file_util,
    'no public ytdlnis audio': '"YTDLnis/Audio"' not in file_util,
    'no public ytdlnis video': '"YTDLnis/Video"' not in file_util,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave brand path contract failed: ' + ', '.join(failed))
print('InSave public path contract: PASS')
