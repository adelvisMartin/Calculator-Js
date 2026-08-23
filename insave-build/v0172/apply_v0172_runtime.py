from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
home_path = root / 'ui/HomeFragment.kt'
repo_path = root / 'database/repository/ResultRepository.kt'
history_path = root / 'ui/downloads/HistoryFragment.kt'
ytdlp_path = root / 'util/extractors/ytdlp/YTDLPUtil.kt'
manifest_path = Path('upstream/app/src/main/AndroidManifest.xml')

hub = hub_path.read_text()
home = home_path.read_text()
repo = repo_path.read_text()
history = history_path.read_text()
ytdlp = ytdlp_path.read_text()
manifest = manifest_path.read_text()

# 1. Back navigation: tabs -> Inicio; engine -> previous InSave shell.
if 'import androidx.activity.addCallback\n' not in hub:
    hub = hub.replace('import androidx.activity.result.contract.ActivityResultContracts\n', 'import androidx.activity.addCallback\nimport androidx.activity.result.contract.ActivityResultContracts\n', 1)
anchor = '''        buildShell()
        consumeIncomingIntent(intent)
'''
replacement = '''        buildShell()
        onBackPressedDispatcher.addCallback(this) {
            if (currentTab != InSaveTab.HOME) showTab(InSaveTab.HOME) else moveTaskToBack(true)
        }
        consumeIncomingIntent(intent)
'''
if 'onBackPressedDispatcher.addCallback(this)' not in hub:
    if anchor not in hub: raise SystemExit('Hub back anchor missing')
    hub = hub.replace(anchor, replacement, 1)
home = home.replace('                mainActivity?.finishAffinity()\n', '                mainActivity?.finish()\n')

# 2. States: repository already returns every item. The bug is the RecyclerView
# being non-scrolling WRAP_CONTENT inside a ScrollView, which visually stops at
# three rows. Give it an independent viewport and scrolling.
auto_marker = 'val automaticGranted = automaticStatusAccessGranted()'
pos = hub.find(auto_marker)
if pos < 0: raise SystemExit('automatic statuses marker missing')
segment_end = hub.find('    private fun automaticStatusAccessGranted()', pos)
if segment_end < 0: raise SystemExit('automatic statuses end missing')
segment = hub[pos:segment_end]
segment = segment.replace('overScrollMode = View.OVER_SCROLL_NEVER', 'overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS')
segment = segment.replace('isNestedScrollingEnabled = false', 'isNestedScrollingEnabled = true')
segment = segment.replace(
    'LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT\n            ))',
    'LinearLayout.LayoutParams.MATCH_PARENT, dp(540)\n            ))',
    1,
)
segment = segment.replace(
    'text = "Buscando estados automáticamente…"',
    'text = "Buscando estados automáticamente… · desliza para ver todos"',
    1,
)
hub = hub[:pos] + segment + hub[segment_end:]
if 'isNestedScrollingEnabled = true' not in segment or 'dp(540)' not in segment:
    raise SystemExit('states scroll patch did not apply')

# 3. Main input is a search field. A song/artist name must not be discarded.
hub = hub.replace('hint = "Pega un enlace de YouTube, Instagram, Facebook o TikTok"', 'hint = "Busca una canción, artista o pega un enlace"', 1)
hub = hub.replace('smallButton("Analizar") { openUrlAs(DownloadType.audio) }', 'smallButton("Buscar audio") { openUrlAs(DownloadType.audio) }', 1)
hub = hub.replace('primaryButton("Descargar MP3") { openUrlAs(DownloadType.audio) }', 'primaryButton("Buscar / descargar MP3") { openUrlAs(DownloadType.audio) }', 1)
hub = hub.replace('secondaryButton("Descargar video") { openUrlAs(DownloadType.video) }', 'secondaryButton("Buscar / descargar video") { openUrlAs(DownloadType.video) }', 1)

open_old = '''        val url = if (::urlInput.isInitialized) normalizeUrl(urlInput.text.toString()) else null
        if (url == null) {
            openDownloader(type)
            return
        }
'''
open_new = '''        val rawInput = if (::urlInput.isInitialized) urlInput.text.toString().trim() else ""
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
                    action = Intent.ACTION_VIEW
                    putExtra("insave_query", rawInput)
                })
                toast("Buscando: $rawInput")
            }
            return
        }
'''
if open_old in hub:
    hub = hub.replace(open_old, open_new, 1)
elif 'putExtra("insave_query", rawInput)' not in hub:
    raise SystemExit('plain search openUrlAs anchor missing')

# Playlist patch created openAudioSearch; preserve plain text there too.
search_start = hub.find('    private fun openAudioSearch() {')
search_end = hub.find('    private fun openDownloader(type: DownloadType) {', search_start)
if search_start < 0 or search_end < 0: raise SystemExit('openAudioSearch boundaries missing')
new_audio_search = '''    private fun openAudioSearch() {
        val bitrate = prefs.getString("audio_bitrate", "320k").orEmpty().ifBlank { "320k" }
        prefs.edit()
            .putString("preferred_download_type", DownloadType.audio.toString())
            .putString("audio_format", "mp3")
            .putString("audio_bitrate", bitrate)
            .putBoolean("remember_download_type", false)
            .putBoolean("insave_playlist_mp3_enabled", true)
            .putString("search_engine", "ytsearch")
            .apply()
        val raw = if (::urlInput.isInitialized) urlInput.text.toString().trim() else ""
        startActivity(Intent(this, MainActivity::class.java).apply {
            if (raw.isNotBlank()) {
                action = Intent.ACTION_VIEW
                putExtra("insave_query", normalizeUrl(raw) ?: raw)
            }
        })
    }

'''
hub = hub[:search_start] + new_audio_search + hub[search_end:]

# HomeFragment used to remove non-URL args before parseQueries. Keep text.
home = home.replace(
    'val argList = url!!.split("\\n").filter { it.isURL() }.toMutableList()',
    'val argList = url!!.split("\\n").map { it.trim() }.filter { it.isNotBlank() }.toMutableList()',
    1,
)

# If NewPipe search fails OR is empty, yt-dlp must receive ytsearch, not bare text.
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
            ytdlpUtil.getFromYTDL("ytsearch10:$inputQuery", resultsGenerated = {})
        }
'''
if repo_old in repo:
    repo = repo.replace(repo_old, repo_new, 1)
elif 'ytsearch10:$inputQuery' not in repo:
    raise SystemExit('ytsearch fallback anchor missing')

# 4. The History play icon incorrectly called shareFileIntent. Open the media.
history_old = '''                item?.apply {
                    FileUtil.shareFileIntent(requireContext(), item.downloadPath)
                }
'''
history_new = '''                item?.apply {
                    val playablePath = item.downloadPath.firstOrNull { FileUtil.exists(it) }
                        ?: item.downloadPath.firstOrNull()
                    if (!playablePath.isNullOrBlank()) {
                        runCatching { FileUtil.openFileIntent(requireContext(), playablePath) }
                            .onFailure { Toast.makeText(requireContext(), "No hay un reproductor compatible.", Toast.LENGTH_SHORT).show() }
                    }
                }
'''
# Restrict replacement to onButtonClick region so contextual Share remains Share.
button_pos = history.find('    override fun onButtonClick(itemID: Long, isPresent: Boolean)')
if button_pos < 0: raise SystemExit('History onButtonClick missing')
button = history[button_pos:]
if history_old in button:
    button = button.replace(history_old, history_new, 1)
    history = history[:button_pos] + button
elif 'FileUtil.openFileIntent(requireContext(), playablePath)' not in button:
    raise SystemExit('History playback patch missing')

# 5. The UI switch existed but did not alter ffmpeg. Use bounded loudness
# normalization for MP3 with a -1 dB true-peak ceiling.
quality_anchor = '''                    request.addOption("--audio-quality", normalizedAudioBitrate)
                }
'''
quality_new = '''                    request.addOption("--audio-quality", normalizedAudioBitrate)
                }
                if (ext.equals("mp3", ignoreCase = true) && sharedPreferences.getBoolean("insave_loudness_boost", true)) {
                    request.addOption("--postprocessor-args", "ffmpeg:-af loudnorm=I=-9:TP=-1.0:LRA=7")
                }
'''
if 'loudnorm=I=-9:TP=-1.0:LRA=7' not in ytdlp:
    if quality_anchor not in ytdlp: raise SystemExit('loudness anchor missing')
    ytdlp = ytdlp.replace(quality_anchor, quality_new, 1)

# 6. Approved logo as launcher/round icon.
if 'android:icon=' in manifest:
    import re
    manifest = re.sub(r'android:icon="[^"]+"', 'android:icon="@drawable/insave_logo"', manifest, count=1)
if 'android:roundIcon=' in manifest:
    import re
    manifest = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/insave_logo"', manifest, count=1)

hub_path.write_text(hub)
home_path.write_text(home)
repo_path.write_text(repo)
history_path.write_text(history)
ytdlp_path.write_text(ytdlp)
manifest_path.write_text(manifest)

checks = {
    'states scroll': 'dp(540)' in hub and 'isNestedScrollingEnabled = true' in hub,
    'plain song search': 'putExtra("insave_query", rawInput)' in hub,
    'text query kept': 'filter { it.isNotBlank() }' in home,
    'ytsearch fallback': 'ytsearch10:$inputQuery' in repo,
    'safe back': 'finishAffinity()' not in home and 'onBackPressedDispatcher.addCallback(this)' in hub,
    'playback': 'FileUtil.openFileIntent(requireContext(), playablePath)' in history,
    'loudness': 'loudnorm=I=-9:TP=-1.0:LRA=7' in ytdlp,
    'logo': '@drawable/insave_logo' in manifest,
}
failed = [k for k,v in checks.items() if not v]
if failed: raise SystemExit('v0.17.2 runtime contract failed: ' + ', '.join(failed))
print('InSave v0.17.2 physical-phone runtime contract: PASS')
