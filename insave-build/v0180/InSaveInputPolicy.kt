package com.deniscerri.ytdl.insave

import java.net.URI

/** Security boundary for all text/URL values that can enter InSave from an exported
 * component, clipboard/paste, search box or configured remote provider.
 *
 * The downloader remains multi-site, so this policy intentionally does not hard-code
 * a small host allowlist. It instead constrains schemes, lengths, credentials and
 * loopback/private literal hosts. This prevents external intents from being turned into
 * file/content/javascript loads or obvious local-network probes.
 */
object InSaveInputPolicy {
    const val MAX_URL_LENGTH = 4096
    const val MAX_SEARCH_LENGTH = 256

    private val ipv4 = Regex("^(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})$")
    private val controls = Regex("[\\u0000-\\u001F\\u007F]")

    sealed interface Input {
        data class Url(val value: String) : Input
        data class Search(val value: String) : Input
    }

    fun classify(raw: String?): Input? {
        val cleaned = raw?.trim()?.takeIf { it.isNotEmpty() } ?: return null
        normalizeHttpUrl(cleaned)?.let { return Input.Url(it) }
        if (looksLikeExplicitUri(cleaned)) return null
        return sanitizeSearch(cleaned)?.let(Input::Search)
    }

    fun normalizeHttpUrl(raw: String?): String? {
        val value = raw?.trim()?.takeIf { it.isNotEmpty() && it.length <= MAX_URL_LENGTH } ?: return null
        if (controls.containsMatchIn(value)) return null
        val parsed = runCatching { URI(value) }.getOrNull() ?: return null
        val scheme = parsed.scheme?.lowercase() ?: return null
        if (scheme !in setOf("http", "https")) return null
        if (!parsed.userInfo.isNullOrBlank()) return null
        val host = parsed.host?.trimEnd('.')?.lowercase()?.takeIf { it.isNotBlank() } ?: return null
        if (isPrivateOrLoopbackLiteral(host)) return null
        return parsed.normalize().toASCIIString()
    }

    fun sanitizeSearch(raw: String?): String? {
        val value = raw?.trim()?.takeIf { it.isNotEmpty() } ?: return null
        val normalized = controls.replace(value, " ")
            .replace(Regex("\\s+"), " ")
            .trim()
        if (normalized.isEmpty()) return null
        return normalized.take(MAX_SEARCH_LENGTH)
    }

    /** Remote Provider C must be TLS in release. Emulator loopback is allowed only when
     * explicitly requested by the caller (debug/QA). Private RFC1918 literal endpoints are
     * intentionally rejected to avoid silently turning provider configuration into SSRF.
     */
    fun normalizeProviderEndpoint(raw: String?, allowLocalDebug: Boolean = false): String? {
        val value = raw?.trim()?.trimEnd('/')?.takeIf { it.isNotEmpty() && it.length <= MAX_URL_LENGTH } ?: return null
        if (controls.containsMatchIn(value)) return null
        val uri = runCatching { URI(value) }.getOrNull() ?: return null
        val scheme = uri.scheme?.lowercase() ?: return null
        val host = uri.host?.trimEnd('.')?.lowercase()?.takeIf { it.isNotBlank() } ?: return null
        if (!uri.userInfo.isNullOrBlank()) return null
        val local = host in setOf("127.0.0.1", "localhost", "10.0.2.2", "::1", "[::1]")
        if (local && allowLocalDebug && scheme == "http") return uri.normalize().toASCIIString().trimEnd('/')
        if (scheme != "https" || isPrivateOrLoopbackLiteral(host)) return null
        return uri.normalize().toASCIIString().trimEnd('/')
    }

    fun isSafeProviderResponseUrl(raw: String?, allowLocalDebug: Boolean = false): Boolean {
        val value = raw?.trim()?.takeIf { it.isNotEmpty() && it.length <= MAX_URL_LENGTH } ?: return false
        val uri = runCatching { URI(value) }.getOrNull() ?: return false
        val scheme = uri.scheme?.lowercase() ?: return false
        val host = uri.host?.trimEnd('.')?.lowercase()?.takeIf { it.isNotBlank() } ?: return false
        if (!uri.userInfo.isNullOrBlank()) return false
        val local = host in setOf("127.0.0.1", "localhost", "10.0.2.2", "::1", "[::1]")
        if (local && allowLocalDebug && scheme == "http") return true
        return scheme == "https" && !isPrivateOrLoopbackLiteral(host)
    }

    private fun looksLikeExplicitUri(value: String): Boolean =
        Regex("^[A-Za-z][A-Za-z0-9+.-]*:").containsMatchIn(value)

    private fun isPrivateOrLoopbackLiteral(host: String): Boolean {
        val h = host.removePrefix("[").removeSuffix("]").lowercase()
        if (h == "localhost" || h == "::1" || h.endsWith(".localhost")) return true
        if (h.startsWith("fc") || h.startsWith("fd") || h.startsWith("fe80:")) return true
        val match = ipv4.matchEntire(h) ?: return false
        val parts = match.groupValues.drop(1).map { it.toIntOrNull() ?: return true }
        if (parts.any { it !in 0..255 }) return true
        val (a, b, _, _) = parts
        return a == 0 || a == 10 || a == 127 ||
            (a == 169 && b == 254) ||
            (a == 172 && b in 16..31) ||
            (a == 192 && b == 168) ||
            (a == 100 && b in 64..127) ||
            a >= 224
    }
}
