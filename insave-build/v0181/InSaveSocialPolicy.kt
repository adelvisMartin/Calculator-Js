package com.deniscerri.ytdl.insave

import java.net.URI
import java.util.Locale

/**
 * Small deterministic policy used by InSave's dedicated Instagram/Facebook UX.
 * It intentionally validates only the platform for the shortcut; the maintained
 * yt-dlp engine remains responsible for resolving the concrete public media URL.
 */
object InSaveSocialPolicy {
    enum class Platform(val displayName: String) {
        INSTAGRAM("Instagram"),
        FACEBOOK("Facebook"),
    }

    data class Target(val platform: Platform, val normalizedUrl: String)

    private val instagramHosts = setOf("instagram.com", "www.instagram.com", "m.instagram.com")
    private val facebookHosts = setOf(
        "facebook.com",
        "www.facebook.com",
        "m.facebook.com",
        "mobile.facebook.com",
        "fb.watch",
        "www.fb.watch",
    )

    fun classify(raw: String?): Target? {
        val normalized = InSaveInputPolicy.normalizeHttpUrl(raw) ?: return null
        val host = runCatching { URI(normalized).host }
            .getOrNull()
            ?.trimEnd('.')
            ?.lowercase(Locale.ROOT)
            ?: return null

        val platform = when {
            host in instagramHosts || host.endsWith(".instagram.com") -> Platform.INSTAGRAM
            host in facebookHosts || host.endsWith(".facebook.com") -> Platform.FACEBOOK
            else -> return null
        }
        return Target(platform, normalized)
    }

    fun matches(raw: String?, platform: Platform): Boolean = classify(raw)?.platform == platform

    fun supportedHint(platform: Platform): String = when (platform) {
        Platform.INSTAGRAM -> "Pega un enlace de publicación, Reel o video público de Instagram."
        Platform.FACEBOOK -> "Pega un enlace de video, Reel o publicación pública de Facebook."
    }
}
