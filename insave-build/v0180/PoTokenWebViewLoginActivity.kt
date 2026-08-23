package com.deniscerri.ytdl.ui.more.settings.advanced.generateyoutubepotokens.webview

import android.annotation.SuppressLint
import android.content.Intent
import android.content.SharedPreferences
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.MenuItem
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.core.view.children
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.preference.PreferenceManager
import com.deniscerri.ytdl.R
import com.deniscerri.ytdl.database.models.CookieItem
import com.deniscerri.ytdl.database.viewmodel.CookieViewModel
import com.deniscerri.ytdl.insave.InSaveInputPolicy
import com.deniscerri.ytdl.ui.BaseActivity
import com.deniscerri.ytdl.util.UiUtil
import com.deniscerri.ytdl.util.extractors.newpipe.potoken.NewPipePoTokenGenerator
import com.google.android.material.appbar.AppBarLayout
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Native Android WebView implementation for the manual PO-token fallback screen.
 * The former accompanist/web dependency is intentionally removed because that API is
 * unmaintained. Runtime BotGuard generation remains in NewPipePoTokenGenerator; this
 * Activity is only the explicit user-facing fallback/login helper.
 */
class PoTokenWebViewLoginActivity : BaseActivity() {
    private lateinit var webView: WebView
    private lateinit var toolbar: MaterialToolbar
    private lateinit var generateBtn: MaterialButton
    private lateinit var cookieManager: CookieManager
    private lateinit var cookiesViewModel: CookieViewModel
    private lateinit var preferences: SharedPreferences

    private val sampleVideoID = "aqz-KE-bpKQ"
    private var redirectUrl: String? = null
    private var noAuth: Boolean = false

    @SuppressLint("SetJavaScriptEnabled")
    public override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.webview_potoken_activity)

        val requestedUrl = InSaveInputPolicy.normalizeHttpUrl(intent.getStringExtra("url"))
            ?: "https://www.youtube.com/"
        redirectUrl = InSaveInputPolicy.normalizeHttpUrl(intent.getStringExtra("redirect_url"))
        noAuth = intent.getBooleanExtra("no_auth", false)

        cookiesViewModel = ViewModelProvider(this)[CookieViewModel::class.java]
        preferences = PreferenceManager.getDefaultSharedPreferences(this)
        preferences.edit().putString("genenerate_youtube_po_token_preferred_url", requestedUrl).apply()

        val appbar = findViewById<AppBarLayout>(R.id.webview_appbarlayout)
        toolbar = appbar.findViewById(R.id.webviewToolbar)
        toolbar.menu.children.firstOrNull { it.itemId == R.id.incognito }?.isVisible = false
        generateBtn = toolbar.findViewById(R.id.generate)
        webView = findViewById(R.id.webview_native)
        cookieManager = CookieManager.getInstance()

        configureWebView()
        configureToolbar()
        configureBackNavigation()

        if (savedInstanceState == null && noAuth) {
            cookieManager.removeAllCookies(null)
            cookieManager.flush()
        }
        webView.loadUrl(requestedUrl)
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        webView.settings.apply {
            cacheMode = WebSettings.LOAD_NO_CACHE
            domStorageEnabled = false
            setGeolocationEnabled(false)
            javaScriptEnabled = true
            javaScriptCanOpenWindowsAutomatically = false
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) safeBrowsingEnabled = true
        }
        cookieManager.setAcceptThirdPartyCookies(webView, true)
        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val safe = InSaveInputPolicy.normalizeHttpUrl(request.url.toString()) ?: return true
                view.loadUrl(safe)
                return true
            }

            override fun onPageFinished(view: WebView, url: String?) {
                super.onPageFinished(view, url)
                toolbar.title = view.title.orEmpty()
                if (url?.contains("robots.txt") == true) {
                    finishTokenGeneration()
                    return
                }

                val canRedirect = noAuth || url?.contains("youtube.com/account") == true
                if (canRedirect) {
                    view.evaluateJavascript("(function(){return document.readyState;})()") { value ->
                        if (value?.trim('"') == "complete") {
                            Handler(Looper.getMainLooper()).postDelayed({
                                redirectUrl?.let { target ->
                                    view.loadUrl(target, mapOf("Referer" to "https://www.google.com/"))
                                }
                                redirectUrl = null
                            }, 2500)
                        }
                    }
                }
            }
        }
    }

    private fun configureToolbar() {
        toolbar.setOnMenuItemClickListener { item: MenuItem ->
            when (item.itemId) {
                R.id.get_data_sync_id -> webView.evaluateJavascript("ytcfg.get('DATASYNC_ID')") { id ->
                    UiUtil.copyToClipboard(id.replace("\"", ""), this)
                }
                R.id.desktop -> {
                    item.isChecked = !item.isChecked
                    configureDesktopMode(webView, item.isChecked)
                    webView.reload()
                }
            }
            true
        }
        toolbar.setNavigationOnClickListener { finish() }
        generateBtn.setOnClickListener {
            generateBtn.isEnabled = false
            webView.loadUrl("https://www.youtube.com/robots.txt")
        }
    }

    private fun configureBackNavigation() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) webView.goBack() else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    private fun finishTokenGeneration() {
        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                NewPipePoTokenGenerator().getWebClientPoToken(sampleVideoID)
            }
            if (result == null) {
                setResult(RESULT_CANCELED)
            } else {
                setResult(RESULT_OK, Intent().apply {
                    putExtra("visitor_data", result.visitorData)
                    putExtra("player_potoken", result.playerRequestPoToken)
                    putExtra("subs_potoken", result.playerRequestPoToken)
                    putExtra("streaming_potoken", result.streamingDataPoToken)
                })
                updateGeneratedCookies()
            }
            destroyWebView()
            finish()
        }
    }

    private suspend fun updateGeneratedCookies() = withContext(Dispatchers.IO) {
        val cookieURL = "Po Token Generated Cookies"
        cookiesViewModel.getCookiesFromDB(cookieURL).getOrNull()?.let { cookieText ->
            runCatching {
                cookiesViewModel.insert(CookieItem(0, cookieURL, cookieText, cookieURL, true))
                cookiesViewModel.updateCookiesFile()
                preferences.edit().putBoolean("use_cookies", true).apply()
            }.onFailure {
                withContext(Dispatchers.Main) {
                    Toast.makeText(
                        this@PoTokenWebViewLoginActivity,
                        "Tokens were generated but cookies were not updated",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }
        }
    }

    private fun destroyWebView() {
        webView.stopLoading()
        webView.clearCache(true)
        webView.loadUrl("about:blank")
        webView.onPause()
        webView.removeAllViews()
        webView.destroy()
    }

    private fun configureDesktopMode(view: WebView, desktop: Boolean) {
        view.settings.apply {
            if (desktop) {
                userAgentString = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                useWideViewPort = true
                loadWithOverviewMode = true
            } else {
                userAgentString = WebSettings.getDefaultUserAgent(view.context)
                useWideViewPort = false
                loadWithOverviewMode = false
            }
        }
    }

    override fun onDestroy() {
        if (::webView.isInitialized) runCatching { destroyWebView() }
        super.onDestroy()
    }

    companion object {
        const val TAG = "PoTokenWebViewActivity"
    }
}
