package com.deniscerri.ytdl.insave

import android.net.Uri
import android.os.Environment
import java.io.File

/**
 * Local/sideload status discovery used by InSave.
 *
 * This intentionally restores the historical behavior: once Android grants the app's
 * all-files special access, WhatsApp and WhatsApp Business .Statuses are discovered
 * automatically under Android/media without asking the user to pick each folder with SAF.
 * SAF remains a fallback in InSaveHubActivity for devices/ROMs where direct discovery fails.
 */
class AutomaticStatusRepository {

    fun scan(source: InSaveStatusSource): List<InSaveStatus> {
        val seen = linkedSetOf<String>()
        return candidateDirectories(source)
            .asSequence()
            .filter { it.isDirectory && it.canRead() }
            .flatMap { directory -> directory.listFiles()?.asSequence() ?: emptySequence() }
            .filter { it.isFile && it.canRead() }
            .mapNotNull { file ->
                val canonical = runCatching { file.canonicalPath }.getOrElse { file.absolutePath }
                if (!seen.add(canonical)) return@mapNotNull null
                val mime = mimeFromName(file.name) ?: return@mapNotNull null
                InSaveStatus(Uri.fromFile(file), file.name, mime, file.lastModified())
            }
            .sortedByDescending { it.modified }
            .toList()
    }

    fun candidateDirectories(source: InSaveStatusSource): List<File> {
        val root = Environment.getExternalStorageDirectory()
        return when (source) {
            InSaveStatusSource.WHATSAPP -> listOf(
                File(root, "Android/media/com.whatsapp/WhatsApp/Media/.Statuses"),
                File(root, "WhatsApp/Media/.Statuses"),
            )
            InSaveStatusSource.WHATSAPP_BUSINESS -> listOf(
                File(root, "Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses"),
                File(root, "WhatsApp Business/Media/.Statuses"),
            )
        }
    }

    private fun mimeFromName(name: String): String? = when (name.substringAfterLast('.', "").lowercase()) {
        "jpg", "jpeg" -> "image/jpeg"
        "png" -> "image/png"
        "webp" -> "image/webp"
        "heic", "heif" -> "image/heic"
        "mp4" -> "video/mp4"
        "webm" -> "video/webm"
        "mkv" -> "video/x-matroska"
        "mov" -> "video/quicktime"
        "3gp" -> "video/3gpp"
        else -> null
    }
}
