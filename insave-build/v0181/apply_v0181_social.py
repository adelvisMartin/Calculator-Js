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

social_cards = '''
        root.addView(card().apply {
            addView(sectionTitle("Instagram"))
            addView(body("Acceso directo para publicaciones, Reels y videos públicos. Copia el enlace en Instagram y toca el botón; InSave usa primero el enlace escrito arriba y, si no corresponde, revisa el portapapeles."))
            addView(primaryButton("Instagram · Pegar y descargar") {
                openSocialDownload(InSaveSocialPolicy.Platform.INSTAGRAM)
            })
        })

        root.addView(card().apply {
            addView(sectionTitle("Facebook"))
            addView(body("Acceso directo para videos, Reels y publicaciones públicas de Facebook, incluido fb.watch. Evita tener que encontrar el flujo genérico de Video."))
            addView(primaryButton("Facebook · Pegar y descargar") {
                openSocialDownload(InSaveSocialPolicy.Platform.FACEBOOK)
            })
        })

'''
anchor = '''        root.addView(card().apply {
            addView(sectionTitle("YouTube"))
'''
if 'Instagram · Pegar y descargar' not in hub:
    if anchor not in hub:
        raise SystemExit('v0.18.1 social card anchor missing')
    hub = hub.replace(anchor, social_cards + anchor, 1)

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
    'instagram dedicated card': 'Instagram · Pegar y descargar' in hub,
    'facebook dedicated card': 'Facebook · Pegar y descargar' in hub,
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

print('InSave v0.18.1 dedicated Instagram/Facebook UX: PASS')
