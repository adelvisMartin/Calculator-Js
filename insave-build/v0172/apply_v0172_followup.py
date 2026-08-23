from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
repo_path = root / 'database/repository/ResultRepository.kt'
history_path = root / 'ui/downloads/HistoryFragment.kt'

hub = hub_path.read_text()
repo = repo_path.read_text()
history = history_path.read_text()

# Make the home input clearly behave as a search field.
hub = hub.replace(
    'hint = "Pega un enlace de YouTube, Instagram, Facebook o TikTok"',
    'hint = "Busca una canción, artista o pega un enlace"',
    1,
)
hub = hub.replace('smallButton("Analizar") { openUrlAs(DownloadType.audio) }', 'smallButton("Buscar audio") { openUrlAs(DownloadType.audio) }', 1)
hub = hub.replace('primaryButton("Descargar MP3") { openUrlAs(DownloadType.audio) }', 'primaryButton("Buscar / descargar MP3") { openUrlAs(DownloadType.audio) }', 1)
hub = hub.replace('secondaryButton("Descargar video") { openUrlAs(DownloadType.video) }', 'secondaryButton("Buscar / descargar video") { openUrlAs(DownloadType.video) }', 1)

# The primary audio/video actions previously discarded text that was not a URL.
old = '''        val url = if (::urlInput.isInitialized) normalizeUrl(urlInput.text.toString()) else null
        if (url == null) {
            openDownloader(type)
            return
        }
'''
new = '''        val rawInput = if (::urlInput.isInitialized) urlInput.text.toString().trim() else ""
        val url = normalizeUrl(rawInput)
        if (url == null) {
            if (rawInput.isBlank()) {
                openDownloader(type)
            } else {
                prefs.edit()
                    .putString("preferred_download_type", type.toString())
                    .putBoolean("remember_download_type", false)
                    .putString("search_engine", "ytsearch")
                    .apply()
                startActivity(Intent(this, MainActivity::class.java).apply {
                    action = Intent.ACTION_SEARCH
                    putExtra("insave_search_query", rawInput)
                })
                toast("Buscando: $rawInput")
            }
            return
        }
'''
if old in hub:
    hub = hub.replace(old, new, 1)
elif 'putExtra("insave_search_query", rawInput)' not in hub:
    raise SystemExit('openUrlAs plain-text search anchor missing')

# NewPipe search remains first. If it fails OR returns no results, make yt-dlp
# execute a real search expression instead of interpreting bare text as a URL.
repo_old = '''        val items = if (res.isSuccess) {
            res.getOrNull()!!
        }else{
            //fallback to yt-dlp
            ytdlpUtil.getFromYTDL(inputQuery, resultsGenerated = {})
        }
'''
repo_new = '''        val items = if (res.isSuccess && !res.getOrNull().isNullOrEmpty()) {
            res.getOrNull()!!
        }else{
            // InSave fallback: execute a real YouTube search for plain text.
            ytdlpUtil.getFromYTDL("ytsearch10:$inputQuery", resultsGenerated = {})
        }
'''
if repo_old in repo:
    repo = repo.replace(repo_old, repo_new, 1)
elif 'ytsearch10:$inputQuery' not in repo:
    raise SystemExit('ResultRepository ytsearch fallback anchor missing')

# The downloaded-media icon in upstream HistoryFragment called SHARE rather
# than PLAY. Open the existing media file with Android ACTION_VIEW instead.
history_old = '''    override fun onButtonClick(itemID: Long, isPresent: Boolean) {
        if (isPresent){
            lifecycleScope.launch {
                val item = withContext(Dispatchers.IO){
                    historyViewModel.getByID(itemID)
                }

                item?.apply {
                    FileUtil.shareFileIntent(requireContext(), item.downloadPath)
                }
            }

        }
    }
'''
history_new = '''    override fun onButtonClick(itemID: Long, isPresent: Boolean) {
        if (!isPresent) return
        lifecycleScope.launch {
            val item = withContext(Dispatchers.IO) { historyViewModel.getByID(itemID) }
            val playablePath = item?.downloadPath?.firstOrNull { FileUtil.exists(it) }
                ?: item?.downloadPath?.firstOrNull { it.isNotBlank() }
            if (playablePath.isNullOrBlank()) {
                Toast.makeText(requireContext(), "No encontré el archivo descargado.", Toast.LENGTH_SHORT).show()
                return@launch
            }
            runCatching { FileUtil.openFileIntent(requireContext(), playablePath) }
                .onFailure {
                    Toast.makeText(requireContext(), "No hay un reproductor compatible para este archivo.", Toast.LENGTH_SHORT).show()
                }
        }
    }
'''
if history_old in history:
    history = history.replace(history_old, history_new, 1)
elif 'FileUtil.openFileIntent(requireContext(), playablePath)' not in history:
    raise SystemExit('History playback anchor missing')

hub_path.write_text(hub)
repo_path.write_text(repo)
history_path.write_text(history)

checks = {
    'intuitive search hint': 'Busca una canción, artista o pega un enlace' in hub,
    'audio/video plain search': 'putExtra("insave_search_query", rawInput)' in hub,
    'yt-dlp search fallback': 'ytsearch10:$inputQuery' in repo,
    'history playback': 'FileUtil.openFileIntent(requireContext(), playablePath)' in history,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave v0.17.2 follow-up contract failed: ' + ', '.join(failed))
print('InSave v0.17.2 search/history follow-up contract: PASS')
