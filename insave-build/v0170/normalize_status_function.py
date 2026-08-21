from pathlib import Path

p = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
s = p.read_text()
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
        sourceRow.addView(toggleButton("WhatsApp", statusSource == InSaveStatusSource.WHATSAPP) {
            statusSource = InSaveStatusSource.WHATSAPP
            showTab(InSaveTab.STATUSES)
        }, 1f)
        sourceRow.addView(toggleButton("Business", statusSource == InSaveStatusSource.WHATSAPP_BUSINESS) {
            statusSource = InSaveStatusSource.WHATSAPP_BUSINESS
            showTab(InSaveTab.STATUSES)
        }, 1f)
        root.addView(sourceRow)

        val filterRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        filterRow.addView(toggleButton("Imágenes", statusFilter == StatusFilter.IMAGES) {
            statusFilter = StatusFilter.IMAGES
            showTab(InSaveTab.STATUSES)
        }, 1f)
        filterRow.addView(toggleButton("Videos", statusFilter == StatusFilter.VIDEOS) {
            statusFilter = StatusFilter.VIDEOS
            showTab(InSaveTab.STATUSES)
        }, 1f)
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
            root.addView(secondaryButton("Cambiar acceso de carpeta") {
                prefs.edit().remove(statusKey(statusSource)).apply()
                launchStatusTree(statusSource)
            })
            loadStatuses(stored, info, recycler)
        }
        return ScrollView(this).apply { addView(root) }
    }

'''
p.write_text(s[:start] + canonical + s[end:])
print('InSave status function normalization: PASS')
