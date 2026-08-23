package com.deniscerri.ytdl.insave

/** Classifies provider failures so fallback is deterministic instead of retrying every error.
 * Private/age/account-required content is never disguised as a transient anonymous failure.
 */
object InSaveProviderFailureClassifier {
    enum class Kind {
        BOT_CHALLENGE,
        HTTP_FORBIDDEN,
        NO_FORMATS,
        NETWORK_TRANSIENT,
        AUTH_REQUIRED,
        CONTENT_UNAVAILABLE,
        CANCELED,
        UNKNOWN
    }

    fun classify(error: Throwable): Kind {
        val message = generateSequence(error) { it.cause }
            .mapNotNull { it.message }
            .joinToString("\n")
            .lowercase()

        return when {
            message.contains("cancel") -> Kind.CANCELED
            message.contains("sign in to confirm you’re not a bot") ||
                message.contains("sign in to confirm you're not a bot") ||
                message.contains("not a bot") -> Kind.BOT_CHALLENGE
            message.contains("http error 403") || message.contains("403 forbidden") ||
                message.contains("status code 403") -> Kind.HTTP_FORBIDDEN
            message.contains("requested format is not available") ||
                message.contains("no video formats found") ||
                message.contains("no formats found") -> Kind.NO_FORMATS
            message.contains("private video") || message.contains("members-only") ||
                message.contains("age-restricted") || message.contains("login required") ||
                message.contains("authentication required") -> Kind.AUTH_REQUIRED
            message.contains("this video is unavailable") || message.contains("video unavailable") ||
                message.contains("removed by the uploader") || message.contains("copyright") -> Kind.CONTENT_UNAVAILABLE
            message.contains("timed out") || message.contains("timeout") ||
                message.contains("connection reset") || message.contains("connection refused") ||
                message.contains("temporary failure") || message.contains("network is unreachable") ||
                message.contains("remote end closed") -> Kind.NETWORK_TRANSIENT
            else -> Kind.UNKNOWN
        }
    }

    fun allowsAnonymousClientFallback(error: Throwable): Boolean = when (classify(error)) {
        Kind.BOT_CHALLENGE,
        Kind.HTTP_FORBIDDEN,
        Kind.NO_FORMATS,
        Kind.NETWORK_TRANSIENT -> true
        else -> false
    }

    val anonymousYoutubeFallbackClients: List<String> = listOf("web_embedded", "android_vr")
}
