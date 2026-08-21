from pathlib import Path

p = Path('upstream/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt')
s = p.read_text()

# Provider C import.
import_anchor = 'import com.deniscerri.ytdl.util.extractors.newpipe.NewPipeUtil\n'
if 'import com.deniscerri.ytdl.insave.InSaveCobaltResolver\n' not in s:
    if import_anchor not in s:
        raise SystemExit('NewPipe import anchor missing')
    s = s.replace(import_anchor, 'import com.deniscerri.ytdl.insave.InSaveCobaltResolver\n' + import_anchor, 1)

# Provider C lazy client.
property_anchor = '    private val inSaveNewPipe by lazy { NewPipeUtil(context) }\n'
if 'private val inSaveCobalt by lazy' not in s:
    if property_anchor not in s:
        raise SystemExit('NewPipe property anchor missing')
    s = s.replace(
        property_anchor,
        property_anchor + '    private val inSaveCobalt by lazy { InSaveCobaltResolver(context) }\n',
        1,
    )

# Replace only the recovery resolver helper. Provider A returns immediately on success;
# Provider C is attempted only when Provider A cannot resolve and an endpoint is configured.
start_marker = '    private fun resolveInSaveYoutubeAudioDirectUrl(url: String): String? {'
end_marker = '    private fun YTDLRequest.setYoutubeExtractorArgs(url: String?) {'
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('InSave resolver helper boundaries missing')

replacement = '''    private fun resolveInSaveYoutubeAudioDirectUrl(url: String): String? {
        if (sharedPreferences.getBoolean("insave_newpipe_audio_primary", true)) {
            val localNewPipe = kotlin.runCatching {
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
            if (!localNewPipe.isNullOrBlank()) return localNewPipe
        }

        val preferredBitrate = sharedPreferences
            .getString("audio_bitrate", "320k")
            ?.filter(Char::isDigit)
            ?.toIntOrNull()
            ?: 320
        return inSaveCobalt.resolveAudio(url, preferredBitrate)
    }

'''
s = s[:start] + replacement + s[end:]
p.write_text(s)

checks = {
    'cobalt import': 'InSaveCobaltResolver' in s,
    'newpipe primary': 'if (!localNewPipe.isNullOrBlank()) return localNewPipe' in s,
    'cobalt fallback': 'inSaveCobalt.resolveAudio(url, preferredBitrate)' in s,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit('Remote fallback contract failed: ' + ', '.join(failed))
print('InSave Provider C fallback contract: PASS')
