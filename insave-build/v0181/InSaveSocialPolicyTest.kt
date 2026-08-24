package com.deniscerri.ytdl.insave

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class InSaveSocialPolicyTest {
    @Test
    fun instagramUrlsAreRecognized() {
        val target = InSaveSocialPolicy.classify("https://www.instagram.com/reel/C-test123/")
        assertEquals(InSaveSocialPolicy.Platform.INSTAGRAM, target?.platform)
        assertTrue(InSaveSocialPolicy.matches("https://instagram.com/p/C-test123/", InSaveSocialPolicy.Platform.INSTAGRAM))
        assertFalse(InSaveSocialPolicy.matches("https://instagram.com/p/C-test123/", InSaveSocialPolicy.Platform.FACEBOOK))
    }

    @Test
    fun facebookUrlsAreRecognizedIncludingFbWatch() {
        assertEquals(
            InSaveSocialPolicy.Platform.FACEBOOK,
            InSaveSocialPolicy.classify("https://www.facebook.com/watch/?v=123456789")?.platform,
        )
        assertEquals(
            InSaveSocialPolicy.Platform.FACEBOOK,
            InSaveSocialPolicy.classify("https://fb.watch/test123/")?.platform,
        )
    }

    @Test
    fun nonSocialAndUnsafeUrlsAreRejected() {
        assertNull(InSaveSocialPolicy.classify("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        assertNull(InSaveSocialPolicy.classify("file:///sdcard/video.mp4"))
        assertNull(InSaveSocialPolicy.classify("http://127.0.0.1/video"))
    }
}
