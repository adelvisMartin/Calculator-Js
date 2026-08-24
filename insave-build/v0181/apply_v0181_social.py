from pathlib import Path
import shutil

ROOT = Path.cwd()
UPSTREAM = (ROOT / "upstream").resolve()
APP = UPSTREAM / "app"
SRC = APP / "src/main/java/com/deniscerri/ytdl"
INSAVE = SRC / "insave"
TESTS = APP / "src/test/java/com/deniscerri/ytdl/insave"
OVERLAY = Path(__file__).resolve().parent

INSAVE.mkdir(parents=True, exist_ok=True)
TESTS.mkdir(parents=True, exist_ok=True)

shutil.copy2(OVERLAY / "InSaveSocialPolicy.kt", INSAVE / "InSaveSocialPolicy.kt")
shutil.copy2(OVERLAY / "InSaveSocialPolicyTest.kt", TESTS / "InSaveSocialPolicyTest.kt")

hub_path = INSAVE / "InSaveHubActivity.kt"
hub = hub_path.read_text()

# The user reported Facebook downloads already worked but were hard to discover.
# Put both social shortcuts immediately after the Home title, before the large
# music/video sections, so they are visible without hunting through the generic flow.
social_quick = '''
        root.addView(card().apply {
            addView(sectionTitle("Descargas sociales"))
            addView(body("Copia el enlace de una publicación, Reel o video público. InSave detecta la plataforma, toma el enlace escrito arriba o el portapapeles y abre directamente el flujo de video."))
            addView(primaryButton("Instagram · Pegar y descargar") {
                openSocialDownload(InSaveSocialPolicy.Platform.INSTAGRAM)
            })
            addView(primaryButton("Facebook · Pegar y descargar") {
                openSocialDownload(InSaveSocialPolicy.Platform.FACEBOOK)
            })
            addView(body("Facebook admite facebook.com y fb.watch. Instagram admite instagram.com. Para contenido privado puede ser necesaria una sesión válida en el motor avanzado."))
        })

'''
anchor = '        root.addView(appTitle("InSave", "Descarga música primero. Video cuando lo necesites."))\n'
if 'Instagram · Pegar y descargar' not in hub:
    if anchor not in hub:
        raise SystemExit('v0.18.1 social top-level anchor missing')
    hub = hub.replace(anchor, anchor + social_quick, 1)

helper = '''    private fun openSocialDownload(platform: InSaveSocialPolicy.Platform) {
        if (!::urlInput.isInitialized) {
            toast("Abre Inicio e inténtalo de nuevo.")
            return
        }

        val typed = InSaveSocialPolicy.classify(urlInput.text.toString())
        var target = typed?.takeIf { it.platform == platform }

        if (target == null) {
            val clipboard = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
            val clipboardText = clipboard.primaryClip
                ?.takeIf { it.itemCount > 0 }
                ?.getItemAt(0)
                ?.coerceToText(this)
                ?.toString()
            target = InSaveSocialPolicy.classify(clipboardText)
                ?.takeIf { it.platform == platform }
        }

        if (target == null) {
            toast(InSaveSocialPolicy.supportedHint(platform))
            return
        }

        urlInput.setText(target.normalizedUrl)
        urlInput.setSelection(target.normalizedUrl.length)
        prefs.edit()
            .putString("preferred_download_type", DownloadType.video.toString())
            .putBoolean("remember_download_type", false)
            .apply()
        openUrlAs(DownloadType.video)
    }

'''
helper_anchor = '    private fun buildStatusesView(): View {'
if 'private fun openSocialDownload(platform: InSaveSocialPolicy.Platform)' not in hub:
    if helper_anchor not in hub:
        raise SystemExit('v0.18.1 social helper anchor missing')
    hub = hub.replace(helper_anchor, helper + helper_anchor, 1)

hub_path.write_text(hub)

build_path = APP / "build.gradle"
build = build_path.read_text()
build = build.replace('versionCode 18000', 'versionCode 18100')
build = build.replace('versionName "0.18.0-Hardening-QA"', 'versionName "0.18.1-Social-UX-QA"')
build_path.write_text(build)

checks = {
    'social shortcuts top-level': hub.find('Descargas sociales') > hub.find('appTitle("InSave"') and hub.find('Descargas sociales') < hub.find('sectionTitle("Descargar música")'),
    'instagram dedicated shortcut': 'Instagram · Pegar y descargar' in hub,
    'facebook dedicated shortcut': 'Facebook · Pegar y descargar' in hub,
    'facebook fb.watch hint': 'fb.watch' in hub,
    'social clipboard fallback': 'clipboard.primaryClip' in hub,
    'social platform validation': 'InSaveSocialPolicy.classify' in hub,
    'social defaults video': 'openUrlAs(DownloadType.video)' in hub,
    'version code': 'versionCode 18100' in build,
    'version name': 'versionName "0.18.1-Social-UX-QA"' in build,
    'social policy source': (INSAVE / 'InSaveSocialPolicy.kt').exists(),
    'social policy test': (TESTS / 'InSaveSocialPolicyTest.kt').exists(),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave v0.18.1 social UX contract failed: ' + ', '.join(failed))

print('InSave v0.18.1 top-level Instagram/Facebook UX: PASS')
