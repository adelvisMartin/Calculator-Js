from pathlib import Path

hub_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
ytdlp_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt')

hub = hub_path.read_text()
start_marker = '    private fun buildStatusesView(): View {'
end_marker = '    private fun automaticStatusAccessGranted()'
start = hub.find(start_marker)
end = hub.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Final status view boundaries missing')

final_status_view = '''    private fun buildStatusesView(): View {
        val root = verticalPage()
        root.addView(appTitle("Estados de WhatsApp", "WhatsApp y Business se detectan automáticamente cuando el acceso local está autorizado."))

        val sourceRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        sourceRow.addView(toggleButton("WhatsApp", statusSource == InSaveStatusSource.WHATSAPP, {
            statusSource = InSaveStatusSource.WHATSAPP
            showTab(InSaveTab.STATUSES)
        }, 1f))
        sourceRow.addView(toggleButton("Business", statusSource == InSaveStatusSource.WHATSAPP_BUSINESS, {
            statusSource = InSaveStatusSource.WHATSAPP_BUSINESS
            showTab(InSaveTab.STATUSES)
        }, 1f))
        root.addView(sourceRow)

        val filterRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        filterRow.addView(toggleButton("Imágenes", statusFilter == StatusFilter.IMAGES, {
            statusFilter = StatusFilter.IMAGES
            showTab(InSaveTab.STATUSES)
        }, 1f))
        filterRow.addView(toggleButton("Videos", statusFilter == StatusFilter.VIDEOS, {
            statusFilter = StatusFilter.VIDEOS
            showTab(InSaveTab.STATUSES)
        }, 1f))
        root.addView(filterRow)

        val stored = prefs.getString(statusKey(statusSource), null)?.let(Uri::parse)
        when {
            automaticStatusAccessGranted() -> {
                val info = TextView(this).apply {
                    text = "Buscando estados automáticamente…"
                    setTextColor(MUTED)
                    setPadding(dp(2), dp(14), dp(2), dp(10))
                }
                root.addView(info)
                val recycler = RecyclerView(this).apply {
                    layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)
                    overScrollMode = View.OVER_SCROLL_NEVER
                    isNestedScrollingEnabled = false
                }
                root.addView(recycler, LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
                ))
                root.addView(secondaryButton("Revisar acceso automático") { requestAutomaticStatusAccess() })
                loadAutomaticStatuses(info, recycler)
            }
            stored != null -> {
                val info = TextView(this).apply {
                    text = "Cargando acceso de carpeta de respaldo…"
                    setTextColor(MUTED)
                    setPadding(dp(2), dp(14), dp(2), dp(10))
                }
                root.addView(info)
                val recycler = RecyclerView(this).apply {
                    layoutManager = GridLayoutManager(this@InSaveHubActivity, 2)
                    overScrollMode = View.OVER_SCROLL_NEVER
                    isNestedScrollingEnabled = false
                }
                root.addView(recycler, LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
                ))
                val accessButton = secondaryButton("Cambiar acceso de carpeta") {
                    prefs.edit().remove(statusKey(statusSource)).apply()
                    launchStatusTree(statusSource)
                }
                root.addView(accessButton)
                root.addView(primaryButton("Activar detección automática") { requestAutomaticStatusAccess() })
                loadStatuses(stored, info, recycler, accessButton)
            }
            else -> {
                root.addView(card().apply {
                    addView(sectionTitle("Activar Estados automáticos"))
                    addView(body("Autoriza el acceso especial una sola vez. Después InSave leerá WhatsApp y WhatsApp Business desde Android/media al entrar en Estados."))
                    addView(primaryButton("Activar acceso automático") { requestAutomaticStatusAccess() })
                    addView(secondaryButton("Elegir carpeta manualmente (fallback)") { launchStatusTree(statusSource) })
                })
            }
        }
        return ScrollView(this).apply { addView(root) }
    }

'''
hub_path.write_text(hub[:start] + final_status_view + hub[end:])

# apply_v0170 originally touched the first canUseWriteInfoJson occurrence in the file.
# The direct-stream variable exists only inside buildYTDLRequest, so remove any accidental
# reference before that method and add the guard only inside the method.
ytdlp = ytdlp_path.read_text()
method_marker = '    fun buildYTDLRequest(downloadItem: DownloadItem) : YTDLRequest {'
pos = ytdlp.find(method_marker)
if pos < 0:
    raise SystemExit('buildYTDLRequest boundary missing')
head = ytdlp[:pos]
tail = ytdlp[pos:]
head = head.replace(
    '                    !request.toString().contains("--download-sections") &&\n                inSaveDirectYoutubeAudioUrl.isNullOrBlank()',
    '                    !request.toString().contains("--download-sections")',
)
head = head.replace(
    '                !request.toString().contains("--download-sections") &&\n                inSaveDirectYoutubeAudioUrl.isNullOrBlank()',
    '                !request.toString().contains("--download-sections")',
)

correct_anchor = '''            val canUseWriteInfoJson =
                !sharedPreferences.getBoolean("disable_write_info_json", false) &&
                !request.toString().contains("--download-sections")
'''
correct_replacement = '''            val canUseWriteInfoJson =
                !sharedPreferences.getBoolean("disable_write_info_json", false) &&
                !request.toString().contains("--download-sections") &&
                inSaveDirectYoutubeAudioUrl.isNullOrBlank()
'''
if correct_anchor in tail:
    tail = tail.replace(correct_anchor, correct_replacement, 1)
elif 'inSaveDirectYoutubeAudioUrl.isNullOrBlank()' not in tail:
    raise SystemExit('Could not apply buildYTDLRequest info-json guard')

ytdlp_path.write_text(head + tail)

assert 'toggleButton("WhatsApp", statusSource == InSaveStatusSource.WHATSAPP, {' in hub_path.read_text()
assert 'loadStatuses(stored, info, recycler, accessButton)' in hub_path.read_text()
assert 'inSaveDirectYoutubeAudioUrl' not in ytdlp_path.read_text()[:ytdlp_path.read_text().find(method_marker)]
print('InSave v0.17 generated Kotlin compile fixes: PASS')
