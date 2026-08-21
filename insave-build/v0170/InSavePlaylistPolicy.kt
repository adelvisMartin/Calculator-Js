package com.deniscerri.ytdl.insave

import com.deniscerri.ytdl.database.enums.DownloadType
import com.deniscerri.ytdl.database.models.DownloadItem

/**
 * InSave recovery policy for playlist / Mix audio jobs.
 *
 * Every selected entry remains an independent DownloadItem.  This is important for
 * YouTube's current per-video PO-token behaviour: one failed entry must not poison
 * the rest of the batch.
 */
object InSavePlaylistPolicy {
    const val MAX_BATCH_ITEMS = 50
    private val allowedBitrates = linkedSetOf("320K", "256K", "192K")

    fun normalizeBitrate(raw: String?): String {
        val digits = raw.orEmpty().filter(Char::isDigit)
        return when (digits) {
            "320" -> "320K"
            "256" -> "256K"
            "192" -> "192K"
            else -> "320K"
        }
    }

    fun limitIds(ids: List<Long>): List<Long> = ids.distinct().take(MAX_BATCH_ITEMS)

    fun applyMp3Preset(item: DownloadItem, requestedBitrate: String?) {
        if (item.type != DownloadType.audio) return

        item.container = "mp3"
        item.audioPreferences.bitrate = normalizeBitrate(requestedBitrate)
        item.audioPreferences.embedThumb = false
        item.audioPreferences.cropThumb = false
        item.audioPreferences.splitByChapters = false

        // Stable ordering and collision resistance for playlist / Mix downloads.
        if (item.playlistIndex != null || item.playlistTitle.isNotBlank()) {
            item.customFileNameTemplate = "%(playlist_index)03d - %(title).170B"
        }
    }

    fun isSupportedBitrate(value: String): Boolean = normalizeBitrate(value) in allowedBitrates
}
