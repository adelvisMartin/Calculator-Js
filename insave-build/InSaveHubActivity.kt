package com.deniscerri.ytdl.insave

import android.app.Activity
import android.content.ClipDescription
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.documentfile.provider.DocumentFile
import androidx.lifecycle.lifecycleScope
import androidx.preference.PreferenceManager
import com.deniscerri.ytdl.MainActivity
import com.deniscerri.ytdl.database.models.YoutubeGeneratePoTokenItem
import com.deniscerri.ytdl.database.models.YoutubePoTokenItem
import com.deniscerri.ytdl.receiver.ShareActivity
import com.deniscerri.ytdl.ui.more.settings.SettingsActivity
import com.deniscerri.ytdl.ui.more.settings.advanced.generateyoutubepotokens.webview.PoTokenWebViewLoginActivity
import com.deniscerri.ytdl.util.ThemeUtil
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.text.DateFormat
import java.util.Date

enum class InSaveStatusSource { WHATSAPP, WHATSAPP_BUSINESS }
data class InSaveStatus(val uri: Uri, val name: String, val mime: String, val modified: Long)
data class InSaveFollowersReport(
    val followers: Set<String>,
    val following: Set<String>,
    val mutuals: Set<String>,
    val notFollowingBack: Set<String>,
    val youDoNotFollowBack: Set<String>,
)

class InSaveHubActivity : AppCompatActivity() {
    private val prefs by lazy { PreferenceManager.getDefaultSharedPreferences(this) }
    private lateinit var urlInput: EditText
    private var followersJson: String? = null
    private var followingJson: String? = null

    private val whatsappTreeLauncher = registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        uri?.let { persistStatusTree(InSaveStatusSource.WHATSAPP, it) }
    }
    private val businessTreeLauncher = registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        uri?.let { persistStatusTree(InSaveStatusSource.WHATSAPP_BUSINESS, it) }
    }
    private val followersFileLauncher = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        uri?.let {
            followersJson = readText(it)
            maybeAnalyzeFollowers()
        }
    }
    private val followingFileLauncher = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        uri?.let {
            followingJson = readText(it)
            maybeAnalyzeFollowers()
        }
    }
    private val poTokenLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            if (storePoTokens(result.data!!)) {
                toast("PO Token guardado. Reintenta YouTube sin iniciar sesión.")
            } else {
                toast("El generador respondió sin tokens utilizables. Inténtalo nuevamente.")
            }
        } else {
            toast("No se generó el PO Token. No se inició sesión en YouTube.")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        applyInSaveDefaults()
        ThemeUtil.updateTheme(this)
        title = "InSave"
        setContentView(buildContent())
        consumeIncomingIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        consumeIncomingIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        if (::urlInput.isInitialized) {
            urlInput.postDelayed({ autoPasteUrlIfAllowed() }, 250)
        }
    }

    private fun applyInSaveDefaults() {
        if (!prefs.getBoolean("insave_brand_initialized", false)) {
            prefs.edit()
                .putBoolean("insave_brand_initialized", true)
                .putString("theme_accent", "purple")
                .putString("ytdlnis_theme", "Dark")
                .putString("search_engine", "ytsearch")
                .putString("formats_source", "yt-dlp")
                .putBoolean("download_card", true)
                .apply()
        }
    }

    private fun buildContent(): View {
        val scroll = ScrollView(this).apply { setBackgroundColor(BG) }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(32))
        }
        root.addView(TextView(this).apply {
            text = "InSave"
            textSize = 30f
            setTextColor(TEXT)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        root.addView(TextView(this).apply {
            text = "Descargas y herramientas locales · v0.16.0-RC"
            textSize = 14f
            setTextColor(SOFT)
            setPadding(0, dp(4), 0, dp(18))
        })

        urlInput = EditText(this).apply {
            hint = "Pega o copia un enlace"
            setHintTextColor(MUTED)
            setTextColor(TEXT)
            minHeight = dp(56)
            backgroundTintList = ColorStateList.valueOf(ACCENT)
            setPadding(dp(12), dp(8), dp(12), dp(8))
        }
        root.addView(urlInput, LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        root.addView(actionButton("Abrir / descargar enlace") { openUrlOrDownloader() })
        root.addView(actionButton("Buscar en YouTube y otros sitios") { openDownloader() })
        root.addView(actionButton("Reparar YouTube sin login (PO Token)") { generatePoTokenNoLogin() })

        root.addView(sectionTitle("Estados"))
        root.addView(actionButton("Estados de WhatsApp") { openStatuses(InSaveStatusSource.WHATSAPP) })
        root.addView(actionButton("Estados de WhatsApp Business") { openStatuses(InSaveStatusSource.WHATSAPP_BUSINESS) })

        root.addView(sectionTitle("Instagram"))
        root.addView(actionButton("Analizar seguidores / seguidos (JSON)") {
            followersJson = null
            followingJson = null
            followersFileLauncher.launch(arrayOf("application/json", "text/json", "text/plain"))
            toast("Selecciona primero el archivo de seguidores.")
        })

        root.addView(sectionTitle("Gestión"))
        root.addView(actionButton("Descargas, cola y playlists") { openDownloader() })
        root.addView(actionButton("Ajustes y sesiones web") { startActivity(Intent(this, SettingsActivity::class.java)) })

        root.addView(TextView(this).apply {
            text = "YouTube público se intenta sin sesión. El PO Token es un fallback sin autenticación. Instagram, Facebook, TikTok, playlists y selección múltiple usan el motor mantenido; Estados y Seguidores se procesan localmente."
            textSize = 13f
            setTextColor(MUTED)
            setPadding(0, dp(22), 0, 0)
        })
        scroll.addView(root)
        return scroll
    }

    private fun actionButton(label: String, action: () -> Unit): Button = Button(this).apply {
        text = label
        isAllCaps = false
        textSize = 15f
        setTextColor(Color.WHITE)
        backgroundTintList = ColorStateList.valueOf(ACCENT)
        minHeight = dp(52)
        gravity = Gravity.CENTER
        setOnClickListener { action() }
        layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = dp(10) }
    }

    private fun sectionTitle(label: String): TextView = TextView(this).apply {
        text = label
        textSize = 18f
        setTextColor(TEXT)
        setTypeface(typeface, android.graphics.Typeface.BOLD)
        setPadding(0, dp(24), 0, dp(2))
    }

    private fun openDownloader() = startActivity(Intent(this, MainActivity::class.java))

    private fun openUrlOrDownloader() {
        val url = normalizeUrl(urlInput.text.toString())
        if (url == null) {
            openDownloader()
            return
        }
        startActivity(Intent(this, ShareActivity::class.java).apply {
            action = Intent.ACTION_SEND
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, url)
        })
    }

    private fun generatePoTokenNoLogin() {
        poTokenLauncher.launch(Intent(this, PoTokenWebViewLoginActivity::class.java).apply {
            putExtra("url", "https://www.youtube.com")
            putExtra("redirect_url", "https://www.youtube.com/watch?v=aqz-KE-bpKQ")
            putExtra("no_auth", true)
        })
    }

    private fun storePoTokens(data: Intent): Boolean {
        val streaming = data.getStringExtra("streaming_potoken").orEmpty()
        val player = data.getStringExtra("player_potoken").orEmpty()
        val subs = data.getStringExtra("subs_potoken").orEmpty()
        val visitorData = data.getStringExtra("visitor_data").orEmpty()
        if (streaming.isBlank() || player.isBlank()) return false

        val current = runCatching {
            Gson().fromJson(
                prefs.getString("youtube_generated_po_tokens", "[]").orEmpty().ifEmpty { "[]" },
                Array<YoutubeGeneratePoTokenItem>::class.java
            ).toMutableList()
        }.getOrDefault(mutableListOf())
        current.removeAll { item -> item.clients.any { it.contains("web") } }
        current += YoutubeGeneratePoTokenItem(
            true,
            mutableListOf("mweb"),
            mutableListOf(
                YoutubePoTokenItem("gvs", streaming),
                YoutubePoTokenItem("player", player),
                YoutubePoTokenItem("subs", if (subs.isBlank()) player else subs),
            ),
            visitorData,
            visitorData.isNotBlank(),
        )
        prefs.edit().putString("youtube_generated_po_tokens", Gson().toJson(current)).apply()
        return true
    }

    private fun consumeIncomingIntent(intent: Intent?) {
        if (!::urlInput.isInitialized || intent == null) return
        val candidate = when (intent.action) {
            Intent.ACTION_SEND -> intent.getStringExtra(Intent.EXTRA_TEXT)
            Intent.ACTION_VIEW -> intent.dataString
            else -> null
        }
        normalizeUrl(candidate.orEmpty())?.let {
            urlInput.setText(it)
            urlInput.setSelection(it.length)
        }
    }

    private fun autoPasteUrlIfAllowed() {
        if (!window.hasWindowFocus()) return
        val manager = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
        val clip = manager.primaryClip ?: return
        val description = manager.primaryClipDescription ?: return
        if (!description.hasMimeType(ClipDescription.MIMETYPE_TEXT_PLAIN) &&
            !description.hasMimeType(ClipDescription.MIMETYPE_TEXT_URILIST)) return
        val value = clip.getItemAt(0).coerceToText(this)?.toString().orEmpty()
        normalizeUrl(value)?.let {
            if (urlInput.text.toString() != it) {
                urlInput.setText(it)
                urlInput.setSelection(it.length)
            }
        }
    }

    private fun normalizeUrl(raw: String): String? {
        val candidate = raw.trim().lineSequence().firstOrNull().orEmpty().trim()
        if (candidate.isBlank()) return null
        val uri = runCatching { Uri.parse(candidate) }.getOrNull() ?: return null
        if (uri.scheme?.lowercase() !in setOf("http", "https") || uri.host.isNullOrBlank()) return null
        return candidate
    }

    private fun statusKey(source: InSaveStatusSource): String = "insave_status_tree_${source.name.lowercase()}"

    private fun persistStatusTree(source: InSaveStatusSource, uri: Uri) {
        runCatching { contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION) }
        prefs.edit().putString(statusKey(source), uri.toString()).apply()
        showStatusPicker(source, uri)
    }

    private fun openStatuses(source: InSaveStatusSource) {
        val stored = prefs.getString(statusKey(source), null)?.let(Uri::parse)
        if (stored != null) showStatusPicker(source, stored)
        else {
            toast("Selecciona exactamente la carpeta Media/.Statuses; InSave conservará ese acceso.")
            launchStatusTree(source)
        }
    }

    private fun launchStatusTree(source: InSaveStatusSource) {
        if (source == InSaveStatusSource.WHATSAPP) whatsappTreeLauncher.launch(null)
        else businessTreeLauncher.launch(null)
    }

    private fun showStatusPicker(source: InSaveStatusSource, tree: Uri) {
        lifecycleScope.launch(Dispatchers.IO) {
            val root = DocumentFile.fromTreeUri(this@InSaveHubActivity, tree)
            val items = root?.listFiles()?.asSequence()
                ?.filter { it.isFile }
                ?.mapNotNull { file ->
                    val name = file.name ?: return@mapNotNull null
                    val mime = file.type ?: mimeFromName(name) ?: return@mapNotNull null
                    if (!mime.startsWith("image/") && !mime.startsWith("video/")) return@mapNotNull null
                    InSaveStatus(file.uri, name, mime, file.lastModified())
                }
                ?.sortedByDescending { it.modified }
                ?.take(150)
                ?.toList()
                .orEmpty()

            withContext(Dispatchers.Main) {
                if (items.isEmpty()) {
                    AlertDialog.Builder(this@InSaveHubActivity)
                        .setTitle(if (source == InSaveStatusSource.WHATSAPP) "WhatsApp" else "WhatsApp Business")
                        .setMessage("No encontré estados en esa carpeta. Selecciona exactamente Media/.Statuses.")
                        .setPositiveButton("Cambiar carpeta") { _, _ ->
                            prefs.edit().remove(statusKey(source)).apply()
                            launchStatusTree(source)
                        }
                        .setNegativeButton("Cerrar", null)
                        .show()
                    return@withContext
                }
                val selected = BooleanArray(items.size)
                val dateFormat = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                val labels = items.mapIndexed { index, item ->
                    val kind = if (item.mime.startsWith("video/")) "Video" else "Foto"
                    "$kind ${index + 1} · ${dateFormat.format(Date(item.modified))}"
                }.toTypedArray()
                AlertDialog.Builder(this@InSaveHubActivity)
                    .setTitle("Selecciona estados (${items.size})")
                    .setMultiChoiceItems(labels, selected) { _, which, checked -> selected[which] = checked }
                    .setPositiveButton("Guardar seleccionados") { _, _ ->
                        val chosen = items.filterIndexed { index, _ -> selected[index] }
                        if (chosen.isEmpty()) toast("No seleccionaste ningún estado.") else saveStatuses(chosen)
                    }
                    .setNeutralButton("Cambiar carpeta") { _, _ ->
                        prefs.edit().remove(statusKey(source)).apply()
                        launchStatusTree(source)
                    }
                    .setNegativeButton("Cancelar", null)
                    .show()
            }
        }
    }

    private fun saveStatuses(items: List<InSaveStatus>) {
        lifecycleScope.launch(Dispatchers.IO) {
            var saved = 0
            items.forEach { if (copyStatusToDownloads(it)) saved++ }
            withContext(Dispatchers.Main) { toast("Guardados $saved de ${items.size} en Downloads/InSave.") }
        }
    }

    private fun copyStatusToDownloads(item: InSaveStatus): Boolean = runCatching {
        val input = contentResolver.openInputStream(item.uri) ?: return@runCatching false
        input.use { src ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val collection = if (item.mime.startsWith("video/")) {
                    MediaStore.Video.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
                } else {
                    MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
                }
                val values = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, item.name)
                    put(MediaStore.MediaColumns.MIME_TYPE, item.mime)
                    put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/InSave")
                    put(MediaStore.MediaColumns.IS_PENDING, 1)
                }
                val outUri = contentResolver.insert(collection, values) ?: return@runCatching false
                contentResolver.openOutputStream(outUri, "w")!!.use { out -> src.copyTo(out) }
                contentResolver.update(outUri, ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }, null, null)
            } else {
                val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "InSave").apply { mkdirs() }
                FileOutputStream(File(dir, item.name)).use { out -> src.copyTo(out) }
            }
        }
        true
    }.getOrDefault(false)

    private fun mimeFromName(name: String): String? = when (name.substringAfterLast('.', "").lowercase()) {
        "jpg", "jpeg" -> "image/jpeg"
        "png" -> "image/png"
        "webp" -> "image/webp"
        "heic", "heif" -> "image/heic"
        "mp4" -> "video/mp4"
        "webm" -> "video/webm"
        "mkv" -> "video/x-matroska"
        "mov" -> "video/quicktime"
        "3gp" -> "video/3gpp"
        else -> null
    }

    private fun readText(uri: Uri): String? = runCatching {
        contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
    }.getOrNull()

    private fun maybeAnalyzeFollowers() {
        if (followersJson == null) return
        if (followingJson == null) {
            followingFileLauncher.launch(arrayOf("application/json", "text/json", "text/plain"))
            toast("Ahora selecciona el archivo de cuentas que sigues.")
            return
        }
        val report = runCatching { analyzeInstagram(followersJson!!, followingJson!!) }.getOrElse {
            toast("No pude interpretar esos archivos de Instagram.")
            return
        }
        showFollowersReport(report)
    }

    private fun analyzeInstagram(followersRaw: String, followingRaw: String): InSaveFollowersReport {
        val followers = collectUsernames(followersRaw).toSet()
        val following = collectUsernames(followingRaw).toSet()
        return InSaveFollowersReport(
            followers,
            following,
            followers intersect following,
            following - followers,
            followers - following,
        )
    }

    private fun collectUsernames(raw: String): List<String> {
        val out = linkedSetOf<String>()
        fun canonical(value: String): String? {
            var v = value.trim()
            if (v.isEmpty()) return null
            v = v.substringAfterLast("instagram.com/", v).substringBefore('?').substringBefore('/').removePrefix("@").trim()
            if (!Regex("^[A-Za-z0-9._]{1,30}$").matches(v)) return null
            return v.lowercase()
        }
        fun walk(value: Any?) {
            when (value) {
                is JSONObject -> value.keys().forEach { key ->
                    if (key == "value" || key == "title" || key == "href") canonical(value.optString(key))?.let(out::add)
                    walk(value.opt(key))
                }
                is JSONArray -> for (i in 0 until value.length()) walk(value.opt(i))
            }
        }
        val trimmed = raw.trim()
        if (trimmed.startsWith("[")) walk(JSONArray(trimmed)) else if (trimmed.startsWith("{")) walk(JSONObject(trimmed))
        return out.toList()
    }

    private fun showFollowersReport(report: InSaveFollowersReport) {
        val text = buildString {
            appendLine("Seguidores: ${report.followers.size}")
            appendLine("Siguiendo: ${report.following.size}")
            appendLine("Mutuos: ${report.mutuals.size}")
            appendLine("No te siguen de vuelta: ${report.notFollowingBack.size}")
            appendLine("Tú no sigues de vuelta: ${report.youDoNotFollowBack.size}")
            appendLine()
            appendLine("NO TE SIGUEN DE VUELTA")
            report.notFollowingBack.sorted().take(500).forEach { appendLine("@$it") }
            appendLine()
            appendLine("TÚ NO SIGUES DE VUELTA")
            report.youDoNotFollowBack.sorted().take(500).forEach { appendLine("@$it") }
        }
        val content = TextView(this).apply {
            setText(text)
            setTextColor(TEXT)
            textSize = 14f
            setPadding(dp(20), dp(12), dp(20), dp(12))
            setTextIsSelectable(true)
        }
        AlertDialog.Builder(this)
            .setTitle("Seguidores de Instagram")
            .setView(ScrollView(this).apply { addView(content) })
            .setPositiveButton("Cerrar", null)
            .show()
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    companion object {
        private val BG = Color.rgb(18, 13, 19)
        private val TEXT = Color.rgb(247, 238, 244)
        private val SOFT = Color.rgb(240, 167, 204)
        private val MUTED = Color.rgb(190, 170, 183)
        private val ACCENT = Color.rgb(190, 59, 128)
    }
}
