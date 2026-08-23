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
class InSaveV0180InstrumentedTest {
    companion object {
        private const val PUBLIC_1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        private const val PUBLIC_2 = "https://www.youtube.com/watch?v=M7lc1UVf-VE"
        private const val PUBLIC_3 = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
        private const val PUBLIC_4 = "https://www.youtube.com/watch?v=9bZkp7q19f0"
        private val PUBLIC_CANDIDATES = listOf(PUBLIC_1, PUBLIC_2, PUBLIC_3, PUBLIC_4)
    }

    @Test
    fun discoversFourteenWhatsappFixturesAndBusinessWithoutSafPicker() {
        val repository = AutomaticStatusRepository()
        val whatsapp = repository.scan(InSaveStatusSource.WHATSAPP)
        val business = repository.scan(InSaveStatusSource.WHATSAPP_BUSINESS)

        val fixtures = whatsapp.filter { it.name.startsWith("insave-auto-test") && it.name.endsWith(".jpg") }
        assertTrue("Expected at least 14 WhatsApp fixtures, got=${fixtures.map { it.name }}", fixtures.size >= 14)
        assertTrue("Later status fixture was not discovered", fixtures.any { it.name == "insave-auto-test-12.jpg" })
        assertTrue(
            "WhatsApp Business automatic .Statuses discovery failed; found=${business.map { it.name }}",
            business.any { it.name == "insave-auto-business-test.mp4" }
        )
    }

    @Test
    fun providerBPrimaryAndBoundedFallbackStrategiesAreIsolated() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = false)
        RuntimeManager.init(context)
        val util = ytdlp(context)
        val item = audioItem(context, 920001L, "v0180-strategy", PUBLIC_1)

        val primary = util.parseYTDLRequestString(util.buildYTDLRequest(item))
        assertTrue("Primary B must use mweb", primary.contains("player_client=mweb"))
        assertTrue("Primary B must carry player PO token", primary.contains("mweb.player+"))
        assertTrue("Primary B must carry GVS PO token", primary.contains("mweb.gvs+"))

        val embedded = util.parseYTDLRequestString(
            util.buildYTDLRequest(item, inSaveYoutubeClientOverride = "web_embedded")
        )
        assertTrue("B2 must explicitly use web_embedded", embedded.contains("player_client=web_embedded"))
        assertFalse("B2 must not reuse mweb PO material", embedded.contains("mweb.player+") || embedded.contains("mweb.gvs+"))

        val androidVr = util.parseYTDLRequestString(
            util.buildYTDLRequest(item, inSaveYoutubeClientOverride = "android_vr")
        )
        assertTrue("B3 must explicitly use android_vr", androidVr.contains("player_client=android_vr"))
        assertFalse("B3 must not reuse mweb PO material", androidVr.contains("mweb.player+") || androidVr.contains("mweb.gvs+"))
    }

    @Test
    fun providerBDynamicProducesReal320kMp3OnAtLeastOnePublicCandidate() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = false)
        RuntimeManager.init(context)
        val util = ytdlp(context)
        val failures = mutableListOf<String>()

        for ((index, url) in PUBLIC_CANDIDATES.withIndex()) {
            val item = audioItem(context, 920010L + index, "v0180-provider-b-$index", url)
            val request = util.buildYTDLRequest(item)
            val rendered = util.parseYTDLRequestString(request)
            assertTrue("Provider B must receive a dynamic mweb player PO token", rendered.contains("mweb.player+"))
            assertTrue("Provider B must receive a dynamic mweb GVS PO token", rendered.contains("mweb.gvs+"))
            assertFalse("Anonymous Provider B must not require cookies", rendered.contains("--cookies"))
            assertMp3Contract(rendered, "candidate-$index")

            val result = runCatching {
                RuntimeManager.execute(
                    request = request,
                    processId = "v0180-provider-b-$index",
                    redirectErrorStream = false,
                    usingCacheDir = true,
                )
            }
            val mp3 = findGeneratedMp3(context, item.id)
            if (result.isSuccess && mp3 != null && mp3.length() > 16_384) {
                assertLooksLikeMp3(mp3)
                return
            }
            val error = result.exceptionOrNull()
            failures += "${url.substringAfter("v=")}: ${InSaveProviderFailureClassifier.classify(error ?: Exception("no MP3"))}: ${error?.message?.takeLast(350)}"
        }
        throw AssertionError("Provider B did not produce an MP3 from any public candidate: ${failures.joinToString(" | ")}")
    }

    @Test
    fun twoIndependentSelectedJobsProduceTwoDistinctMp3FilesWithoutAllOrNothingBatch() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = false)
        RuntimeManager.init(context)
        val util = ytdlp(context)
        val produced = mutableListOf<File>()
        val failures = mutableListOf<String>()

        for ((candidateIndex, url) in PUBLIC_CANDIDATES.withIndex()) {
            if (produced.size == 2) break
            val id = 920100L + candidateIndex
            val item = audioItem(
                context = context,
                id = id,
                title = "%03d-v0180-playlist".format(candidateIndex + 1),
                url = url,
                playlistTitle = "InSave v0.18 QA Playlist",
                playlistIndex = candidateIndex + 1,
            )
            val request = util.buildYTDLRequest(item)
            val rendered = util.parseYTDLRequestString(request)
            assertMp3Contract(rendered, "playlist-$candidateIndex")
            assertTrue("Independent job lost its own URL", rendered.contains(url))
            assertTrue("Independent job lost per-video Player PO", rendered.contains("mweb.player+"))
            assertTrue("Independent job lost GVS PO", rendered.contains("mweb.gvs+"))

            val result = runCatching {
                RuntimeManager.execute(
                    request = request,
                    processId = "v0180-playlist-$candidateIndex",
                    redirectErrorStream = false,
                    usingCacheDir = true,
                )
            }
            val mp3 = findGeneratedMp3(context, item.id)
            if (result.isSuccess && mp3 != null && mp3.length() > 16_384) {
                assertLooksLikeMp3(mp3)
                produced += mp3
            } else {
                val error = result.exceptionOrNull()
                failures += "${url.substringAfter("v=")}: ${InSaveProviderFailureClassifier.classify(error ?: Exception("no MP3"))}: ${error?.message?.takeLast(350)}"
            }
        }

        assertEquals(
            "Need two successful independent public-video jobs. failures=${failures.joinToString(" | ")}",
            2,
            produced.map { it.absolutePath }.distinct().size
        )
    }

    @Test
    fun providerCRemainsOptionalAndRejectsUnsafeEndpointConfiguration() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        configureP0(context, newPipePrimary = false)
        val prefs = PreferenceManager.getDefaultSharedPreferences(context)
        val util = ytdlp(context)
        assertTrue("Provider C must be off by default", util.resolveInSaveCobaltFallbackUrl(PUBLIC_1).isNullOrBlank())

        prefs.edit().putString(InSaveCobaltResolver.PREF_ENDPOINT, "http://192.168.1.25:9000").apply()
        assertTrue("Private cleartext Provider C endpoint must be rejected", util.resolveInSaveCobaltFallbackUrl(PUBLIC_1).isNullOrBlank())
    }

    private fun assertMp3Contract(rendered: String, label: String) {
        assertTrue("$label lost MP3: $rendered", rendered.contains("--audio-format") && rendered.contains("mp3"))
        assertTrue("$label lost 320K: $rendered", rendered.contains("--audio-quality") && rendered.contains("320K", ignoreCase = true))
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
        url: String,
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
            downloadPath = File(context.cacheDir, "insave-v0180-output").absolutePath,
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
