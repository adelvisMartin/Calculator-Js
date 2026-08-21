from pathlib import Path

# InSave v0.16.3-RC runtime repair:
# - dynamically obtain per-video Web PO tokens from the maintained NewPipe provider
# - apply PO tokens even when cookies are disabled (anonymous-first InSave flow)
# - prefer fresh dynamic Web tokens over stale stored Web tokens
# - preserve full yt-dlp logs and surface a useful last error in notifications
# - keep the manual PO-token button as fallback, but target the current YouTube URL

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
ytdlp = root / 'util/extractors/ytdlp/YTDLPUtil.kt'
hub = root / 'insave/InSaveHubActivity.kt'
worker = root / 'work/download/DownloadWorker.kt'

s = ytdlp.read_text()

import_anchor = 'import com.deniscerri.ytdl.util.FormatUtil\n'
imports = (
    'import com.deniscerri.ytdl.util.FormatUtil\n'
    'import com.deniscerri.ytdl.util.extractors.newpipe.NewPipeUtil\n'
    'import com.deniscerri.ytdl.util.extractors.newpipe.potoken.NewPipePoTokenGenerator\n'
)
if 'NewPipePoTokenGenerator' not in s:
    if import_anchor not in s:
        raise SystemExit('YTDLPUtil import anchor missing')
    s = s.replace(import_anchor, imports, 1)

property_anchor = '    private val handler = Handler(Looper.getMainLooper())\n'
property_insert = '''    private val handler = Handler(Looper.getMainLooper())
    // One provider per YTDLPUtil instance. NewPipePoTokenGenerator caches the Web/BotGuard
    // generator and creates a player token for the concrete video ID on each request.
    private val dynamicPoTokenProvider by lazy {
        NewPipeUtil(context) // guarantees NewPipe + its downloader are initialized
        NewPipePoTokenGenerator()
    }
'''
if 'private val dynamicPoTokenProvider by lazy' not in s:
    if property_anchor not in s:
        raise SystemExit('YTDLPUtil property anchor missing')
    s = s.replace(property_anchor, property_insert, 1)

po_anchor = '''        val poTokens = mutableListOf<String>()

        val configuredPlayerClientsRaw'''
po_insert = '''        val poTokens = mutableListOf<String>()
        var dynamicPoTokenApplied = false

        // YouTube increasingly binds player PO tokens to a concrete video. Generate a fresh
        // Web-client player token for this video and reuse the provider's streaming token.
        // This path is anonymous and MUST NOT depend on cookies/login.
        if (url?.isYoutubeURL() == true) {
            val videoId = url.getIDFromYoutubeURL()
            if (!videoId.isNullOrBlank()) {
                kotlin.runCatching {
                    dynamicPoTokenProvider.getWebClientPoToken(videoId)
                }.getOrNull()?.let { tokenResult ->
                    if (tokenResult.visitorData.isNotBlank() && tokenResult.playerRequestPoToken.isNotBlank()) {
                        dynamicPoTokenApplied = true
                        // Remove any stale/manual Web tokens before installing the fresh set.
                        poTokens.removeAll { it.startsWith("web.") }
                        playerClients.add("web")
                        extractorArgs.add("visitor_data=${tokenResult.visitorData}")
                        poTokens.add("web.player+${tokenResult.playerRequestPoToken}")
                        tokenResult.streamingDataPoToken
                            ?.takeIf { it.isNotBlank() }
                            ?.let { poTokens.add("web.gvs+$it") }
                    }
                }
            }
        }

        val configuredPlayerClientsRaw'''
if 'var dynamicPoTokenApplied = false' not in s:
    if po_anchor not in s:
        raise SystemExit('PO-token insertion anchor missing')
    s = s.replace(po_anchor, po_insert, 1)

# If configured/static Web tokens were loaded before/after the dynamic set, prefer dynamic ones.
static_add = '                            poTokens.add("${value.playerClient}.${pt.context}+${pt.token}")\n'
static_repl = '''                            if (!(dynamicPoTokenApplied && value.playerClient == "web")) {
                                poTokens.add("${value.playerClient}.${pt.context}+${pt.token}")
                            }
'''
if static_add in s:
    s = s.replace(static_add, static_repl, 1)

generated_loop = '''                        for (cl in value.clients) {
                            playerClients.add(cl)
                            for (pt in value.poTokens) {
                                if (pt.token.isNotBlank()) {
                                    poTokens.add("${cl}.${pt.context}+${pt.token}")
                                }
                            }
                        }

                        if (dataSyncID.isBlank() && value.useVisitorData) {'''
generated_repl = '''                        for (cl in value.clients) {
                            if (dynamicPoTokenApplied && cl == "web") continue
                            playerClients.add(cl)
                            for (pt in value.poTokens) {
                                if (pt.token.isNotBlank()) {
                                    poTokens.add("${cl}.${pt.context}+${pt.token}")
                                }
                            }
                        }

                        if (!dynamicPoTokenApplied && dataSyncID.isBlank() && value.useVisitorData) {'''
if generated_loop in s:
    s = s.replace(generated_loop, generated_repl, 1)

cookie_gate = '        if (poTokens.isNotEmpty() && sharedPreferences.getBoolean("use_cookies", false)) {\n'
if cookie_gate not in s:
    raise SystemExit('Expected cookie-gated PO-token block missing')
s = s.replace(cookie_gate, '        if (poTokens.isNotEmpty()) {\n', 1)

ytdlp.write_text(s)

h = hub.read_text()
# Keep downloader logs on for the RC so the actual yt-dlp/FFmpeg error is retained.
brand_anchor = '.putBoolean("auto_update_ytdlp", true)\n'
if '.putBoolean("log_downloads", true)' not in h:
    if brand_anchor not in h:
        raise SystemExit('Hub defaults anchor missing')
    h = h.replace(brand_anchor, brand_anchor + '            .putBoolean("log_downloads", true)\n', 1)

fixed_redirect = '            putExtra("redirect_url", "https://www.youtube.com/watch?v=aqz-KE-bpKQ")\n'
current_redirect = '''            val currentYoutubeUrl = if (::urlInput.isInitialized) {
                normalizeUrl(urlInput.text.toString())?.takeIf {
                    runCatching { Uri.parse(it).host.orEmpty().contains("youtu", ignoreCase = true) }.getOrDefault(false)
                }
            } else null
            putExtra("redirect_url", currentYoutubeUrl ?: "https://www.youtube.com/watch?v=aqz-KE-bpKQ")
'''
if fixed_redirect in h:
    h = h.replace(fixed_redirect, current_redirect, 1)
hub.write_text(h)

w = worker.read_text()
# The upstream notification receives Throwable.message, which is often null. Fall back to the
# last useful yt-dlp/FFmpeg line already captured in logString.
old_error_arg = '''                                it.message,
                                downloadItem.logID,'''
new_error_arg = '''                                it.message?.takeIf { message -> message.isNotBlank() }
                                    ?: logString.toString().lineSequence()
                                        .filter { line -> line.isNotBlank() }
                                        .lastOrNull { line ->
                                            line.contains("ERROR", ignoreCase = true) ||
                                            line.contains("403") ||
                                            line.contains("PO Token", ignoreCase = true) ||
                                            line.contains("Sign in", ignoreCase = true) ||
                                            line.contains("ffmpeg", ignoreCase = true)
                                        }
                                        ?.takeLast(500),
                                downloadItem.logID,'''
if old_error_arg not in w:
    raise SystemExit('DownloadWorker error notification anchor missing')
w = w.replace(old_error_arg, new_error_arg, 1)
worker.write_text(w)

# Static source contract.
checks = {
    'dynamic provider import': 'NewPipePoTokenGenerator' in ytdlp.read_text(),
    'per video id': 'getWebClientPoToken(videoId)' in ytdlp.read_text(),
    'web player token': 'web.player+' in ytdlp.read_text(),
    'web gvs token': 'web.gvs+' in ytdlp.read_text(),
    'anonymous PO token': 'poTokens.isNotEmpty() && sharedPreferences.getBoolean("use_cookies"' not in ytdlp.read_text(),
    'logs enabled': '.putBoolean("log_downloads", true)' in hub.read_text(),
    'current-url manual fallback': 'currentYoutubeUrl' in hub.read_text(),
    'diagnostic notification': 'PO Token' in worker.read_text() and 'takeLast(500)' in worker.read_text(),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('v0.16.3 source contract failed: ' + ', '.join(failed))
print('InSave v0.16.3 dynamic PO-token contract: PASS')
