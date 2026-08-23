package com.deniscerri.ytdl.insave

/**
 * Central redaction policy for extractor/runtime diagnostics.
 * Download failures remain useful for QA while cookies, authorization headers,
 * PO tokens, visitor data and signed media query parameters are never persisted.
 */
object InSaveRedactor {
    private const val REDACTED = "<redacted>"

    private val headerSecret = Regex(
        "(?i)(authorization|proxy-authorization|cookie|set-cookie)\\s*[:=]\\s*([^\\r\\n]+)"
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
            .replace(headerSecret) { "${it.groupValues[1]}: $REDACTED" }
            .replace(namedSecret) { "${it.groupValues[1]}=$REDACTED" }
            .replace(querySecret) { "${it.groupValues[1]}$REDACTED" }
            .replace(bearer, "Bearer $REDACTED")
    }
}
