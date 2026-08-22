package com.deniscerri.ytdl.insave

import android.content.Context
import androidx.preference.PreferenceManager
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.deniscerri.ytdl.core.RuntimeManager
import com.deniscerri.ytdl.database.DBManager
import com.deniscerri.ytdl.database.enums.DownloadType
import com.deniscerri.ytdl.database.models.AudioPreferences
import com.deniscerri.ytdl.database.models.DownloadItem
import com.deniscerri.ytdl.database.models.Format
import com.deniscerri.ytdl.database.models.VideoPreferences
import com.deniscerri.ytdl.util.FileUtil
import com.deniscerri.ytdl.util.extractors.ytdlp.YTDLPUtil
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class InSaveRecoveryInstrumentedTest {

    companion object {
        // Public, long-lived videos selected for P0 instead of the historical
        // BaW_jenozKc test asset, which currently returns unavailable.
        private const val PUBLIC_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        private const val SECOND_PUBLIC_YOUTUBE_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    }

    @Test
    fun discoversWhatsappAndBusinessStatusesWithoutSafPicker() {
        val repository = AutomaticStatusRepository()
        val whatsapp = repository.scan(InSaveStatusSource.WHATSAPP)
        val business = repository.scan(InSaveStatusSource.WHATSAPP_BUSINESS)

        assertTrue(
            "WhatsApp automatic .Statuses discovery failed; found=${whatsapp.map { it.name }}",
            whatsapp.any { it.name == "insave-auto-test.jpg" }
        )
        assertTrue(
            "WhatsApp Business automatic .Statuses discovery failed; found=${business.map { it.name }}",
            business.any { it.name == "insave-auto-business-test.mp4" }
        )
    }

    @Test
    fun providerChainAThenBDynamicProducesMp3WithoutLogin() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = true)
        val util = ytdlp(context)
        val item = audioItem(context, id = 910001L, title = "p0-chain-a-b")

        RuntimeManager.init(context)
        val request = util.buildYTDLRequest(item)
        val rendered = util.parseYTDLRequestString(request)
        assertTrue("P0 request must stay MP3", rendered.contains("--audio-format") && rendered.contains("mp3"))
        assertTrue(
            "P0 request must keep 320 kbps. request=$rendered",
            rendered.contains("--audio-quality") && rendered.contains("320K", ignoreCase = true)
        )

        val response = RuntimeManager.execute(
            request = request,
            processId = "p0-chain-a-b",
            redirectErrorStream = true,
            usingCacheDir = true,
        )

        val mp3 = findGeneratedMp3(context, item.id)
        assertTrue(
            "A->B chain failed to produce MP3. stdout=${response.out.takeLast(1800)} stderr=${response.err.takeLast(1800)}",
            mp3 != null && mp3.length() > 16_384
        )
        assertLooksLikeMp3(mp3!!)
    }

    @Test
    fun providerBDynamicPerVideoPoTokenProduces320kMp3() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        // Force A off and keep C unconfigured. A successful result therefore proves
        // Provider B (local yt-dlp + per-video dynamic PO token) can complete MP3.
        configureP0(context, newPipePrimary = false)
        val util = ytdlp(context)
        val item = audioItem(context, id = 910002L, title = "p0-provider-b")

        RuntimeManager.init(context)
        val request = util.buildYTDLRequest(item)
        val rendered = util.parseYTDLRequestString(request)

        assertTrue("Provider B must receive YouTube extractor args", rendered.contains("--extractor-args"))
        assertTrue("Provider B must receive a dynamic web player PO token", rendered.contains("web.player+"))
        assertTrue("Provider B must receive a dynamic web GVS PO token", rendered.contains("web.gvs+"))
        assertFalse("Provider B P0 must not require cookies", rendered.contains("--cookies"))
        assertTrue("Provider B must request MP3", rendered.contains("--audio-format") && rendered.contains("mp3"))
        assertTrue(
            "Provider B must request 320 kbps. request=$rendered",
            rendered.contains("--audio-quality") && rendered.contains("320K", ignoreCase = true)
        )

        val response = RuntimeManager.execute(
            request = request,
            processId = "p0-provider-b",
            redirectErrorStream = true,
            usingCacheDir = true,
        )

        val mp3 = findGeneratedMp3(context, item.id)
        assertTrue(
            "Provider B dynamic PO -> MP3 failed. stdout=${response.out.takeLast(2200)} stderr=${response.err.takeLast(2200)}",
            mp3 != null && mp3.length() > 16_384
        )
        assertLooksLikeMp3(mp3!!)
    }

    @Test
    fun selectedPlaylistEntriesUseProviderBAsIndependent320kMp3Jobs() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = false)
        val util = ytdlp(context)
        RuntimeManager.init(context)

        val urls = listOf(PUBLIC_YOUTUBE_URL, SECOND_PUBLIC_YOUTUBE_URL)
        val created = urls.mapIndexed { zeroBasedIndex, url ->
            val index = zeroBasedIndex + 1
            val id = 910010L + index
            val item = audioItem(
                context = context,
                id = id,
                title = "%03d-p0-playlist".format(index),
                url = url,
                playlistTitle = "InSave P0 Playlist",
                playlistIndex = index,
            )
            val request = util.buildYTDLRequest(item)
            val rendered = util.parseYTDLRequestString(request)
            assertTrue("Batch job $index lost MP3", rendered.contains("--audio-format") && rendered.contains("mp3"))
            assertTrue(
                "Batch job $index lost 320 kbps. request=$rendered",
                rendered.contains("--audio-quality") && rendered.contains("320K", ignoreCase = true)
            )
            assertTrue("Batch job $index lost dynamic Player PO", rendered.contains("web.player+"))
            assertTrue("Batch job $index lost dynamic GVS PO", rendered.contains("web.gvs+"))
            assertTrue("Batch job $index must keep its own video URL", rendered.contains(url))

            val response = RuntimeManager.execute(
                request = request,
                processId = "p0-playlist-$index",
                redirectErrorStream = true,
                usingCacheDir = true,
            )
            val file = findGeneratedMp3(context, item.id)
            assertTrue(
                "Independent playlist MP3 job $index failed. stdout=${response.out.takeLast(1600)} stderr=${response.err.takeLast(1600)}",
                file != null && file.length() > 16_384
            )
            assertLooksLikeMp3(file!!)
            file
        }

        assertEquals(
            "Two selected entries must produce two independent MP3 files",
            2,
            created.map { it.absolutePath }.distinct().size
        )
    }

    @Test
    fun providerCRemainsOptionalAndDisabledByDefault() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = false)
        val util = ytdlp(context)
        assertTrue(
            "Provider C must remain optional when no private endpoint is configured",
            util.resolveInSaveCobaltFallbackUrl(PUBLIC_YOUTUBE_URL).isNullOrBlank()
        )
    }

    private fun configureP0(context: Context, newPipePrimary: Boolean) {
        PreferenceManager.getDefaultSharedPreferences(context).edit()
            .putBoolean("insave_newpipe_audio_primary", newPipePrimary)
            .putBoolean("use_cookies", false)
            .putBoolean("use_sponsorblock", false)
            .putBoolean("embed_thumbnail", false)
            .putBoolean("crop_thumbnail", false)
            .putBoolean("cache_downloads", true)
            .putBoolean("disable_write_info_json", true)
            .putBoolean("embed_metadata", false)
            .putBoolean("use_format_sorting", false)
            .putBoolean("aria2", false)
            .putBoolean("force_ipv4", false)
            .putString("audio_format", "mp3")
            .putString("audio_bitrate", "320k")
            .putString("retries", "5")
            .putString("fragment_retries", "5")
            .putString("socket_timeout", "20")
            .remove(InSaveCobaltResolver.PREF_ENDPOINT)
            .remove(InSaveCobaltResolver.PREF_API_KEY)
            .apply()
    }

    private fun ytdlp(context: Context): YTDLPUtil = YTDLPUtil(
        context,
        DBManager.getInstance(context).commandTemplateDao,
    )

    private fun audioItem(
        context: Context,
        id: Long,
        title: String,
        url: String = PUBLIC_YOUTUBE_URL,
        playlistTitle: String = "",
        playlistIndex: Int? = null,
    ): DownloadItem {
        File(FileUtil.getCacheDownloadsPath(context), id.toString()).deleteRecursively()
        return DownloadItem(
            id = id,
            url = url,
            title = title,
            author = "",
            thumb = "",
            duration = "",
            type = DownloadType.audio,
            format = Format(),
            container = "mp3",
            downloadSections = "",
            allFormats = mutableListOf(),
            downloadPath = File(context.cacheDir, "insave-p0-output").absolutePath,
            website = "YouTube",
            downloadSize = "",
            playlistTitle = playlistTitle,
            audioPreferences = AudioPreferences(
                embedThumb = false,
                cropThumb = false,
                splitByChapters = false,
                sponsorBlockFilters = arrayListOf(),
                bitrate = "320k",
            ),
            videoPreferences = VideoPreferences(),
            extraCommands = "",
            customFileNameTemplate = "$title.%(ext)s",
            SaveThumb = false,
            status = "Queued",
            downloadStartTime = 0L,
            logID = null,
            playlistURL = "",
            playlistIndex = playlistIndex,
            incognito = true,
        )
    }

    private fun findGeneratedMp3(context: Context, id: Long): File? =
        File(FileUtil.getCacheDownloadsPath(context), id.toString())
            .walkTopDown()
            .firstOrNull { it.isFile && it.extension.equals("mp3", ignoreCase = true) }

    private fun assertLooksLikeMp3(mp3: File) {
        val header = mp3.inputStream().use { stream -> ByteArray(16).also { stream.read(it) } }
        val hasId3 = header.copyOfRange(0, 3).toString(Charsets.US_ASCII) == "ID3"
        val hasMp3Frame = (0 until (header.size - 1)).any { i ->
            (header[i].toInt() and 0xFF) == 0xFF && (header[i + 1].toInt() and 0xE0) == 0xE0
        }
        assertTrue("Generated file does not look like a real MP3", hasId3 || hasMp3Frame)
    }
}
