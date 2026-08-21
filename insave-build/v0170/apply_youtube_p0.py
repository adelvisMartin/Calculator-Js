from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
ytdlp_path = root / 'util/extractors/ytdlp/YTDLPUtil.kt'
worker_path = root / 'work/download/DownloadWorker.kt'

ytdlp = ytdlp_path.read_text()

# Provider order is strict:
# A = NewPipe signed direct stream
# B = local yt-dlp + dynamic per-video PO token (normal request)
# C = optional user-configured Cobalt, only after B throws.
helper_start = '    private fun resolveInSaveYoutubeAudioDirectUrl(url: String): String? {'
helper_end = '    private fun YTDLRequest.setYoutubeExtractorArgs(url: String?) {'
start = ytdlp.find(helper_start)
end = ytdlp.find(helper_end, start)
if start < 0 or end < 0:
    raise SystemExit('InSave YouTube resolver boundaries missing')

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

    fun resolveInSaveCobaltFallbackUrl(url: String): String? {
        val preferredBitrate = sharedPreferences
            .getString("audio_bitrate", "320k")
            ?.filter(Char::isDigit)
            ?.toIntOrNull()
            ?: 320
        return inSaveCobalt.resolveAudio(url, preferredBitrate)
    }

'''
ytdlp = ytdlp[:start] + helper + ytdlp[end:]

old_build = '''    fun buildYTDLRequest(downloadItem: DownloadItem) : YTDLRequest {
        val inSaveDirectYoutubeAudioUrl = if (
            downloadItem.type == DownloadType.audio && downloadItem.url.isYoutubeURL()
        ) resolveInSaveYoutubeAudioDirectUrl(downloadItem.url) else null

        var useItemURL = sharedPreferences.getBoolean("use_itemurl_instead_playlisturl", false)
'''
new_build = '''    fun buildYTDLRequest(
        downloadItem: DownloadItem,
        inSaveOverrideDirectUrl: String? = null
    ) : YTDLRequest {
        val inSaveDirectYoutubeAudioUrl = inSaveOverrideDirectUrl ?: if (
            downloadItem.type == DownloadType.audio && downloadItem.url.isYoutubeURL()
        ) resolveInSaveYoutubeAudioDirectUrl(downloadItem.url) else null

        var useItemURL = sharedPreferences.getBoolean("use_itemurl_instead_playlisturl", false)
'''
if old_build not in ytdlp:
    raise SystemExit('InSave buildYTDLRequest signature block missing')
ytdlp = ytdlp.replace(old_build, new_build, 1)

ytdlp_path.write_text(ytdlp)

worker = worker_path.read_text()

# Imports used by the recovery decision in the worker.
if 'import com.deniscerri.ytdl.database.enums.DownloadType\n' not in worker:
    anchor = 'import com.deniscerri.ytdl.database.DBManager\n'
    if anchor not in worker:
        raise SystemExit('DownloadWorker DBManager import anchor missing')
    worker = worker.replace(anchor, anchor + 'import com.deniscerri.ytdl.database.enums.DownloadType\n', 1)
if 'import com.deniscerri.ytdl.util.Extensions.isYoutubeURL\n' not in worker:
    anchor = 'import com.deniscerri.ytdl.util.Extensions.getMediaDuration\n'
    if anchor not in worker:
        raise SystemExit('DownloadWorker Extensions import anchor missing')
    worker = worker.replace(anchor, anchor + 'import com.deniscerri.ytdl.util.Extensions.isYoutubeURL\n', 1)

# The request has to become mutable because Provider C is a real retry request,
# not a URL substituted ahead of Provider B.
worker = worker.replace(
    '                        val request = ytdlpUtil.buildYTDLRequest(downloadItem)\n',
    '                        var request = ytdlpUtil.buildYTDLRequest(downloadItem)\n',
    1,
)
worker = worker.replace(
    '                        val commandString = ytdlpUtil.parseYTDLRequestString(request)\n',
    '                        var commandString = ytdlpUtil.parseYTDLRequestString(request)\n',
    1,
)

run_start = '''                        runCatching {
                            RuntimeManager.getInstance().destroyProcessById(downloadItem.id.toString())
                            RuntimeManager.getInstance().execute(
                                request = request,
                                processId = downloadItem.id.toString(),
                                redirectErrorStream = true,
                                usingCacheDir = true
                            ) { progress, _, line ->
                                WorkerEventBus.post(
                                    WorkerProgress(
                                        progress.toInt(),
                                        line,
                                        downloadItem.id,
                                        downloadItem.logID
                                    )
                                )
                                val title: String = downloadItem.title.ifEmpty { downloadItem.url }
                                notificationUtil.updateDownloadNotification(
                                    downloadItem.id.toInt(),
                                    line, progress.toInt(), 0, title,
                                    NotificationUtil.DOWNLOAD_SERVICE_CHANNEL_ID
                                )
                                CoroutineScope(Dispatchers.IO).launch {
                                    if (logDownloads) {
                                        logRepo.update(line, logItem.id)
                                    }
                                    logString.append("$line\\n")
                                }
                            }
                        }.onSuccess {
'''

replacement = '''                        fun executeInSaveRequest(candidateRequest: com.deniscerri.ytdl.core.models.YTDLRequest) =
                            RuntimeManager.getInstance().execute(
                                request = candidateRequest,
                                processId = downloadItem.id.toString(),
                                redirectErrorStream = true,
                                usingCacheDir = true
                            ) { progress, _, line ->
                                WorkerEventBus.post(
                                    WorkerProgress(
                                        progress.toInt(),
                                        line,
                                        downloadItem.id,
                                        downloadItem.logID
                                    )
                                )
                                val title: String = downloadItem.title.ifEmpty { downloadItem.url }
                                notificationUtil.updateDownloadNotification(
                                    downloadItem.id.toInt(),
                                    line, progress.toInt(), 0, title,
                                    NotificationUtil.DOWNLOAD_SERVICE_CHANNEL_ID
                                )
                                CoroutineScope(Dispatchers.IO).launch {
                                    if (logDownloads) {
                                        logRepo.update(line, logItem.id)
                                    }
                                    logString.append("$line\\n")
                                }
                            }

                        runCatching {
                            RuntimeManager.getInstance().destroyProcessById(downloadItem.id.toString())
                            executeInSaveRequest(request)
                        }.recoverCatching { providerBError ->
                            val isYoutubeAudio =
                                downloadItem.type == DownloadType.audio && downloadItem.url.isYoutubeURL()
                            if (!isYoutubeAudio || providerBError is RuntimeManager.CanceledException) {
                                throw providerBError
                            }

                            // A has already been attempted by buildYTDLRequest(). If the request
                            // reaching RuntimeManager failed, that is Provider B. Only now may C run.
                            val cobaltUrl = ytdlpUtil.resolveInSaveCobaltFallbackUrl(downloadItem.url)
                            if (cobaltUrl.isNullOrBlank()) throw providerBError

                            logString.append("InSave Provider B failed; retrying optional Provider C.\\n")
                            request = ytdlpUtil.buildYTDLRequest(downloadItem, cobaltUrl)
                            commandString = ytdlpUtil.parseYTDLRequestString(request)
                            RuntimeManager.getInstance().destroyProcessById(downloadItem.id.toString())
                            executeInSaveRequest(request)
                        }.onSuccess {
'''

if run_start not in worker:
    raise SystemExit('DownloadWorker RuntimeManager execution block missing')
worker = worker.replace(run_start, replacement, 1)
worker_path.write_text(worker)

# P0 static contract. Provider C must not be called from the direct resolver anymore.
y = ytdlp_path.read_text()
w = worker_path.read_text()
resolver_body = y[y.find(helper_start):y.find(helper_end, y.find(helper_start))]
checks = {
    'provider A newpipe': 'inSaveNewPipe.getFormats(url)' in resolver_body,
    'provider A does not call C': 'inSaveCobalt.resolveAudio' not in resolver_body,
    'provider C explicit resolver': 'fun resolveInSaveCobaltFallbackUrl' in y,
    'override request support': 'inSaveOverrideDirectUrl: String? = null' in y,
    'provider B dynamic player token': 'getWebClientPoToken(videoId)' in y and 'web.player+' in y,
    'provider B dynamic gvs token': 'web.gvs+' in y,
    'provider B anonymous token path': 'poTokens.isNotEmpty() && sharedPreferences.getBoolean("use_cookies"' not in y,
    'provider C only recover': 'recoverCatching { providerBError' in w,
    'provider C retry marker': 'Provider B failed; retrying optional Provider C' in w,
    'youtube audio guard': 'downloadItem.type == DownloadType.audio && downloadItem.url.isYoutubeURL()' in w,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave YouTube P0 provider-chain contract failed: ' + ', '.join(failed))
print('InSave YouTube P0 provider chain A -> B -> C: PASS')
