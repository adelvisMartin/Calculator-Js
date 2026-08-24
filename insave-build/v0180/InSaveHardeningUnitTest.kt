package com.deniscerri.ytdl.insave

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class InSaveHardeningUnitTest {
    @Test
    fun inputPolicyAcceptsPublicHttpsAndSearch() {
        val url = InSaveInputPolicy.classify("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assertTrue(url is InSaveInputPolicy.Input.Url)
        val search = InSaveInputPolicy.classify("  artista   canción  ")
        assertEquals("artista canción", (search as InSaveInputPolicy.Input.Search).value)
    }

    @Test
    fun inputPolicyRejectsDangerousSchemesCredentialsAndPrivateLiterals() {
        assertNull(InSaveInputPolicy.classify("javascript:alert(1)"))
        assertNull(InSaveInputPolicy.classify("file:///sdcard/secret.txt"))
        assertNull(InSaveInputPolicy.normalizeHttpUrl("https://user:pass@example.com/video"))
        assertNull(InSaveInputPolicy.normalizeHttpUrl("http://127.0.0.1/admin"))
        assertNull(InSaveInputPolicy.normalizeHttpUrl("http://192.168.1.20/media"))
        assertNull(InSaveInputPolicy.normalizeProviderEndpoint("http://example.com"))
        assertNotNull(InSaveInputPolicy.normalizeProviderEndpoint("https://example.com/api"))
    }

    @Test
    fun redactorRemovesRuntimeSecretsButKeepsUsefulError() {
        val raw = "ERROR 403 Authorization: Bearer abc.def po_token=secret-value visitor_data=visitor-secret-value https://x.test/v?sig=signed-value&foo=1"
        val clean = InSaveRedactor.redact(raw)
        assertTrue(clean.contains("ERROR 403"))
        assertFalse(clean.contains("abc.def"))
        assertFalse(clean.contains("secret-value"))
        assertFalse(clean.contains("visitor-secret-value"))
        assertFalse(clean.contains("signed-value"))
        assertTrue(clean.contains("visitor_data=<redacted>"))
        assertTrue(clean.contains("foo=1"))
    }

    @Test
    fun providerFailureClassifierSeparatesBotFromPrivateContent() {
        assertEquals(
            InSaveProviderFailureClassifier.Kind.BOT_CHALLENGE,
            InSaveProviderFailureClassifier.classify(Exception("Sign in to confirm you're not a bot"))
        )
        assertTrue(
            InSaveProviderFailureClassifier.allowsAnonymousClientFallback(
                Exception("HTTP Error 403: Forbidden")
            )
        )
        assertFalse(
            InSaveProviderFailureClassifier.allowsAnonymousClientFallback(
                Exception("Private video. Login required")
            )
        )
        assertEquals(listOf("web_embedded", "android_vr"), InSaveProviderFailureClassifier.anonymousYoutubeFallbackClients)
    }
}
