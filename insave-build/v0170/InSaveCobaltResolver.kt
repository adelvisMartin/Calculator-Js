package com.deniscerri.ytdl.insave

import android.content.Context
import androidx.preference.PreferenceManager
import com.google.gson.Gson
import com.google.gson.JsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import java.util.concurrent.TimeUnit

/**
 * Optional Provider C for InSave.
 *
 * Provider A = local NewPipe + per-video PO token.
 * Provider B = local yt-dlp/youtubedl-android.
 * Provider C = user-owned/self-hosted Cobalt-compatible endpoint.
 *
 * No public Cobalt instance is hard-coded. If no endpoint is configured this provider is a no-op.
 */
class InSaveCobaltResolver(context: Context) {
    private val prefs = PreferenceManager.getDefaultSharedPreferences(context.applicationContext)
    private val gson = Gson()
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .callTimeout(35, TimeUnit.SECONDS)
        .build()

    fun isConfigured(): Boolean = endpoint() != null

    fun health(): Boolean {
        val endpoint = endpoint() ?: return false
        val request = Request.Builder().url(endpoint).get().build()
        return runCatching {
            client.newCall(request).execute().use { response ->
                response.isSuccessful && !response.body.string().isBlank()
            }
        }.getOrDefault(false)
    }

    /**
     * Returns a Cobalt tunnel/direct URL that can be passed to the local FFmpeg/yt-dlp runtime.
     * For local-processing audio responses we use the first tunnel as the media source and keep
     * the final MP3 conversion local. Returns null on disabled/unhealthy/error/picker responses.
     */
    fun resolveAudio(sourceUrl: String, bitrateKbps: Int = 320): String? {
        val endpoint = endpoint() ?: return null
        val payload = linkedMapOf<String, Any>(
            "url" to sourceUrl,
            "downloadMode" to "audio",
            "audioFormat" to "mp3",
            "audioBitrate" to bitrateKbps.coerceIn(64, 320).toString(),
            "filenameStyle" to "pretty",
            "localProcessing" to "preferred",
            "youtubeBetterAudio" to true,
        )
        val body = gson.toJson(payload).toRequestBody(JSON)
        val builder = Request.Builder()
            .url(endpoint)
            .post(body)
            .header("Accept", "application/json")
            .header("Content-Type", "application/json")

        prefs.getString(PREF_API_KEY, null)
            ?.trim()
            ?.takeIf { it.isNotBlank() }
            ?.let { builder.header("Authorization", "Api-Key $it") }

        return runCatching {
            client.newCall(builder.build()).execute().use { response ->
                if (!response.isSuccessful) return@use null
                val json = gson.fromJson(response.body.string(), JsonObject::class.java) ?: return@use null
                when (json.get("status")?.asString) {
                    "redirect", "tunnel" -> json.get("url")?.asString?.takeIf(::isPublicOrSelfHostedHttpUrl)
                    "local-processing" -> json.getAsJsonArray("tunnel")
                        ?.firstOrNull()
                        ?.asString
                        ?.takeIf(::isPublicOrSelfHostedHttpUrl)
                    else -> null
                }
            }
        }.getOrNull()
    }

    private fun endpoint(): String? {
        val raw = prefs.getString(PREF_ENDPOINT, null)?.trim()?.trimEnd('/') ?: return null
        val parsed = raw.toHttpUrlOrNull() ?: return null
        if (parsed.scheme != "https" && parsed.host !in LOCAL_HOSTS) return null
        return parsed.toString()
    }

    private fun isPublicOrSelfHostedHttpUrl(value: String): Boolean {
        val parsed = value.toHttpUrlOrNull() ?: return false
        return parsed.scheme == "https" || parsed.host in LOCAL_HOSTS
    }

    companion object {
        const val PREF_ENDPOINT = "insave_cobalt_endpoint"
        const val PREF_API_KEY = "insave_cobalt_api_key"
        private val JSON = "application/json; charset=utf-8".toMediaType()
        private val LOCAL_HOSTS = setOf("127.0.0.1", "localhost", "10.0.2.2")
    }
}
