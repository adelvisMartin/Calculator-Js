from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
main_path = root / 'MainActivity.kt'
home_path = root / 'ui/HomeFragment.kt'
ytdlp_path = root / 'util/extractors/ytdlp/YTDLPUtil.kt'
manifest_path = Path('upstream/app/src/main/AndroidManifest.xml')

hub = hub_path.read_text()
main = main_path.read_text()
home = home_path.read_text()
ytdlp = ytdlp_path.read_text()
manifest = manifest_path.read_text()

# ---------------------------------------------------------------------------
# Imports + local UI state.
# ---------------------------------------------------------------------------
if 'import androidx.activity.addCallback\n' not in hub:
    hub = hub.replace('import androidx.activity.result.contract.ActivityResultContracts\n', 'import androidx.activity.addCallback\nimport androidx.activity.result.contract.ActivityResultContracts\n', 1)
if 'import androidx.core.widget.doAfterTextChanged\n' not in hub:
    hub = hub.replace('import androidx.core.content.ContextCompat\n', 'import androidx.core.content.ContextCompat\nimport androidx.core.widget.doAfterTextChanged\n', 1)
if 'import android.content.ContentUris\n' not in hub:
    hub = hub.replace('import android.content.ContentValues\n', 'import android.content.ContentUris\nimport android.content.ContentValues\n', 1)

state_anchor = '    private var statusFilter = StatusFilter.IMAGES\n'
if 'private var statusSearchQuery = ""' not in hub:
    if state_anchor not in hub:
        raise SystemExit('statusFilter state anchor missing')
    hub = hub.replace(state_anchor, state_anchor + '    private var statusSearchQuery = ""\n', 1)

# ---------------------------------------------------------------------------
# Correct Android back behavior in the InSave shell.
# Back from an internal InSave tab returns Home; back from Home finishes only
# this activity. It must not immediately kill the complete task.
# ---------------------------------------------------------------------------
oncreate_anchor = '''        buildShell()
        consumeIncomingIntent(intent)
    }
'''
oncreate_insert = '''        buildShell()
        onBackPressedDispatcher.addCallback(this) {
            if (currentTab != InSaveTab.HOME) {
                showTab(InSaveTab.HOME)
            } else {
                finish()
            }
        }
        consumeIncomingIntent(intent)
    }
'''
if 'onBackPressedDispatcher.addCallback(this)' not in hub:
    if oncreate_anchor not in hub:
        raise SystemExit('Hub onCreate anchor missing')
    hub = hub.replace(oncreate_anchor, oncreate_insert, 1)

# The maintained engine had a HomeFragment callback that called finishAffinity,
# which also destroys the underlying InSave shell. Close only MainActivity.
home = home.replace('                mainActivity?.finishAffinity()\n', '                mainActivity?.finish()\n')

# ---------------------------------------------------------------------------
# Statuses: searchable and truly scrollable beyond the six visible cards.
# Keep the compact 2-column UI, but give RecyclerView its own bounded viewport
# and internal scrolling instead of embedding a non-scrolling WRAP_CONTENT list.
# ---------------------------------------------------------------------------
status_info_anchor = '''            val info = TextView(this).apply {
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
'''
status_info_new = '''            val info = TextView(this).apply {
                text = "Buscando estados automáticamente…"
                setTextColor(MUTED)
                setPadding(dp(2), dp(14), dp(2), dp(8))
            }
            root.addView(info)

            val statusSearch = EditText(this).apply {
                hint = "Buscar estados…"
                setHintTextColor(MUTED)
                setTextColor(TEXT)
                textSize = 14f
                isSingleLine = true
                setText(statusSearchQuery)
                backgroundTintList = ColorStateList.valueOf(ACCENT)
                setPadding(dp(10), dp(6), dp(10), dp(6))
            }
            root.addView(statusSearch, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(52)
            ))

            val recycler = RecyclerView(this).apply {
                layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)
                overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS
                isNestedScrollingEnabled = true
            }
            root.addView(recycler, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(530)
            ))
            statusSearch.doAfterTextChanged {
                statusSearchQuery = it?.toString().orEmpty()
                loadAutomaticStatuses(info, recycler)
            }
'''
if 'hint = "Buscar estados…"' not in hub:
    if status_info_anchor not in hub:
        raise SystemExit('Automatic statuses recycler anchor missing')
    hub = hub.replace(status_info_anchor, status_info_new, 1)

# SAF fallback should also scroll independently when used.
hub = hub.replace(
    'val recycler = RecyclerView(this@InSaveHubActivity).apply {\n                            layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)\n                        }',
    'val recycler = RecyclerView(this@InSaveHubActivity).apply {\n                            layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)\n                            isNestedScrollingEnabled = true\n                        }'
)

# Apply the status search query to the complete result set. Empty query shows
# every matching media state; no artificial six-item limit is introduced.
auto_filter_old = '''            val filtered = all.filter {
                if (filterSnapshot == StatusFilter.IMAGES) it.mime.startsWith("image/") else it.mime.startsWith("video/")
            }
'''
auto_filter_new = '''            val querySnapshot = statusSearchQuery.trim()
            val filtered = all.filter {
                val mediaMatches = if (filterSnapshot == StatusFilter.IMAGES) it.mime.startsWith("image/") else it.mime.startsWith("video/")
                val searchMatches = querySnapshot.isBlank() || it.name.contains(querySnapshot, ignoreCase = true)
                mediaMatches && searchMatches
            }
'''
if 'val querySnapshot = statusSearchQuery.trim()' not in hub:
    count = hub.count(auto_filter_old)
    if count < 1:
        raise SystemExit('Automatic status filter anchor missing')
    hub = hub.replace(auto_filter_old, auto_filter_new, 1)

# ---------------------------------------------------------------------------
# Search by song/artist name from the InSave home screen.
# URL -> direct parse. Plain text -> open maintained search UI and immediately
# launch a ytsearch query, restoring the historical intuitive behavior.
# ---------------------------------------------------------------------------
search_start = hub.find('    private fun openAudioSearch() {')
search_end = hub.find('    private fun openDownloader(type: DownloadType) {', search_start)
if search_start < 0 or search_end < 0:
    raise SystemExit('openAudioSearch boundaries missing')
new_search = '''    private fun openAudioSearch() {
        val bitrate = prefs.getString("audio_bitrate", "320K").orEmpty().ifBlank { "320K" }
        prefs.edit()
            .putString("preferred_download_type", DownloadType.audio.toString())
            .putString("audio_format", "mp3")
            .putString("audio_bitrate", bitrate)
            .putBoolean("remember_download_type", false)
            .putBoolean("insave_playlist_mp3_enabled", true)
            .apply()

        val raw = if (::urlInput.isInitialized) urlInput.text.toString().trim() else ""
        val normalized = normalizeUrl(raw)
        startActivity(Intent(this, MainActivity::class.java).apply {
            if (!normalized.isNullOrBlank()) {
                action = Intent.ACTION_VIEW
                putExtra("insave_query", normalized)
            } else if (raw.isNotBlank()) {
                action = Intent.ACTION_SEARCH
                putExtra("insave_search_query", raw)
            } else {
                putExtra("insave_open_search", true)
            }
        })
        toast(if (raw.isBlank()) "Escribe canción o artista para buscar" else "Buscando: $raw")
    }

'''
hub = hub[:search_start] + new_search + hub[search_end:]

# MainActivity route for plain-text search and explicit open-search intent.
main_anchor = '''        val inSaveQuery = intent.getStringExtra("insave_query")
        if (!inSaveQuery.isNullOrBlank()) {
            intent.removeExtra("insave_query")
            val bundle = Bundle().apply { putString("url", inSaveQuery) }
            navController.popBackStack(R.id.homeFragment, true)
            navController.navigate(R.id.homeFragment, bundle)
            return
        }

        val action = intent.action
'''
main_new = '''        val inSaveQuery = intent.getStringExtra("insave_query")
        if (!inSaveQuery.isNullOrBlank()) {
            intent.removeExtra("insave_query")
            val bundle = Bundle().apply { putString("url", inSaveQuery) }
            navController.popBackStack(R.id.homeFragment, true)
            navController.navigate(R.id.homeFragment, bundle)
            return
        }

        val inSaveSearchQuery = intent.getStringExtra("insave_search_query")
        if (!inSaveSearchQuery.isNullOrBlank()) {
            intent.removeExtra("insave_search_query")
            val bundle = Bundle().apply { putString("insave_search_query", inSaveSearchQuery) }
            navController.popBackStack(R.id.homeFragment, true)
            navController.navigate(R.id.homeFragment, bundle)
            return
        }

        if (intent.getBooleanExtra("insave_open_search", false)) {
            intent.removeExtra("insave_open_search")
            val bundle = Bundle().apply { putBoolean("search", true) }
            navController.popBackStack(R.id.homeFragment, true)
            navController.navigate(R.id.homeFragment, bundle)
            return
        }

        val action = intent.action
'''
if 'val inSaveSearchQuery = intent.getStringExtra("insave_search_query")' not in main:
    if main_anchor not in main:
        raise SystemExit('MainActivity InSave query bridge anchor missing')
    main = main.replace(main_anchor, main_new, 1)

# HomeFragment automatically opens the search view, inserts the raw query, and
# triggers the maintained search engine (ytsearch by InSave default).
home_arg_anchor = '''        if (inputQueries != null) {
            lifecycleScope.launch(Dispatchers.IO){
                resultViewModel.deleteAll()
                resultViewModel.parseQueries(inputQueries!!){}
                inputQueries = null
            }
        }

        searchView?.addTransitionListener'''
home_arg_new = '''        if (inputQueries != null) {
            lifecycleScope.launch(Dispatchers.IO){
                resultViewModel.deleteAll()
                resultViewModel.parseQueries(inputQueries!!){}
                inputQueries = null
            }
        }

        arguments?.getString("insave_search_query")?.takeIf { it.isNotBlank() }?.let { inSaveSearch ->
            arguments?.remove("insave_search_query")
            requireView().post {
                searchBar?.performClick()
                searchView?.setText(inSaveSearch)
                searchView?.editText?.setText(inSaveSearch)
                searchView?.editText?.setSelection(inSaveSearch.length)
                searchView?.editText?.postDelayed({
                    searchView?.let { initSearch(it) }
                }, 250)
            }
        }

        searchView?.addTransitionListener'''
if 'arguments?.getString("insave_search_query")' not in home:
    if home_arg_anchor not in home:
        raise SystemExit('HomeFragment InSave search anchor missing')
    home = home.replace(home_arg_anchor, home_arg_new, 1)

# ---------------------------------------------------------------------------
# Downloaded media playback from InSave itself.
# Surface recent InSave Audio/Video MediaStore entries and open the actual
# content URI with a media-capable viewer/player instead of a stale file path.
# ---------------------------------------------------------------------------
download_anchor = '''        root.addView(card().apply {
            addView(sectionTitle("Limpiar cola"))
'''
recent_card = '''        root.addView(card().apply {
            addView(sectionTitle("Reproducir descargados"))
            addView(body("Toca un archivo para reproducirlo con el reproductor disponible en Android."))
            val recent = recentInSaveDownloads(20)
            if (recent.isEmpty()) {
                addView(body("Todavía no encontré archivos de InSave en la biblioteca multimedia."))
            } else {
                recent.forEach { media ->
                    addView(secondaryButton("▶ ${media.second}") {
                        playDownloadedMedia(media.first, media.third)
                    })
                }
            }
        })
        root.addView(card().apply {
            addView(sectionTitle("Limpiar cola"))
'''
if 'sectionTitle("Reproducir descargados")' not in hub:
    if download_anchor not in hub:
        raise SystemExit('Downloads card anchor missing')
    hub = hub.replace(download_anchor, recent_card, 1)

helper_anchor = '    private fun openUrlAs(type: DownloadType) {\n'
play_helpers = '''    private fun recentInSaveDownloads(limit: Int): List<Triple<Uri, String, String>> = runCatching {
        val collection = MediaStore.Files.getContentUri("external")
        val projection = arrayOf(
            MediaStore.Files.FileColumns._ID,
            MediaStore.Files.FileColumns.DISPLAY_NAME,
            MediaStore.Files.FileColumns.MIME_TYPE,
            MediaStore.Files.FileColumns.RELATIVE_PATH,
        )
        val selection = "${MediaStore.Files.FileColumns.RELATIVE_PATH} LIKE ?"
        val args = arrayOf("%InSave/%")
        val sort = "${MediaStore.Files.FileColumns.DATE_ADDED} DESC"
        val out = mutableListOf<Triple<Uri, String, String>>()
        contentResolver.query(collection, projection, selection, args, sort)?.use { cursor ->
            val idCol = cursor.getColumnIndexOrThrow(MediaStore.Files.FileColumns._ID)
            val nameCol = cursor.getColumnIndexOrThrow(MediaStore.Files.FileColumns.DISPLAY_NAME)
            val mimeCol = cursor.getColumnIndexOrThrow(MediaStore.Files.FileColumns.MIME_TYPE)
            while (cursor.moveToNext() && out.size < limit) {
                val mime = cursor.getString(mimeCol).orEmpty()
                if (!mime.startsWith("audio/") && !mime.startsWith("video/")) continue
                val id = cursor.getLong(idCol)
                val uri = ContentUris.withAppendedId(collection, id)
                out += Triple(uri, cursor.getString(nameCol).orEmpty().ifBlank { "Archivo descargado" }, mime)
            }
        }
        out
    }.getOrDefault(emptyList())

    private fun playDownloadedMedia(uri: Uri, mime: String) {
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, mime.ifBlank { "*/*" })
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        runCatching { startActivity(intent) }
            .onFailure { toast("No encontré un reproductor compatible para este archivo.") }
    }

'''
if 'private fun recentInSaveDownloads(limit: Int)' not in hub:
    if helper_anchor not in hub:
        raise SystemExit('openUrlAs helper anchor missing')
    hub = hub.replace(helper_anchor, play_helpers + helper_anchor, 1)

# ---------------------------------------------------------------------------
# Stronger but bounded audio loudness. Apply only to MP3 extraction and only
# when the InSave boost toggle is enabled. Loudnorm raises perceived loudness
# while capping true peak to reduce clipping risk.
# ---------------------------------------------------------------------------
quality_anchor = '''                    request.addOption("--audio-quality", normalizedAudioBitrate)
                }
'''
quality_new = '''                    request.addOption("--audio-quality", normalizedAudioBitrate)
                }
                if (ext.equals("mp3", ignoreCase = true) && sharedPreferences.getBoolean("insave_loudness_boost", true)) {
                    request.addOption("--postprocessor-args", "ExtractAudio+ffmpeg:-af loudnorm=I=-9:TP=-1.0:LRA=7")
                }
'''
if 'loudnorm=I=-9:TP=-1.0:LRA=7' not in ytdlp:
    if quality_anchor not in ytdlp:
        raise SystemExit('YTDLP bitrate anchor missing for loudness boost')
    ytdlp = ytdlp.replace(quality_anchor, quality_new, 1)

# ---------------------------------------------------------------------------
# Branding: the reconstruction script decodes the approved logo into drawable.
# Point both launcher icons to it. This keeps the current UI palette untouched.
# ---------------------------------------------------------------------------
manifest = manifest.replace('android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/insave_logo"')
manifest = manifest.replace('android:roundIcon="@mipmap/ic_launcher_round"', 'android:roundIcon="@drawable/insave_logo"')

hub_path.write_text(hub)
main_path.write_text(main)
home_path.write_text(home)
ytdlp_path.write_text(ytdlp)
manifest_path.write_text(manifest)

checks = {
    'status search': 'hint = "Buscar estados…"' in hub and 'querySnapshot = statusSearchQuery.trim()' in hub,
    'status scroll': 'LinearLayout.LayoutParams.MATCH_PARENT, dp(530)' in hub and 'isNestedScrollingEnabled = true' in hub,
    'back shell': 'onBackPressedDispatcher.addCallback(this)' in hub,
    'back engine': 'mainActivity?.finishAffinity()' not in home,
    'plain search route': 'insave_search_query' in hub and 'insave_search_query' in main and 'insave_search_query' in home,
    'media playback': 'recentInSaveDownloads(20)' in hub and 'playDownloadedMedia' in hub,
    'loudness': 'loudnorm=I=-9:TP=-1.0:LRA=7' in ytdlp,
    'logo manifest': '@drawable/insave_logo' in manifest,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave v0.17.2 contract failed: ' + ', '.join(failed))

print('InSave v0.17.2 UX/playback/search/loudness contract: PASS')
