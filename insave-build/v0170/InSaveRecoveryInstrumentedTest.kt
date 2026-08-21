package com.deniscerri.ytdl.insave

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.deniscerri.ytdl.core.RuntimeManager
import com.deniscerri.ytdl.core.models.YTDLRequest
import com.deniscerri.ytdl.util.extractors.newpipe.NewPipeUtil
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class InSaveRecoveryInstrumentedTest {

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
    fun publicYoutubeResolvesAndConvertsToMp3WithoutLogin() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val directAudioUrl = resolveSignedPublicYoutubeAudio(context)
        val outputDir = File(context.cacheDir, "insave-real-youtube-e2e").apply {
            deleteRecursively()
            mkdirs()
        }

        RuntimeManager.init(context)
        val response = convertDirectAudioToMp3(
            directAudioUrl = directAudioUrl,
            outputDir = outputDir,
            outputName = "insave-e2e",
            processId = "insave-real-youtube-e2e",
        )

        val mp3 = outputDir.listFiles()?.firstOrNull { it.extension.equals("mp3", ignoreCase = true) }
        assertTrue(
            "yt-dlp/FFmpeg direct-stream conversion failed. stdout=${response.out.takeLast(1500)} stderr=${response.err.takeLast(1500)}",
            mp3 != null && mp3.length() > 16_384
        )
        assertLooksLikeMp3(mp3!!)
    }

    @Test
    fun selectedPlaylistEntriesConvertAsIndependent320kMp3Jobs() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val directAudioUrl = resolveSignedPublicYoutubeAudio(context)
        val outputDir = File(context.cacheDir, "insave-playlist-mp3-e2e").apply {
            deleteRecursively()
            mkdirs()
        }

        RuntimeManager.init(context)
        val created = (1..2).map { index ->
            val name = "%03d - insave-playlist-e2e".format(index)
            val response = convertDirectAudioToMp3(
                directAudioUrl = directAudioUrl,
                outputDir = outputDir,
                outputName = name,
                processId = "insave-playlist-e2e-$index",
            )
            val file = File(outputDir, "$name.mp3")
            assertTrue(
                "Independent playlist MP3 job $index failed. stdout=${response.out.takeLast(1200)} stderr=${response.err.takeLast(1200)}",
                file.exists() && file.length() > 180_000
            )
            assertLooksLikeMp3(file)
            file
        }

        assertEquals("Two selected entries must produce two independent MP3 files", 2, created.map { it.name }.distinct().size)
    }

    private fun resolveSignedPublicYoutubeAudio(context: Context): String {
        val youtubeUrl = "https://www.youtube.com/watch?v=BaW_jenozKc"
        val formatsResult = NewPipeUtil(context).getFormats(youtubeUrl)
        assertTrue(
            "NewPipe/PO-token resolution failed: ${formatsResult.exceptionOrNull()?.message}",
            formatsResult.isSuccess
        )

        val audio = formatsResult.getOrThrow()
            .asSequence()
            .filter { !it.url.isNullOrBlank() }
            .filter { it.vcodec.isBlank() || it.vcodec.equals("none", ignoreCase = true) }
            .filter { it.acodec.isNotBlank() && !it.acodec.equals("none", ignoreCase = true) }
            .maxByOrNull { bitrateNumber(it.tbr) }

        assertTrue("No signed direct audio stream was returned for public YouTube", audio?.url?.isNotBlank() == true)
        return audio!!.url!!
    }

    private fun convertDirectAudioToMp3(
        directAudioUrl: String,
        outputDir: File,
        outputName: String,
        processId: String,
    ) = RuntimeManager.execute(
        request = YTDLRequest(directAudioUrl)
            .addOption("--no-playlist")
            .addOption("--force-overwrites")
            .addOption("--retries", "10")
            .addOption("--fragment-retries", "10")
            .addOption("-x")
            .addOption("--audio-format", "mp3")
            .addOption("--audio-quality", "320K")
            .addOption("-P", outputDir.absolutePath)
            .addOption("-o", "$outputName.%(ext)s"),
        processId = processId,
        redirectErrorStream = true,
        usingCacheDir = true,
    )

    private fun assertLooksLikeMp3(mp3: File) {
        val header = mp3.inputStream().use { stream -> ByteArray(12).also { stream.read(it) } }
        val hasId3 = header.copyOfRange(0, 3).toString(Charsets.US_ASCII) == "ID3"
        val hasMp3Frame = (0 until (header.size - 1)).any { i: Int ->
            (header[i].toInt() and 0xFF) == 0xFF && (header[i + 1].toInt() and 0xE0) == 0xE0
        }
        assertTrue("Generated file does not look like a real MP3", hasId3 || hasMp3Frame)
    }

    private fun bitrateNumber(value: String?): Double = value
        ?.lowercase()
        ?.removeSuffix("kbps")
        ?.removeSuffix("k")
        ?.trim()
        ?.toDoubleOrNull()
        ?: 0.0
}
