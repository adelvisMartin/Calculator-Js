from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
ytdlp_path = root / 'util/extractors/ytdlp/YTDLPUtil.kt'
manifest_path = Path('upstream/app/src/main/AndroidManifest.xml')

hub = hub_path.read_text()

# --- Android imports required by automatic local/sideload status discovery ---
if 'import android.Manifest\n' not in hub:
    hub = hub.replace('import android.app.Activity\n', 'import android.app.Activity\nimport android.Manifest\n', 1)
if 'import android.content.pm.PackageManager\n' not in hub:
    hub = hub.replace('import android.content.Intent\n', 'import android.content.Intent\nimport android.content.pm.PackageManager\n', 1)
if 'import android.provider.Settings\n' not in hub:
    hub = hub.replace('import android.provider.MediaStore\n', 'import android.provider.MediaStore\nimport android.provider.Settings\n', 1)
if 'import androidx.core.content.ContextCompat\n' not in hub:
    hub = hub.replace('import androidx.documentfile.provider.DocumentFile\n', 'import androidx.core.content.ContextCompat\nimport androidx.documentfile.provider.DocumentFile\n', 1)

# --- One launcher only for Android 10 and below. Android 11+ uses Special App Access. ---
launcher_anchor = '''    private val businessTreeLauncher = registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        uri?.let { persistStatusTree(InSaveStatusSource.WHATSAPP_BUSINESS, it) }
    }
'''
launcher_insert = launcher_anchor + '''    private val legacyStoragePermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (currentTab == InSaveTab.STATUSES) showTab(InSaveTab.STATUSES)
    }
'''
if 'legacyStoragePermissionLauncher' not in hub:
    if launcher_anchor not in hub:
        raise SystemExit('legacy permission launcher anchor missing')
    hub = hub.replace(launcher_anchor, launcher_insert, 1)

# --- Returning from Android's Special App Access screen must immediately refresh Statuses. ---
resume_old = '''    override fun onResume() {
        super.onResume()
        if (currentTab == InSaveTab.HOME && ::urlInput.isInitialized) {
            urlInput.postDelayed({ autoPasteUrlIfAllowed() }, 250)
        }
    }
'''
resume_new = '''    override fun onResume() {
        super.onResume()
        if (currentTab == InSaveTab.HOME && ::urlInput.isInitialized) {
            urlInput.postDelayed({ autoPasteUrlIfAllowed() }, 250)
        } else if (currentTab == InSaveTab.STATUSES && ::contentHost.isInitialized) {
            contentHost.postDelayed({
                if (currentTab == InSaveTab.STATUSES) showTab(InSaveTab.STATUSES)
            }, 250)
        }
    }
'''
if resume_old in hub:
    hub = hub.replace(resume_old, resume_new, 1)
elif 'currentTab == InSaveTab.STATUSES && ::contentHost.isInitialized' not in hub:
    raise SystemExit('onResume anchor missing')

# --- Internal bitrate values must match upstream YTDLnis values (lowercase k). ---
hub = hub.replace('"320K"', '"320k"').replace('"256K"', '"256k"').replace('"192K"', '"192k"')
hub = hub.replace('.removeSuffix("K")', '.removeSuffix("k")')

# --- Conservative recovery defaults. Keep post-processing simple until real-device gates pass. ---
default_anchor = '''            .putBoolean("auto_update_ytdlp", true)
            .putBoolean("remember_download_type", false)
'''
default_insert = '''            .putBoolean("auto_update_ytdlp", true)
            .putBoolean("insave_newpipe_audio_primary", true)
            .putBoolean("use_cookies", false)
            .putBoolean("use_sponsorblock", false)
            .putBoolean("embed_thumbnail", false)
            .putBoolean("crop_thumbnail", false)
            .putBoolean("log_downloads", true)
            .putBoolean("cache_downloads", true)
            .putString("retries", "5")
            .putString("fragment_retries", "5")
            .putString("socket_timeout", "15")
            .putBoolean("remember_download_type", false)
'''
if '.putBoolean("insave_newpipe_audio_primary", true)' not in hub:
    if default_anchor not in hub:
        raise SystemExit('InSave defaults anchor missing')
    hub = hub.replace(default_anchor, default_insert, 1)

# --- Replace SAF-first States UI with automatic scan first, SAF only as fallback. ---
status_start = '''        val stored = prefs.getString(statusKey(statusSource), null)?.let(Uri::parse)
        if (stored == null) {
'''
status_end = '''        return ScrollView(this).apply { addView(root) }
    }

    private fun buildDownloadsView(): View {
'''
start_index = hub.find(status_start)
end_index = hub.find(status_end, start_index)
if start_index < 0 or end_index < 0:
    raise SystemExit('Statuses UI block anchors missing')
new_status_block = '''        val stored = prefs.getString(statusKey(statusSource), null)?.let(Uri::parse)
        val automaticGranted = automaticStatusAccessGranted()

        if (automaticGranted) {
            val info = TextView(this).apply {
                text = "Buscando estados automáticamente…"
                setTextColor(MUTED)
                setPadding(dp(2), dp(14), dp(2), dp(10))
            }
            root.addView(info)
            val recycler = RecyclerView(this).apply {
                layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)
                overScrollMode = View.OVER_SCROLL_NEVER
                isNestedScrollingEnabled = false
            }
            root.addView(recycler, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
            ))
            root.addView(secondaryButton("Revisar acceso automático") { requestAutomaticStatusAccess() })
            loadAutomaticStatuses(info, recycler)
        } else {
            root.addView(card().apply {
                addView(sectionTitle("Activar Estados automáticos"))
                addView(body("InSave local puede leer automáticamente WhatsApp y WhatsApp Business desde Android/media. Autoriza el acceso especial una sola vez; después los estados aparecerán al entrar aquí, como en las versiones históricas."))
                addView(primaryButton("Activar acceso automático") { requestAutomaticStatusAccess() })
                if (stored != null) {
                    addView(secondaryButton("Usar acceso de carpeta anterior") {
                        val info = TextView(this@InSaveHubActivity).apply {
                            text = "Cargando acceso anterior…"
                            setTextColor(MUTED)
                        }
                        val recycler = RecyclerView(this@InSaveHubActivity).apply {
                            layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)
                        }
                        root.addView(info)
                        root.addView(recycler)
                        loadStatuses(stored, info, recycler)
                    })
                }
                addView(secondaryButton("Elegir carpeta manualmente (fallback)") { launchStatusTree(statusSource) })
            })
        }
        return ScrollView(this).apply { addView(root) }
    }

    private fun automaticStatusAccessGranted(): Boolean = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        Environment.isExternalStorageManager()
    } else {
        ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED
    }

    private fun requestAutomaticStatusAccess() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val appIntent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                data = Uri.parse("package:$packageName")
            }
            runCatching { startActivity(appIntent) }.getOrElse {
                startActivity(Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION))
            }
        } else {
            legacyStoragePermissionLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
    }

    private fun loadAutomaticStatuses(info: TextView, recycler: RecyclerView) {
        val sourceSnapshot = statusSource
        val filterSnapshot = statusFilter
        lifecycleScope.launch(Dispatchers.IO) {
            val all = AutomaticStatusRepository().scan(sourceSnapshot)
            val filtered = all.filter {
                if (filterSnapshot == StatusFilter.IMAGES) it.mime.startsWith("image/") else it.mime.startsWith("video/")
            }
            withContext(Dispatchers.Main) {
                if (currentTab != InSaveTab.STATUSES || sourceSnapshot != statusSource || filterSnapshot != statusFilter) return@withContext
                val images = all.count { it.mime.startsWith("image/") }
                val videos = all.count { it.mime.startsWith("video/") }
                info.text = if (all.isEmpty()) {
                    "No hay estados visibles todavía. Abre WhatsApp y visualiza algún estado; InSave actualizará esta vista al volver."
                } else {
                    "Imágenes · $images     Videos · $videos"
                }
                recycler.adapter = StatusAdapter(filtered)
            }
        }
    }

    private fun buildDownloadsView(): View {
'''
hub = hub[:start_index] + new_status_block + hub[end_index + len(status_end):]

# Remove the artificial state count cap from the SAF fallback too.
hub = hub.replace('                ?.take(180)\n', '')

hub_path.write_text(hub)

# --- Restore all-files permission for LOCAL/SIDELOAD automatic WhatsApp discovery. ---
manifest = manifest_path.read_text()
manage = 'android.permission.MANAGE_EXTERNAL_STORAGE'
if manage not in manifest:
    internet = '    <uses-permission android:name="android.permission.INTERNET" />\n'
    permission = '''    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" tools:ignore="ScopedStorage" />
'''
    if internet not in manifest:
        raise SystemExit('Manifest INTERNET anchor missing')
    manifest = manifest.replace(internet, internet + permission, 1)
if 'android:requestLegacyExternalStorage="true"' not in manifest:
    manifest = manifest.replace('<application\n', '<application\n        android:requestLegacyExternalStorage="true"\n', 1)
manifest_path.write_text(manifest)

# --- YouTube recovery: NewPipe+BotGuard resolves a fresh signed audio stream; yt-dlp remains fallback. ---
ytdlp = ytdlp_path.read_text()
if 'import com.deniscerri.ytdl.util.extractors.newpipe.NewPipeUtil\n' not in ytdlp:
    ytdlp = ytdlp.replace(
        'import com.deniscerri.ytdl.util.FormatUtil\n',
        'import com.deniscerri.ytdl.util.FormatUtil\nimport com.deniscerri.ytdl.util.extractors.newpipe.NewPipeUtil\n',
        1,
    )

property_anchor = '    private val handler = Handler(Looper.getMainLooper())\n'
property_insert = property_anchor + '''    private val inSaveNewPipe by lazy { NewPipeUtil(context) }
'''
if 'private val inSaveNewPipe by lazy' not in ytdlp:
    if property_anchor not in ytdlp:
        raise SystemExit('YTDLPUtil handler anchor missing')
    ytdlp = ytdlp.replace(property_anchor, property_insert, 1)

helper_anchor = '''    private fun YTDLRequest.setYoutubeExtractorArgs(url: String?) {
'''
helper = '''    private fun resolveInSaveYoutubeAudioDirectUrl(url: String): String? {
        if (!sharedPreferences.getBoolean("insave_newpipe_audio_primary", true)) return null
        return kotlin.runCatching {
            inSaveNewPipe.getFormats(url).getOrThrow()
                .asSequence()
                .filter { !it.url.isNullOrBlank() }
                .filter { it.vcodec.isBlank() || it.vcodec.equals("none", ignoreCase = true) }
                .filter { it.acodec.isNotBlank() && !it.acodec.equals("none", ignoreCase = true) }
                .maxByOrNull { format ->
                    format.tbr
                        ?.lowercase()
                        ?.removeSuffix("kbps")
                        ?.removeSuffix("k")
                        ?.trim()
                        ?.toDoubleOrNull()
                        ?: 0.0
                }
                ?.url
        }.getOrNull()
    }

'''
if 'resolveInSaveYoutubeAudioDirectUrl' not in ytdlp:
    if helper_anchor not in ytdlp:
        raise SystemExit('YTDLPUtil YouTube helper anchor missing')
    ytdlp = ytdlp.replace(helper_anchor, helper + helper_anchor, 1)

build_anchor = '''    fun buildYTDLRequest(downloadItem: DownloadItem) : YTDLRequest {
        var useItemURL = sharedPreferences.getBoolean("use_itemurl_instead_playlisturl", false)
'''
build_insert = '''    fun buildYTDLRequest(downloadItem: DownloadItem) : YTDLRequest {
        val inSaveDirectYoutubeAudioUrl = if (
            downloadItem.type == DownloadType.audio && downloadItem.url.isYoutubeURL()
        ) resolveInSaveYoutubeAudioDirectUrl(downloadItem.url) else null

        var useItemURL = sharedPreferences.getBoolean("use_itemurl_instead_playlisturl", false)
        if (!inSaveDirectYoutubeAudioUrl.isNullOrBlank()) useItemURL = true
'''
if 'val inSaveDirectYoutubeAudioUrl = if (' not in ytdlp:
    if build_anchor not in ytdlp:
        raise SystemExit('buildYTDLRequest anchor missing')
    ytdlp = ytdlp.replace(build_anchor, build_insert, 1)

request_anchor = '''        val ytDlRequest = if (downloadItem.url.endsWith(".txt")) {
'''
request_replacement = '''        val ytDlRequest = if (!inSaveDirectYoutubeAudioUrl.isNullOrBlank()) {
            YTDLRequest(inSaveDirectYoutubeAudioUrl)
        } else if (downloadItem.url.endsWith(".txt")) {
'''
if 'YTDLRequest(inSaveDirectYoutubeAudioUrl)' not in ytdlp:
    if request_anchor not in ytdlp:
        raise SystemExit('ytDlRequest construction anchor missing')
    ytdlp = ytdlp.replace(request_anchor, request_replacement, 1)

# Do not apply YouTube extractor args to the already signed direct stream.
ytdlp = ytdlp.replace(
    '            if (downloadItem.url.isYoutubeURL()) {\n                ytDlRequest.setYoutubeExtractorArgs(downloadItem.url)\n            }',
    '            if (downloadItem.url.isYoutubeURL() && inSaveDirectYoutubeAudioUrl.isNullOrBlank()) {\n                ytDlRequest.setYoutubeExtractorArgs(downloadItem.url)\n            }',
    1,
)

# Avoid loading stale YouTube info-json when primary direct resolution succeeded.
ytdlp = ytdlp.replace(
    '                !request.toString().contains("--download-sections")',
    '                !request.toString().contains("--download-sections") &&\n                inSaveDirectYoutubeAudioUrl.isNullOrBlank()',
    1,
)

# SponsorBlock needs YouTube extraction metadata; skip it for a signed media URL.
ytdlp = ytdlp.replace(
    '            if (sharedPreferences.getBoolean("use_sponsorblock", true)){',
    '            if (inSaveDirectYoutubeAudioUrl.isNullOrBlank() && sharedPreferences.getBoolean("use_sponsorblock", false)){',
    1,
)

# Writing a separate thumbnail through YouTube extraction is not part of the minimal recovery path.
ytdlp = ytdlp.replace(
    '            if (downloadItem.SaveThumb) {',
    '            if (downloadItem.SaveThumb && inSaveDirectYoutubeAudioUrl.isNullOrBlank()) {',
    1,
)

# Do not force a YouTube format-id on a direct signed audio file.
ytdlp = ytdlp.replace(
    '                if (audioQualityId.isNotBlank()) {\n',
    '                if (inSaveDirectYoutubeAudioUrl.isNullOrBlank() && audioQualityId.isNotBlank()) {\n',
    1,
)

# Format sorting against a single generic direct stream can incorrectly reject it.
ytdlp = ytdlp.replace(
    '                if(formatSorting.isNotEmpty()) {\n                    request.addOption("-S", formatSorting.joinToString(","))\n                }',
    '                if(inSaveDirectYoutubeAudioUrl.isNullOrBlank() && formatSorting.isNotEmpty()) {\n                    request.addOption("-S", formatSorting.joinToString(","))\n                }',
    1,
)

# A direct stream has no thumbnail metadata; embedding it can turn a successful audio conversion into a failure.
ytdlp = ytdlp.replace(
    '                    if (downloadItem.audioPreferences.embedThumb){',
    '                    if (downloadItem.audioPreferences.embedThumb && inSaveDirectYoutubeAudioUrl.isNullOrBlank()){',
    1,
)

ytdlp_path.write_text(ytdlp)

# --- Release contract: fail fast if a future edit removes the recovered behavior. ---
checks = {
    'automatic manager check': 'Environment.isExternalStorageManager()' in hub_path.read_text(),
    'automatic repository': 'AutomaticStatusRepository().scan' in hub_path.read_text(),
    'SAF fallback retained': 'Elegir carpeta manualmente (fallback)' in hub_path.read_text(),
    'no 180 state cap': '.take(180)' not in hub_path.read_text(),
    'all files manifest': manage in manifest_path.read_text(),
    'lowercase bitrate': '"320k"' in hub_path.read_text() and '"320K"' not in hub_path.read_text(),
    'newpipe primary': 'resolveInSaveYoutubeAudioDirectUrl' in ytdlp_path.read_text(),
    'signed direct request': 'YTDLRequest(inSaveDirectYoutubeAudioUrl)' in ytdlp_path.read_text(),
    'yt-dlp fallback': 'else if (downloadItem.url.endsWith(".txt"))' in ytdlp_path.read_text(),
    'thumbnail bypass': 'embedThumb && inSaveDirectYoutubeAudioUrl.isNullOrBlank()' in ytdlp_path.read_text(),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave v0.17 recovery contract failed: ' + ', '.join(failed))
print('InSave v0.17 LKG recovery contract: PASS')
