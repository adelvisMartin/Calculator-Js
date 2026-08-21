from pathlib import Path

hub_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
ytdlp_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt')

s = hub_path.read_text()
start_marker = '    private fun buildStatusesView(): View {'
end_marker = '    private fun buildDownloadsView(): View {'
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Could not locate buildStatusesView boundaries')

canonical = '''    private fun buildStatusesView(): View {
        val root = verticalPage()
        root.addView(appTitle("Estados de WhatsApp", "Previsualiza primero y guarda cada estado dentro de InSave."))

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
        if (stored == null) {
            root.addView(card().apply {
                addView(sectionTitle(if (statusSource == InSaveStatusSource.WHATSAPP) "Conectar WhatsApp" else "Conectar WhatsApp Business"))
                addView(body("Acceso de carpeta de respaldo."))
                addView(primaryButton("Conectar una sola vez") { launchStatusTree(statusSource) })
            })
        } else {
            val info = TextView(this).apply {
                text = "Cargando estados…"
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
            loadStatuses(stored, info, recycler, accessButton)
        }
        return ScrollView(this).apply { addView(root) }
    }

'''

# v0.16.2 changed loadStatuses to a four-argument helper. The v0.17 patch still contains
# a legacy three-argument fallback call, so provide a small overload to preserve compatibility.
overload = '''    private fun loadStatuses(tree: Uri, info: TextView, recycler: RecyclerView) {
        val accessButton = secondaryButton("Cambiar acceso de carpeta") { launchStatusTree(statusSource) }
        loadStatuses(tree, info, recycler, accessButton)
    }

'''
new_hub = s[:start] + canonical + s[end:]
if 'private fun loadStatuses(tree: Uri, info: TextView, recycler: RecyclerView) {' not in new_hub:
    insert_at = new_hub.find(end_marker)
    if insert_at < 0:
        raise SystemExit('Could not insert loadStatuses compatibility overload')
    new_hub = new_hub[:insert_at] + overload + new_hub[insert_at:]
hub_path.write_text(new_hub)

# apply_v0170 adds its direct-stream info-json guard by replacing the first textual match.
# Make the earlier getFormats() check equivalent but textually different so the recovery guard
# lands inside buildYTDLRequest, where the direct-stream variable actually exists.
y = ytdlp_path.read_text()
build_pos = y.find('    fun buildYTDLRequest(downloadItem: DownloadItem) : YTDLRequest {')
if build_pos < 0:
    raise SystemExit('buildYTDLRequest not found during normalization')
head = y[:build_pos]
tail = y[build_pos:]
old = '!request.toString().contains("--download-sections")'
if old in head:
    head = head.replace(old, '!request.buildCommand().contains("--download-sections")', 1)
ytdlp_path.write_text(head + tail)

print('InSave status/YTDLP pre-patch normalization: PASS')
