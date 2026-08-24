package com.deniscerri.ytdl.insave

/**
 * Central redaction policy for extractor/runtime diagnostics.
 * Download failures remain useful for QA while cookies, authorization headers,
 * PO tokens, visitor data and signed media query parameters are never persisted.
 */
object InSaveRedactor {
    private const val REDACTED = "<redacted>"

    // Authorization values are token-like and must not consume the rest of a
    // diagnostic line. Keeping subsequent error fields makes QA logs useful.
    private val authorizationSecret = Regex(
        "(?i)(authorization|proxy-authorization)\\s*[:=]\\s*(?:Bearer\\s+)?([^,;\\s]+)"
    )

    // Cookie values are themselves compound and may contain semicolon-separated
    // pairs, so redact the complete header value through end-of-line.
    private val cookieSecret = Regex(
        "(?i)(cookie|set-cookie)\\s*[:=]\\s*([^\\r\\n]+)"
    )

    private val namedSecret = Regex(
        "(?i)(po[_-]?token|playerPot|streamingPot|visitor[_-]?data|api[_-]?key|access[_-]?token|refresh[_-]?token)\\s*[=:]\\s*([^,;\\s]+)"
    )
    private val querySecret = Regex(
        "(?i)([?&](?:sig|signature|lsig|token|pot|po_token|visitor_data|expire|expires|key)=)([^&\\s]+)"
    )
    private val bearer = Regex("(?i)Bearer\\s+[A-Za-z0-9._~+\\-/=]+")

    fun redact(value: String?): String {
        if (value.isNullOrEmpty()) return value.orEmpty()
        return value
            .replace(authorizationSecret) { "${it.groupValues[1]}: $REDACTED" }
            .replace(cookieSecret) { "${it.groupValues[1]}: $REDACTED" }
            .replace(namedSecret) { "${it.groupValues[1]}=$REDACTED" }
            .replace(querySecret) { "${it.groupValues[1]}$REDACTED" }
            .replace(bearer, "Bearer $REDACTED")
    }
}
