package com.deniscerri.ytdl.insave

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.deniscerri.ytdl.core.RuntimeManager
import com.deniscerri.ytdl.core.models.YTDLRequest
import com.deniscerri.ytdl.util.extractors.newpipe.NewPipeUtil
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

        val outputDir = File(context.cacheDir, "insave-real-youtube-e2e").apply {
            deleteRecursively()
            mkdirs()
        }

        RuntimeManager.init(context)
        val request = YTDLRequest(audio!!.url!!)
            .addOption("--no-playlist")
            .addOption("--force-overwrites")
            .addOption("-x")
            .addOption("--audio-format", "mp3")
            .addOption("--audio-quality", "320k")
            .addOption("-P", outputDir.absolutePath)
            .addOption("-o", "insave-e2e.%(ext)s")

        val response = RuntimeManager.execute(
            request = request,
            processId = "insave-real-youtube-e2e",
            redirectErrorStream = true,
            usingCacheDir = true,
        )

        val mp3 = outputDir.listFiles()?.firstOrNull { it.extension.equals("mp3", ignoreCase = true) }
        assertTrue(
            "yt-dlp/FFmpeg direct-stream conversion failed. stdout=${response.out.takeLast(1500)} stderr=${response.err.takeLast(1500)}",
            mp3 != null && mp3.length() > 16_384
        )

        val header = mp3!!.inputStream().use { stream -> ByteArray(12).also { stream.read(it) } }
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
