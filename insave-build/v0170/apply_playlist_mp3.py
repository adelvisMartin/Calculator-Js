from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
main_path = root / 'MainActivity.kt'
home_path = root / 'ui/HomeFragment.kt'
vm_path = root / 'database/viewmodel/DownloadViewModel.kt'
ytdlp_path = root / 'util/extractors/ytdlp/YTDLPUtil.kt'

hub = hub_path.read_text()
main = main_path.read_text()
home = home_path.read_text()
vm = vm_path.read_text()
ytdlp = ytdlp_path.read_text()

# ---------------------------------------------------------------------------
# InSave defaults: playlist/audio is a first-class recovery path.
# ---------------------------------------------------------------------------
default_anchor = '''            .putBoolean("auto_update_ytdlp", true)\n'''
default_block = '''            .putBoolean("auto_update_ytdlp", true)\n            .putBoolean("insave_playlist_mp3_enabled", true)\n            .putBoolean("insave_resilient_retries", true)\n            .putInt("concurrent_fragments", 4)\n'''
if '.putBoolean("insave_playlist_mp3_enabled", true)' not in hub:
    if default_anchor not in hub:
        raise SystemExit('Hub defaults anchor missing')
    hub = hub.replace(default_anchor, default_block, 1)

# Existing recovery patch already added these keys with conservative values.
hub = hub.replace('.putString("retries", "5")', '.putString("retries", "10")')
hub = hub.replace('.putString("fragment_retries", "5")', '.putString("fragment_retries", "10")')
hub = hub.replace('.putString("socket_timeout", "15")', '.putString("socket_timeout", "30")')

# ---------------------------------------------------------------------------
# Direct playlist/Mix hand-off: if a URL is pasted in InSave, open it directly
# in HomeFragment so the user sees the individual entries + checkboxes.
# ---------------------------------------------------------------------------
start = hub.find('    private fun openAudioSearch() {')
end = hub.find('    private fun openDownloader(type: DownloadType) {', start)
if start < 0 or end < 0:
    raise SystemExit('openAudioSearch boundaries missing')
new_audio_search = '''    private fun openAudioSearch() {
        val bitrate = prefs.getString("audio_bitrate", "320K").orEmpty().ifBlank { "320K" }
        prefs.edit()
            .putString("preferred_download_type", DownloadType.audio.toString())
            .putString("audio_format", "mp3")
            .putString("audio_bitrate", bitrate)
            .putBoolean("remember_download_type", false)
            .putBoolean("insave_playlist_mp3_enabled", true)
            .apply()

        val query = if (::urlInput.isInitialized) normalizeUrl(urlInput.text.toString()) else null
        startActivity(Intent(this, MainActivity::class.java).apply {
            if (!query.isNullOrBlank()) {
                action = Intent.ACTION_VIEW
                putExtra("insave_query", query)
            }
        })
        toast("Lista MP3 activa · selección individual · máximo 50 · ${bitrate.filter(Char::isDigit)} kbps")
    }

'''
hub = hub[:start] + new_audio_search + hub[end:]

# ---------------------------------------------------------------------------
# MainActivity bridge for the direct playlist URL.
# ---------------------------------------------------------------------------
handle_anchor = '''    private fun handleIntents(intent: Intent) {
        val action = intent.action
'''
handle_insert = '''    private fun handleIntents(intent: Intent) {
        val inSaveQuery = intent.getStringExtra("insave_query")
        if (!inSaveQuery.isNullOrBlank()) {
            intent.removeExtra("insave_query")
            val bundle = Bundle().apply { putString("url", inSaveQuery) }
            navController.popBackStack(R.id.homeFragment, true)
            navController.navigate(R.id.homeFragment, bundle)
            return
        }

        val action = intent.action
'''
if 'val inSaveQuery = intent.getStringExtra("insave_query")' not in main:
    if handle_anchor not in main:
        raise SystemExit('MainActivity handleIntents anchor missing')
    main = main.replace(handle_anchor, handle_insert, 1)

# ---------------------------------------------------------------------------
# Make the maintained upstream multi-select controls explicit in audio mode.
# ---------------------------------------------------------------------------
fab_anchor = '''        downloadSelectedFab?.setOnClickListener(this)
        downloadAllFab?.tag = "downloadAll"
        downloadAllFab?.setOnClickListener(this)
'''
fab_insert = fab_anchor + '''        if (sharedPreferences?.getString("preferred_download_type", "video") == DownloadType.audio.toString()) {
            downloadSelectedFab?.text = "MP3 seleccionados"
            downloadAllFab?.text = "Lista MP3"
        }
'''
if 'downloadSelectedFab?.text = "MP3 seleccionados"' not in home:
    if fab_anchor not in home:
        raise SystemExit('HomeFragment FAB anchor missing')
    home = home.replace(fab_anchor, fab_insert, 1)

# ---------------------------------------------------------------------------
# Every selected playlist entry becomes an independent DownloadItem and receives
# the exact same MP3 preset. Limit a single audio batch to 50 jobs.
# ---------------------------------------------------------------------------
if 'import com.deniscerri.ytdl.insave.InSavePlaylistPolicy\n' not in vm:
    import_anchor = 'import com.deniscerri.ytdl.database.enums.DownloadType\n'
    if import_anchor not in vm:
        raise SystemExit('DownloadViewModel import anchor missing')
    vm = vm.replace(import_anchor, import_anchor + 'import com.deniscerri.ytdl.insave.InSavePlaylistPolicy\n', 1)

method_start = vm.find('    fun turnResultItemsToProcessingDownloads(itemIDs: List<Long>, downloadNow: Boolean = false)')
method_end = vm.find('    fun insert(item: DownloadItem)', method_start)
if method_start < 0 or method_end < 0:
    raise SystemExit('turnResultItemsToProcessingDownloads boundaries missing')
method = vm[method_start:method_end]

if 'val effectiveItemIDs = if (' not in method:
    job_anchor = '''        val job = viewModelScope.launch(Dispatchers.IO) {
            repository.deleteProcessing()
'''
    job_insert = '''        val effectiveItemIDs = if (
            sharedPreferences.getString("preferred_download_type", "video") == DownloadType.audio.toString() &&
            sharedPreferences.getBoolean("insave_playlist_mp3_enabled", true)
        ) InSavePlaylistPolicy.limitIds(itemIDs) else itemIDs

        val job = viewModelScope.launch(Dispatchers.IO) {
            repository.deleteProcessing()
'''
    if job_anchor not in method:
        raise SystemExit('turnResult job anchor missing')
    method = method.replace(job_anchor, job_insert, 1)
    method = method.replace('                itemIDs.forEachIndexed { index, id ->', '                effectiveItemIDs.forEachIndexed { index, id ->', 1)

preset_anchor = '''                    downloadItem.status = DownloadRepository.Status.Processing.toString()
                    downloadItem.rowNumber = index + 1
'''
preset_insert = preset_anchor + '''                    if (downloadItem.type == DownloadType.audio && sharedPreferences.getBoolean("insave_playlist_mp3_enabled", true)) {
                        InSavePlaylistPolicy.applyMp3Preset(
                            downloadItem,
                            sharedPreferences.getString("audio_bitrate", "320K")
                        )
                    }
'''
if 'InSavePlaylistPolicy.applyMp3Preset(' not in method:
    if preset_anchor not in method:
        raise SystemExit('DownloadItem playlist preset anchor missing')
    method = method.replace(preset_anchor, preset_insert, 1)

vm = vm[:method_start] + method + vm[method_end:]

# ---------------------------------------------------------------------------
# yt-dlp/FFmpeg contract: MP3 must be explicit for InSave even when upstream
# format-order settings omit the `container` rule. Normalize CBR bitrate for
# yt-dlp and add bounded retry backoff.
# ---------------------------------------------------------------------------
ext_anchor = '''                request.addOption("-x")
                val ext = downloadItem.container
'''
ext_insert = '''                request.addOption("-x")
                val ext = downloadItem.container
                if (ext.equals("mp3", ignoreCase = true)) {
                    request.addOption("--audio-format", "mp3")
                }
'''
if 'if (ext.equals("mp3", ignoreCase = true))' not in ytdlp:
    if ext_anchor not in ytdlp:
        raise SystemExit('YTDLP audio ext anchor missing')
    ytdlp = ytdlp.replace(ext_anchor, ext_insert, 1)

quality_old = '''                if (downloadItem.audioPreferences.bitrate.isNotBlank()) {
                    request.addOption("--audio-quality", downloadItem.audioPreferences.bitrate)
                }
'''
quality_new = '''                if (downloadItem.audioPreferences.bitrate.isNotBlank()) {
                    val normalizedAudioBitrate = downloadItem.audioPreferences.bitrate
                        .filter(Char::isDigit)
                        .let { if (it in setOf("320", "256", "192")) "${it}K" else "320K" }
                    request.addOption("--audio-quality", normalizedAudioBitrate)
                }
'''
if 'val normalizedAudioBitrate = downloadItem.audioPreferences.bitrate' not in ytdlp:
    if quality_old not in ytdlp:
        raise SystemExit('YTDLP audio quality anchor missing')
    ytdlp = ytdlp.replace(quality_old, quality_new, 1)

retry_anchor = '''        if(retries.isNotEmpty()) request.addOption("--retries", retries)
        if(fragmentRetries.isNotEmpty()) request.addOption("--fragment-retries", fragmentRetries)
'''
retry_insert = retry_anchor + '''        if (sharedPreferences.getBoolean("insave_resilient_retries", true)) {
            request.addOption("--retry-sleep", "http:linear=1:5:1")
            request.addOption("--retry-sleep", "fragment:exp=1:8")
            request.addOption("--retry-sleep", "extractor:linear=1:3:1")
        }
'''
if 'fragment:exp=1:8' not in ytdlp:
    if retry_anchor not in ytdlp:
        raise SystemExit('YTDLP retry anchor missing')
    ytdlp = ytdlp.replace(retry_anchor, retry_insert, 1)

hub_path.write_text(hub)
main_path.write_text(main)
home_path.write_text(home)
vm_path.write_text(vm)
ytdlp_path.write_text(ytdlp)

checks = {
    'playlist direct handoff': 'putExtra("insave_query", query)' in hub and 'val inSaveQuery = intent.getStringExtra("insave_query")' in main,
    'multi select labels': 'MP3 seleccionados' in home and 'Lista MP3' in home,
    'batch cap': 'InSavePlaylistPolicy.limitIds(itemIDs)' in vm,
    'per-item preset': 'InSavePlaylistPolicy.applyMp3Preset(' in vm,
    'explicit mp3': 'request.addOption("--audio-format", "mp3")' in ytdlp,
    'explicit bitrate': 'normalizedAudioBitrate' in ytdlp,
    'retry backoff': 'fragment:exp=1:8' in ytdlp,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave playlist MP3 contract failed: ' + ', '.join(failed))

print('InSave playlist MP3 contract: PASS')
