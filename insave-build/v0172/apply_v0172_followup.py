from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
main_path = root / 'MainActivity.kt'

hub = hub_path.read_text()
main = main_path.read_text()

# Physical-phone UX follow-up:
# - a real search field in the normal automatic WhatsApp/Business status flow
# - no arbitrary status cap; RecyclerView virtualizes the complete collection
# - a debounced filter so hundreds of statuses do not cause repeated scans
# - plain song/artist input reaches HomeFragment through its native `url` arg

if 'import androidx.core.widget.doAfterTextChanged\n' not in hub:
    anchor = 'import androidx.documentfile.provider.DocumentFile\n'
    if anchor not in hub:
        raise SystemExit('DocumentFile import anchor missing')
    hub = hub.replace(anchor, anchor + 'import androidx.core.widget.doAfterTextChanged\n', 1)

# Primary/historical UX is automatic discovery after one Special App Access grant.
# Put search in that branch, not in the SAF fallback card.
if 'hint = "Buscar estados"' not in hub:
    anchor = '''        if (automaticGranted) {\n            val info = TextView(this).apply {\n'''
    replacement = '''        if (automaticGranted) {\n            val statusSearch = EditText(this).apply {\n                hint = "Buscar estados"\n                setSingleLine(true)\n                textSize = 15f\n                setTextColor(TEXT)\n                setHintTextColor(MUTED)\n                background = rounded(Color.rgb(44, 35, 46), 18)\n                setPadding(dp(14), dp(11), dp(14), dp(11))\n            }\n            root.addView(statusSearch, LinearLayout.LayoutParams(\n                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT\n            ).apply { setMargins(0, dp(8), 0, dp(6)) })\n            val info = TextView(this).apply {\n'''
    if anchor not in hub:
        raise SystemExit('automatic status branch anchor missing')
    hub = hub.replace(anchor, replacement, 1)

# Wire the automatic repository to the query. Stale delayed callbacks are cheap
# and ignored before any filesystem scan; only the latest text performs I/O.
load_call = '            loadAutomaticStatuses(info, recycler)\n'
if 'statusSearch.doAfterTextChanged' not in hub:
    replacement = '''            statusSearch.doAfterTextChanged { editable ->\n                val querySnapshot = editable?.toString().orEmpty()\n                statusSearch.postDelayed({\n                    if (statusSearch.text.toString() == querySnapshot) {\n                        loadAutomaticStatuses(info, recycler, querySnapshot)\n                    }\n                }, 250L)\n            }\n            loadAutomaticStatuses(info, recycler, statusSearch.text.toString())\n'''
    if load_call not in hub:
        raise SystemExit('automatic status load call missing')
    hub = hub.replace(load_call, replacement, 1)

# Defensive removal of the legacy fallback cap. The automatic repository already
# returns every discovered item and the RecyclerView keeps memory bounded.
hub = hub.replace('                ?.take(180)\n', '')

sig_old = '    private fun loadAutomaticStatuses(info: TextView, recycler: RecyclerView) {\n'
sig_new = '    private fun loadAutomaticStatuses(info: TextView, recycler: RecyclerView, query: String = "") {\n'
if sig_old in hub:
    hub = hub.replace(sig_old, sig_new, 1)
elif sig_new not in hub:
    raise SystemExit('loadAutomaticStatuses signature missing')

# Restrict filtering edits to the automatic loader so SAF remains a safe fallback.
auto_start = hub.find(sig_new)
auto_end = hub.find('    private fun buildDownloadsView(): View {', auto_start)
if auto_start < 0 or auto_end < 0:
    raise SystemExit('automatic status loader boundaries missing')
auto = hub[auto_start:auto_end]
filter_old = '''            val filtered = all.filter {\n                if (filterSnapshot == StatusFilter.IMAGES) it.mime.startsWith("image/") else it.mime.startsWith("video/")\n            }\n'''
filter_new = '''            val querySnapshot = query.trim()\n            val filtered = all.filter { item ->\n                val matchesType = if (filterSnapshot == StatusFilter.IMAGES) {\n                    item.mime.startsWith("image/")\n                } else {\n                    item.mime.startsWith("video/")\n                }\n                matchesType && (querySnapshot.isBlank() || item.name.contains(querySnapshot, ignoreCase = true))\n            }\n'''
if filter_old in auto:
    auto = auto.replace(filter_old, filter_new, 1)
elif 'item.name.contains(querySnapshot, ignoreCase = true)' not in auto:
    raise SystemExit('automatic status filter anchor missing')

info_old = '                    "Imágenes · $images     Videos · $videos"\n'
info_new = '                    "Imágenes · $images     Videos · $videos     Mostrando · ${filtered.size}"\n'
if info_old in auto:
    auto = auto.replace(info_old, info_new, 1)
hub = hub[:auto_start] + auto + hub[auto_end:]

# MainActivity is the maintained engine. It already routes a navigation argument
# named `url` into HomeFragment; bridge our explicit shell extra to that same arg.
if 'intent.getStringExtra("insave_query")' not in main:
    anchor = '''        }else if (action == Intent.ACTION_VIEW){\n\n            val navbarItems = NavbarUtil.getNavBarItems(this)\n'''
    replacement = '''        }else if (action == Intent.ACTION_VIEW){\n            intent.getStringExtra("insave_query")?.trim()?.takeIf { it.isNotEmpty() }?.let { query ->\n                val bundle = Bundle().apply { putString("url", query) }\n                navController.popBackStack(R.id.homeFragment, true)\n                navController.navigate(R.id.homeFragment, bundle)\n                return\n            }\n\n            val navbarItems = NavbarUtil.getNavBarItems(this)\n'''
    if anchor not in main:
        raise SystemExit('MainActivity ACTION_VIEW anchor missing')
    main = main.replace(anchor, replacement, 1)

hub_path.write_text(hub)
main_path.write_text(main)

checks = {
    'status search label': 'hint = "Buscar estados"' in hub,
    'status live filter': 'statusSearch.doAfterTextChanged' in hub,
    'status debounce': '}, 250L)' in hub,
    'status uncapped': '?.take(180)' not in hub,
    'automatic status name filter': 'item.name.contains(querySnapshot, ignoreCase = true)' in hub,
    'automatic result count': 'Mostrando · ${filtered.size}' in hub,
    'plain search bridge': 'intent.getStringExtra("insave_query")' in main and 'putString("url", query)' in main,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave v0.17.2 follow-up gate failed: ' + ', '.join(failed))

print('InSave v0.17.2 follow-up compatibility gate: PASS')
