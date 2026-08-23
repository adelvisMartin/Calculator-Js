from pathlib import Path
import re
import shutil

OVERLAY = Path(__file__).resolve().parent
UPSTREAM = (Path.cwd() / "upstream").resolve()
APP = UPSTREAM / "app"
SRC = APP / "src/main/java/com/deniscerri/ytdl"
INSAVE = SRC / "insave"
TESTS = APP / "src/test/java/com/deniscerri/ytdl/insave"
INSAVE.mkdir(parents=True, exist_ok=True)
TESTS.mkdir(parents=True, exist_ok=True)


def require(path: Path):
    if not path.exists():
        raise SystemExit(f"required path missing: {path}")
    return path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"hardening anchor missing: {label}")


# ---------------------------------------------------------------------------
# 1) Materialize InSave-owned security/resilience code and unit tests.
# ---------------------------------------------------------------------------
for name in ("InSaveInputPolicy.kt", "InSaveRedactor.kt", "InSaveProviderFailureClassifier.kt"):
    shutil.copy2(require(OVERLAY / name), INSAVE / name)
shutil.copy2(require(OVERLAY / "InSaveHardeningUnitTest.kt"), TESTS / "InSaveHardeningUnitTest.kt")

# ---------------------------------------------------------------------------
# 2) Gradle/build hygiene: remove phantom modules, obsolete WebView dependency,
#    debug-key release signing, duplicate dependencies and known Gradle 9/10 DSL debt.
# ---------------------------------------------------------------------------
settings_path = UPSTREAM / "settings.gradle"
settings = require(settings_path).read_text()
settings = settings.replace("maven { url 'https://jitpack.io' }", "maven { url = uri('https://jitpack.io') }")
settings = settings.replace("rootProject.name = \"YTDLnis\"", "rootProject.name = \"InSaveRecovery\"")
settings = re.sub(r"include\s+':common',\s*':app',\s*':library',\s*':ffmpeg'", "include ':app'", settings)
settings_path.write_text(settings)

root_build_path = UPSTREAM / "build.gradle"
root_build = require(root_build_path).read_text()
root_build = root_build.replace("maven { url 'https://jitpack.io' }", "maven { url = uri('https://jitpack.io') }")
root_build = root_build.replace(
    "maven { url 'https://central.sonatype.com/repository/maven-snapshots/' }",
    "maven { url = uri('https://central.sonatype.com/repository/maven-snapshots/') }",
)
root_build = root_build.replace("delete rootProject.buildDir", "delete rootProject.layout.buildDirectory")
root_build_path.write_text(root_build)

app_build_path = APP / "build.gradle"
build = require(app_build_path).read_text()

signing_defs = '''\ndef insaveReleaseStorePath = System.getenv("INSAVE_KEYSTORE_PATH")\ndef insaveReleaseStorePassword = System.getenv("INSAVE_KEYSTORE_PASSWORD")\ndef insaveReleaseKeyAlias = System.getenv("INSAVE_KEY_ALIAS")\ndef insaveReleaseKeyPassword = System.getenv("INSAVE_KEY_PASSWORD")\ndef hasInSaveReleaseSigning = [\n    insaveReleaseStorePath,\n    insaveReleaseStorePassword,\n    insaveReleaseKeyAlias,\n    insaveReleaseKeyPassword\n].every { it != null && !it.trim().isEmpty() }\n'''
if "def hasInSaveReleaseSigning" not in build:
    build = replace_once(build, "def properties = new Properties()\n", "def properties = new Properties()\n" + signing_defs, "release signing definitions")

android_anchor = "android {\n    namespace 'com.deniscerri.ytdl'\n"
android_insert = '''android {\n    namespace = 'com.deniscerri.ytdl'\n\n    if (hasInSaveReleaseSigning) {\n        signingConfigs {\n            insaveRelease {\n                storeFile = file(insaveReleaseStorePath)\n                storePassword = insaveReleaseStorePassword\n                keyAlias = insaveReleaseKeyAlias\n                keyPassword = insaveReleaseKeyPassword\n            }\n        }\n    }\n'''
if "signingConfigs {\n            insaveRelease" not in build:
    build = replace_once(build, android_anchor, android_insert, "release signing config")

# Recovery previously inherited the upstream debug signing key for release. Never do this.
release_start = build.find("    buildTypes {")
release_end = build.find("    flavorDimensions", release_start)
if release_start < 0 or release_end < 0:
    raise SystemExit("buildTypes block not found")
bt = build[release_start:release_end]
release_marker = "        release {"
rp = bt.find(release_marker)
dp = bt.find("        debug {", rp)
if rp < 0 or dp < 0:
    raise SystemExit("release/debug blocks missing")
release_block = bt[rp:dp]
release_block = release_block.replace("            signingConfig signingConfigs.debug\n", "")
release_block = release_block.replace("            signingConfig = signingConfigs.debug\n", "")
if "signingConfig = signingConfigs.insaveRelease" not in release_block:
    brace = release_block.rfind("        }")
    release_block = release_block[:brace] + '''            if (hasInSaveReleaseSigning) {\n                signingConfig = signingConfigs.insaveRelease\n            }\n''' + release_block[brace:]
bt = bt[:rp] + release_block + bt[dp:]
build = build[:release_start] + bt + build[release_end:]

# The legacy archivesBaseName API is removed in Gradle 9. Artifact naming is handled by CI.
build = re.sub(r'^\s*archivesBaseName\s*=.*\n', '', build, flags=re.MULTILINE)

# Explicit Play flavor: policy-compliant storage manifest removes broad/special permissions.
if "        play {\n            dimension \"version\"" not in build:
    build = replace_once(
        build,
        '''        foss {\n            dimension "version"\n        }\n''',
        '''        foss {\n            dimension "version"\n        }\n        play {\n            dimension "version"\n        }\n''',
        "play flavor",
    )

# Eliminate deprecated/unmaintained accompanist WebView after replacing the only usage.
build = re.sub(r'^\s*implementation\s+[\"\']com\.google\.accompanist:accompanist-webview:[^\"\']+[\"\']\s*\n', '', build, flags=re.MULTILINE)

# De-duplicate preference-ktx without changing version.
pref_line = '    implementation "androidx.preference:preference-ktx:1.2.1"\n'
while build.count(pref_line) > 1:
    idx = build.rfind(pref_line)
    build = build[:idx] + build[idx + len(pref_line):]

# Future-safe Groovy DSL for warnings observed in the real v0.17.2 build.
replacements = {
    "namespace 'com.deniscerri.ytdl'": "namespace = 'com.deniscerri.ytdl'",
    "minifyEnabled true": "minifyEnabled = true",
    "minifyEnabled false": "minifyEnabled = false",
    "shrinkResources true": "shrinkResources = true",
    "shrinkResources false": "shrinkResources = false",
    "debuggable false": "debuggable = false",
    "debuggable true": "debuggable = true",
    "signingConfig signingConfigs.debug": "signingConfig = signingConfigs.debug",
    "isDefault true": "isDefault = true",
    "viewBinding true": "viewBinding = true",
    "buildConfig true": "buildConfig = true",
    "compose true": "compose = true",
    "coreLibraryDesugaringEnabled true": "coreLibraryDesugaringEnabled = true",
    "enable true": "enable = true",
    "universalApk true": "universalApk = true",
    "useLegacyPackaging true": "useLegacyPackaging = true",
    'kotlinCompilerExtensionVersion "1.10.1"': 'kotlinCompilerExtensionVersion = "1.10.1"',
}
for old, new in replacements.items():
    build = build.replace(old, new)
app_build_path.write_text(build)

# ---------------------------------------------------------------------------
# 3) Native WebView replacement for manual PO-token helper.
# ---------------------------------------------------------------------------
po_activity = SRC / "ui/more/settings/advanced/generateyoutubepotokens/webview/PoTokenWebViewLoginActivity.kt"
shutil.copy2(require(OVERLAY / "PoTokenWebViewLoginActivity.kt"), po_activity)
layout_path = APP / "src/main/res/layout/webview_potoken_activity.xml"
layout = require(layout_path).read_text()
layout = re.sub(
    r'<androidx\.compose\.ui\.platform\.ComposeView\s+android:id="@\+id/webview_compose".*?/>',
    '''<WebView\n        android:id="@+id/webview_native"\n        android:layout_width="match_parent"\n        android:layout_height="0dp"\n        app:layout_constraintBottom_toBottomOf="parent"\n        app:layout_constraintEnd_toEndOf="parent"\n        app:layout_constraintStart_toStartOf="parent"\n        app:layout_constraintTop_toBottomOf="@+id/webview_appbarlayout" />''',
    layout,
    count=1,
    flags=re.DOTALL,
)
if "webview_native" not in layout or "ComposeView" in layout:
    raise SystemExit("native WebView layout migration failed")
layout_path.write_text(layout)

# ---------------------------------------------------------------------------
# 4) Manifest attack-surface reduction + Play storage policy variant.
# ---------------------------------------------------------------------------
manifest_path = APP / "src/main/AndroidManifest.xml"
manifest = require(manifest_path).read_text()
if 'android:usesCleartextTraffic=' not in manifest:
    manifest = manifest.replace('        android:allowBackup="false"\n', '        android:allowBackup="false"\n        android:usesCleartextTraffic="false"\n', 1)


def set_activity_exported(xml: str, activity_name: str, value: bool) -> str:
    pattern = re.compile(r'(<activity\b[^>]*android:name="' + re.escape(activity_name) + r'"[^>]*)(>)', re.DOTALL)
    match = pattern.search(xml)
    if not match:
        return xml
    tag = match.group(1)
    replacement = f'android:exported="{str(value).lower()}"'
    if re.search(r'android:exported="(?:true|false)"', tag):
        tag = re.sub(r'android:exported="(?:true|false)"', replacement, tag, count=1)
    else:
        tag += '\n            ' + replacement
    return xml[:match.start()] + tag + match.group(2) + xml[match.end():]

for internal_activity in (
    ".MainActivity",
    ".receiver.TransparentActivity",
    ".ui.more.settings.SettingsActivity",
    ".ui.more.terminal.TerminalActivity",
    ".insave.InSaveHubActivity",
):
    manifest = set_activity_exported(manifest, internal_activity, False)
# ShareActivity intentionally remains exported: it is the validated SEND/VIEW boundary.
manifest_path.write_text(manifest)

play_manifest = APP / "src/play/AndroidManifest.xml"
play_manifest.parent.mkdir(parents=True, exist_ok=True)
play_manifest.write_text('''<?xml version="1.0" encoding="utf-8"?>\n<manifest xmlns:android="http://schemas.android.com/apk/res/android"\n    xmlns:tools="http://schemas.android.com/tools">\n    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" tools:node="remove" />\n    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" tools:node="remove" />\n    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" tools:node="remove" />\n</manifest>\n''')

# ---------------------------------------------------------------------------
# 5) Cobalt Provider C: TLS/public endpoint policy and source validation.
# ---------------------------------------------------------------------------
cobalt_path = INSAVE / "InSaveCobaltResolver.kt"
cobalt = require(cobalt_path).read_text()
if "import com.deniscerri.ytdl.BuildConfig" not in cobalt:
    cobalt = cobalt.replace("import android.content.Context\n", "import android.content.Context\nimport com.deniscerri.ytdl.BuildConfig\n", 1)
cobalt = cobalt.replace("import okhttp3.HttpUrl.Companion.toHttpUrlOrNull\n", "")
cobalt = replace_once(
    cobalt,
    '''        val endpoint = endpoint() ?: return null\n        val cobaltBitrate = normalizeCobaltBitrate(bitrateKbps)\n        val payload = linkedMapOf<String, Any>(\n            "url" to sourceUrl,\n''',
    '''        val endpoint = endpoint() ?: return null\n        val safeSourceUrl = InSaveInputPolicy.normalizeHttpUrl(sourceUrl) ?: return null\n        val cobaltBitrate = normalizeCobaltBitrate(bitrateKbps)\n        val payload = linkedMapOf<String, Any>(\n            "url" to safeSourceUrl,\n''',
    "Cobalt source URL validation",
)
endpoint_pattern = re.compile(r'''    private fun endpoint\(\): String\? \{.*?\n    \}\n\n    private fun isPublicOrSelfHostedHttpUrl\(value: String\): Boolean \{.*?\n    \}\n''', re.DOTALL)
endpoint_repl = '''    private fun endpoint(): String? {\n        val raw = prefs.getString(PREF_ENDPOINT, null) ?: return null\n        return InSaveInputPolicy.normalizeProviderEndpoint(raw, allowLocalDebug = BuildConfig.DEBUG)\n    }\n\n    private fun isPublicOrSelfHostedHttpUrl(value: String): Boolean =\n        InSaveInputPolicy.isSafeProviderResponseUrl(value, allowLocalDebug = BuildConfig.DEBUG)\n'''
cobalt, n = endpoint_pattern.subn(endpoint_repl, cobalt, count=1)
if n != 1:
    raise SystemExit("Cobalt endpoint policy block missing")
cobalt = re.sub(r'\n\s*private val LOCAL_HOSTS = setOf\([^\n]+\)', '', cobalt)
cobalt_path.write_text(cobalt)

# ---------------------------------------------------------------------------
# 6) Validate exported ShareActivity inputs; never log full incoming intents.
# ---------------------------------------------------------------------------
share_path = SRC / "receiver/ShareActivity.kt"
share = require(share_path).read_text()
if "import com.deniscerri.ytdl.insave.InSaveInputPolicy" not in share:
    share = share.replace("import com.deniscerri.ytdl.database.viewmodel.ResultViewModel\n", "import com.deniscerri.ytdl.database.viewmodel.ResultViewModel\nimport com.deniscerri.ytdl.insave.InSaveInputPolicy\n", 1)
share = share.replace('        Log.e("aa", intent.toString())\n', '        Log.d("InSaveShare", "Inbound share/view intent received")\n')
share = replace_once(
    share,
    '''            val inputQuery = data.extractURL()\n            val ai = packageManager.getActivityInfo(componentName, PackageManager.GET_META_DATA)\n''',
    '''            val extractedUrl = data.extractURL()\n            val inputQuery = InSaveInputPolicy.normalizeHttpUrl(extractedUrl)\n            if (inputQuery == null) {\n                Toast.makeText(this, "El enlace compartido no es válido o seguro.", Toast.LENGTH_SHORT).show()\n                finish()\n                return\n            }\n            val ai = packageManager.getActivityInfo(componentName, PackageManager.GET_META_DATA)\n''',
    "ShareActivity inbound validation",
)
share_path.write_text(share)

# ---------------------------------------------------------------------------
# 7) Hub/Main input bridge: sanitize search terms and URLs before crossing Activities.
# ---------------------------------------------------------------------------
hub_path = INSAVE / "InSaveHubActivity.kt"
hub = require(hub_path).read_text()
if "import com.deniscerri.ytdl.insave.InSaveInputPolicy" not in hub:
    # Same package; no import required. Marker comment documents the boundary.
    hub = hub.replace("class InSaveHubActivity", "// Inbound values are normalized by InSaveInputPolicy before engine handoff.\nclass InSaveHubActivity", 1)
open_old = '''        val rawInput = if (::urlInput.isInitialized) urlInput.text.toString().trim() else ""\n        val url = normalizeUrl(rawInput)\n        if (url == null) {\n            if (rawInput.isBlank()) {\n                openDownloader(type)\n            } else {\n                prefs.edit()\n                    .putString("preferred_download_type", type.toString())\n                    .putBoolean("remember_download_type", false)\n                    .putString("search_engine", "ytsearch")\n                    .apply()\n                startActivity(Intent(this, MainActivity::class.java).apply {\n                    action = Intent.ACTION_VIEW\n                    putExtra("insave_query", rawInput)\n                })\n                toast("Buscando: $rawInput")\n            }\n            return\n        }\n'''
open_new = '''        val rawInput = if (::urlInput.isInitialized) urlInput.text.toString().trim() else ""\n        val safeInput = InSaveInputPolicy.classify(rawInput)\n        val url = (safeInput as? InSaveInputPolicy.Input.Url)?.value\n        if (url == null) {\n            if (rawInput.isBlank()) {\n                openDownloader(type)\n            } else {\n                val safeQuery = (safeInput as? InSaveInputPolicy.Input.Search)?.value\n                if (safeQuery == null) {\n                    toast("Entrada no válida o no segura")\n                    return\n                }\n                prefs.edit()\n                    .putString("preferred_download_type", type.toString())\n                    .putBoolean("remember_download_type", false)\n                    .putString("search_engine", "ytsearch")\n                    .apply()\n                startActivity(Intent(this, MainActivity::class.java).apply {\n                    action = Intent.ACTION_VIEW\n                    putExtra("insave_query", safeQuery)\n                })\n                toast("Buscando: $safeQuery")\n            }\n            return\n        }\n'''
hub = replace_once(hub, open_old, open_new, "Hub safe openUrlAs")
hub = hub.replace('putExtra("insave_query", normalizeUrl(raw) ?: raw)', '''putExtra("insave_query", when (val safe = InSaveInputPolicy.classify(raw)) {\n                    is InSaveInputPolicy.Input.Url -> safe.value\n                    is InSaveInputPolicy.Input.Search -> safe.value\n                    null -> return@apply\n                })''')
hub_path.write_text(hub)

main_path = SRC / "MainActivity.kt"
main = require(main_path).read_text()
if "import com.deniscerri.ytdl.insave.InSaveInputPolicy" not in main:
    package_line = "package com.deniscerri.ytdl\n"
    main = main.replace(package_line, package_line + "\nimport com.deniscerri.ytdl.insave.InSaveInputPolicy\n", 1)
bridge_old = '''            intent.getStringExtra("insave_query")?.trim()?.takeIf { it.isNotEmpty() }?.let { query ->\n                val bundle = Bundle().apply { putString("url", query) }\n                navController.popBackStack(R.id.homeFragment, true)\n                navController.navigate(R.id.homeFragment, bundle)\n                return\n            }\n'''
bridge_new = '''            intent.getStringExtra("insave_query")?.let { inbound ->\n                val query = when (val safe = InSaveInputPolicy.classify(inbound)) {\n                    is InSaveInputPolicy.Input.Url -> safe.value\n                    is InSaveInputPolicy.Input.Search -> safe.value\n                    null -> null\n                }\n                if (!query.isNullOrBlank()) {\n                    val bundle = Bundle().apply { putString("url", query) }\n                    navController.popBackStack(R.id.homeFragment, true)\n                    navController.navigate(R.id.homeFragment, bundle)\n                    return\n                }\n            }\n'''
main = replace_once(main, bridge_old, bridge_new, "MainActivity search bridge validation")
main_path.write_text(main)

# ---------------------------------------------------------------------------
# 8) Provider B strategy ladder: mweb+fresh token -> web_embedded -> android_vr,
#    then optional Provider C. Fallback is bounded and only for recoverable failures.
# ---------------------------------------------------------------------------
ytdlp_path = SRC / "util/extractors/ytdlp/YTDLPUtil.kt"
ytdlp = require(ytdlp_path).read_text()
ytdlp = replace_once(
    ytdlp,
    "    private fun YTDLRequest.setYoutubeExtractorArgs(url: String?) {",
    "    private fun YTDLRequest.setYoutubeExtractorArgs(url: String?, inSavePlayerClientOverride: String? = null) {",
    "youtube extractor override signature",
)
# Limit dynamic mweb token installation to the normal B1 strategy.
fn_pos = ytdlp.find("private fun YTDLRequest.setYoutubeExtractorArgs")
fn_end = ytdlp.find("    private fun YTDLRequest.addConfig", fn_pos)
if fn_pos < 0 or fn_end < 0:
    raise SystemExit("youtube extractor function boundaries missing")
fn = ytdlp[fn_pos:fn_end]
fn = fn.replace(
    '        if (url?.isYoutubeURL() == true) {',
    '        if (url?.isYoutubeURL() == true && (inSavePlayerClientOverride == null || inSavePlayerClientOverride == "mweb")) {',
    1,
)
override_anchor = '        if (playerClients.isNotEmpty()){\n'
if "playerClients.clear()" not in fn:
    fn = replace_once(
        fn,
        override_anchor,
        '''        if (!inSavePlayerClientOverride.isNullOrBlank()) {\n            playerClients.clear()\n            poTokens.clear()\n            playerClients.add(inSavePlayerClientOverride)\n        }\n\n''' + override_anchor,
        "player client override",
    )
ytdlp = ytdlp[:fn_pos] + fn + ytdlp[fn_end:]

sig_old = '''    fun buildYTDLRequest(\n        downloadItem: DownloadItem,\n        inSaveOverrideDirectUrl: String? = null\n    ) : YTDLRequest {'''
sig_new = '''    fun buildYTDLRequest(\n        downloadItem: DownloadItem,\n        inSaveOverrideDirectUrl: String? = null,\n        inSaveYoutubeClientOverride: String? = null\n    ) : YTDLRequest {'''
ytdlp = replace_once(ytdlp, sig_old, sig_new, "buildYTDLRequest client override")
# Only the call inside buildYTDLRequest should consume the override; other data-fetch calls keep defaults.
build_pos = ytdlp.find(sig_new)
if build_pos < 0:
    raise SystemExit("new buildYTDLRequest signature missing")
next_fun = ytdlp.find("\n    fun ", build_pos + len(sig_new))
if next_fun < 0:
    next_fun = len(ytdlp)
build_fn = ytdlp[build_pos:next_fun]
if "setYoutubeExtractorArgs(downloadItem.url, inSaveYoutubeClientOverride)" not in build_fn:
    build_fn = build_fn.replace(
        "setYoutubeExtractorArgs(downloadItem.url)",
        "setYoutubeExtractorArgs(downloadItem.url, inSaveYoutubeClientOverride)",
        1,
    )
    if "setYoutubeExtractorArgs(downloadItem.url, inSaveYoutubeClientOverride)" not in build_fn:
        raise SystemExit("download request youtube extractor call missing")
ytdlp = ytdlp[:build_pos] + build_fn + ytdlp[next_fun:]
ytdlp_path.write_text(ytdlp)

worker_path = SRC / "work/download/DownloadWorker.kt"
worker = require(worker_path).read_text()
for imp in (
    "import com.deniscerri.ytdl.insave.InSaveProviderFailureClassifier\n",
    "import com.deniscerri.ytdl.insave.InSaveRedactor\n",
):
    if imp not in worker:
        anchor = "import com.deniscerri.ytdl.database.enums.DownloadType\n"
        worker = replace_once(worker, anchor, anchor + imp, f"worker import {imp.strip()}")

recover_start = worker.find("                        }.recoverCatching { providerBError ->")
recover_end = worker.find("                        }.onSuccess {", recover_start)
if recover_start < 0 or recover_end < 0:
    raise SystemExit("Provider B recover block missing")
recover_new = '''                        }.recoverCatching { providerBError ->\n                            val isYoutubeAudio =\n                                downloadItem.type == DownloadType.audio && downloadItem.url.isYoutubeURL()\n                            if (!isYoutubeAudio || providerBError is RuntimeManager.CanceledException) {\n                                throw providerBError\n                            }\n\n                            var terminalProviderError: Throwable = providerBError\n                            if (InSaveProviderFailureClassifier.allowsAnonymousClientFallback(providerBError)) {\n                                for (client in InSaveProviderFailureClassifier.anonymousYoutubeFallbackClients) {\n                                    val fallback = runCatching {\n                                        val kind = InSaveProviderFailureClassifier.classify(terminalProviderError)\n                                        logString.append("InSave Provider B fallback: client=$client cause=$kind\\n")\n                                        request = ytdlpUtil.buildYTDLRequest(\n                                            downloadItem,\n                                            inSaveYoutubeClientOverride = client\n                                        )\n                                        commandString = ytdlpUtil.parseYTDLRequestString(request)\n                                        RuntimeManager.getInstance().destroyProcessById(downloadItem.id.toString())\n                                        executeInSaveRequest(request)\n                                    }\n                                    if (fallback.isSuccess) return@recoverCatching fallback.getOrThrow()\n                                    terminalProviderError = fallback.exceptionOrNull() ?: terminalProviderError\n                                    if (terminalProviderError is RuntimeManager.CanceledException) throw terminalProviderError\n                                }\n                            }\n\n                            // Provider C is last and remains explicitly configured/self-hosted only.\n                            val cobaltUrl = ytdlpUtil.resolveInSaveCobaltFallbackUrl(downloadItem.url)\n                            if (cobaltUrl.isNullOrBlank()) throw terminalProviderError\n\n                            logString.append("InSave Provider B strategies failed; retrying optional Provider C.\\n")\n                            request = ytdlpUtil.buildYTDLRequest(\n                                downloadItem,\n                                inSaveOverrideDirectUrl = cobaltUrl\n                            )\n                            commandString = ytdlpUtil.parseYTDLRequestString(request)\n                            RuntimeManager.getInstance().destroyProcessById(downloadItem.id.toString())\n                            executeInSaveRequest(request)\n'''
worker = worker[:recover_start] + recover_new + worker[recover_end:]

# Redact all persisted/visible extractor lines inside the centralized execution helper.
exec_start = worker.find("                        fun executeInSaveRequest")
exec_end = worker.find("                        runCatching {", exec_start)
if exec_start < 0 or exec_end < 0:
    raise SystemExit("executeInSaveRequest block missing")
exec_block = worker[exec_start:exec_end]
if "val safeLine = InSaveRedactor.redact(line)" not in exec_block:
    exec_block = exec_block.replace(
        ") { progress, _, line ->\n",
        ") { progress, _, line ->\n                                val safeLine = InSaveRedactor.redact(line)\n",
        1,
    )
    exec_block = exec_block.replace("                                    line,\n", "                                    safeLine,\n")
    exec_block = exec_block.replace("                                    line, progress.toInt(),", "                                    safeLine, progress.toInt(),")
    exec_block = exec_block.replace("                                        logRepo.update(line, logItem.id)", "                                        logRepo.update(safeLine, logItem.id)")
    exec_block = exec_block.replace('                                    logString.append("$line\\n")', '                                    logString.append("$safeLine\\n")')
worker = worker[:exec_start] + exec_block + worker[exec_end:]
worker = worker.replace(
    'it.message?.takeIf { message -> message.isNotBlank() }',
    'InSaveRedactor.redact(it.message).takeIf { message -> message.isNotBlank() }',
)
worker_path.write_text(worker)

# ---------------------------------------------------------------------------
# 9) Remove PO-token values from debug logs at the source.
# ---------------------------------------------------------------------------
generator_path = SRC / "util/extractors/newpipe/potoken/NewPipePoTokenGenerator.kt"
generator = require(generator_path).read_text()
generator = re.sub(
    r'''\s*Log\.d\(\s*TAG,\s*"poToken for \$videoId: playerPot=\$playerPot, " \+\s*"streamingPot=\$streamingPot, visitor_data=\$visitorData"\s*\)''',
    '\n            Log.d(TAG, "PO token generated for video=${videoId.take(6)}…; secret values redacted")',
    generator,
    count=1,
    flags=re.DOTALL,
)
if "playerPot=$playerPot" in generator or "streamingPot=$streamingPot" in generator:
    raise SystemExit("NewPipe token debug log still exposes secret values")
generator_path.write_text(generator)

pot_webview_path = SRC / "util/extractors/newpipe/potoken/PoTokenWebView.kt"
pot_webview = require(pot_webview_path).read_text()
pot_webview = re.sub(
    r'Log\.d\(TAG, "Generated poToken \(before decoding\): identifier=\$identifier poTokenU8=\$poTokenU8"\)',
    'Log.d(TAG, "Generated PO token bytes; value redacted")',
    pot_webview,
)
pot_webview = re.sub(
    r'Log\.d\(TAG, "Generated poToken: identifier=\$identifier poToken=\$poToken"\)',
    'Log.d(TAG, "Generated PO token; value redacted")',
    pot_webview,
)
if "poToken=$poToken" in pot_webview or "poTokenU8=$poTokenU8" in pot_webview:
    raise SystemExit("PoTokenWebView still logs token material")
pot_webview_path.write_text(pot_webview)

# ---------------------------------------------------------------------------
# 10) Room query warning: the summary query intentionally omits large log blobs.
#     Keep that performance characteristic and explicitly suppress the known mismatch.
# ---------------------------------------------------------------------------
terminal_dao_path = SRC / "database/dao/TerminalDao.kt"
tdao = require(terminal_dao_path).read_text()
for signature in (
    '    @Query("SELECT id,command FROM terminalDownloads ORDER BY id")\n    fun getActiveTerminalDownloads()',
    '    @Query("SELECT id,command FROM terminalDownloads ORDER BY id")\n    fun getActiveTerminalDownloadsFlow()',
):
    if signature in tdao:
        tdao = tdao.replace(
            signature,
            '    @SuppressWarnings(androidx.room.RoomWarnings.QUERY_MISMATCH)\n' + signature.lstrip(),
            1,
        )
terminal_dao_path.write_text(tdao)

# ---------------------------------------------------------------------------
# Hard gate: these are implementation facts, not a claimed score.
# ---------------------------------------------------------------------------
checks = {
    "only app Gradle module": "include ':app'" in settings and ":common" not in settings,
    "no debug release signing": "release {" in build and "signingConfig signingConfigs.debug" not in build[build.find("release {"):build.find("debug {", build.find("release {"))],
    "release secret signing": "INSAVE_KEYSTORE_PATH" in build and "signingConfigs.insaveRelease" in build,
    "play flavor": 'play {' in build,
    "no accompanist webview": "accompanist-webview" not in build and "com.google.accompanist.web" not in po_activity.read_text(),
    "native WebView": "webview_native" in layout,
    "play broad storage removed": "MANAGE_EXTERNAL_STORAGE" in play_manifest.read_text() and 'tools:node="remove"' in play_manifest.read_text(),
    "share input validated": "InSaveInputPolicy.normalizeHttpUrl(extractedUrl)" in share,
    "Hub input validated": "InSaveInputPolicy.classify(rawInput)" in hub,
    "Cobalt TLS policy": "normalizeProviderEndpoint" in cobalt,
    "B fallback ladder": "anonymousYoutubeFallbackClients" in worker and "inSaveYoutubeClientOverride" in ytdlp,
    "diagnostic redaction": "InSaveRedactor.redact(line)" in worker,
    "token logs redacted": "secret values redacted" in generator and "value redacted" in pot_webview,
    "Room mismatch intentional": "RoomWarnings.QUERY_MISMATCH" in tdao,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("InSave v0.18.0 hardening contract failed: " + ", ".join(failed))

print("InSave v0.18.0 architecture/security/build hardening: PASS")
