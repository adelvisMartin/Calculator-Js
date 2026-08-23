from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
main_path = root / 'MainActivity.kt'

hub = hub_path.read_text()
main = main_path.read_text()

# Physical-phone UX follow-up:
# - real search in the normal automatic WhatsApp/Business status flow
# - no arbitrary status cap
# - debounced filtering for hundreds of statuses
# - plain song/artist input bridged into HomeFragment's native `url` argument

if 'import androidx.core.widget.doAfterTextChanged\n' not in hub:
    anchor = 'import androidx.documentfile.provider.DocumentFile\n'
    if anchor not in hub:
        raise SystemExit('DocumentFile import anchor missing')
    hub = hub.replace(anchor, anchor + 'import androidx.core.widget.doAfterTextChanged\n', 1)

# Locate the primary automatic UI by its visible loading label. Some recovery
# normalizers leave only a marker comment, so the actual variable name/branch is
# intentionally not used as an anchor here.
auto_label = 'Buscando estados automáticamente'
auto_label_pos = hub.find(auto_label)
if auto_label_pos < 0:
    raise SystemExit('automatic status loading label missing')

if 'hint = "Buscar estados"' not in hub:
    info_pos = hub.rfind('val info = TextView', 0, auto_label_pos)
    if info_pos < 0:
        raise SystemExit('automatic status info view missing')
    line_start = hub.rfind('\n', 0, info_pos) + 1
    indent = hub[line_start:info_pos]
    insert = f'''{indent}val statusSearch = EditText(this).apply {{\n{indent}    hint = "Buscar estados"\n{indent}    setSingleLine(true)\n{indent}    textSize = 15f\n{indent}    setTextColor(TEXT)\n{indent}    setHintTextColor(MUTED)\n{indent}    background = rounded(Color.rgb(44, 35, 46), 18)\n{indent}    setPadding(dp(14), dp(11), dp(14), dp(11))\n{indent}}}\n{indent}root.addView(statusSearch, LinearLayout.LayoutParams(\n{indent}    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT\n{indent}).apply {{ setMargins(0, dp(8), 0, dp(6)) }})\n'''
    hub = hub[:line_start] + insert + hub[line_start:]
    auto_label_pos = hub.find(auto_label)

# Replace the first automatic load after the status-loading label with a
# debounced live query. Only the last keystroke performs filesystem I/O.
if 'statusSearch.doAfterTextChanged' not in hub:
    load_pos = hub.find('loadAutomaticStatuses(info, recycler)', auto_label_pos)
    if load_pos < 0:
        raise SystemExit('automatic status load call missing')
    line_start = hub.rfind('\n', 0, load_pos) + 1
    line_end = hub.find('\n', load_pos)
    if line_end < 0:
        line_end = len(hub)
    indent = hub[line_start:load_pos]
    replacement = f'''{indent}statusSearch.doAfterTextChanged {{ editable ->\n{indent}    val querySnapshot = editable?.toString().orEmpty()\n{indent}    statusSearch.postDelayed({{\n{indent}        if (statusSearch.text.toString() == querySnapshot) {{\n{indent}            loadAutomaticStatuses(info, recycler, querySnapshot)\n{indent}        }}\n{indent}    }}, 250L)\n{indent}}}\n{indent}loadAutomaticStatuses(info, recycler, statusSearch.text.toString())'''
    hub = hub[:line_start] + replacement + hub[line_end:]

# Defensive removal of the old SAF cap as well. RecyclerView virtualizes rows.
hub = hub.replace('                ?.take(180)\n', '')

sig_old = 'private fun loadAutomaticStatuses(info: TextView, recycler: RecyclerView) {'
sig_new = 'private fun loadAutomaticStatuses(info: TextView, recycler: RecyclerView, query: String = "") {'
if sig_old in hub:
    hub = hub.replace(sig_old, sig_new, 1)
elif sig_new not in hub:
    raise SystemExit('loadAutomaticStatuses signature missing')

loader_pos = hub.find(sig_new)
if loader_pos < 0:
    raise SystemExit('automatic loader missing after signature patch')
loader_end = hub.find('private fun buildDownloadsView', loader_pos)
if loader_end < 0:
    raise SystemExit('automatic loader end missing')
auto = hub[loader_pos:loader_end]

filter_old = '''val filtered = all.filter {\n                if (filterSnapshot == StatusFilter.IMAGES) it.mime.startsWith("image/") else it.mime.startsWith("video/")\n            }'''
filter_new = '''val querySnapshot = query.trim()\n            val filtered = all.filter { item ->\n                val matchesType = if (filterSnapshot == StatusFilter.IMAGES) {\n                    item.mime.startsWith("image/")\n                } else {\n                    item.mime.startsWith("video/")\n                }\n                matchesType && (querySnapshot.isBlank() || item.name.contains(querySnapshot, ignoreCase = true))\n            }'''
if filter_old in auto:
    auto = auto.replace(filter_old, filter_new, 1)
elif 'item.name.contains(querySnapshot, ignoreCase = true)' not in auto:
    raise SystemExit('automatic status filter anchor missing')

auto = auto.replace(
    '"Imágenes · $images     Videos · $videos"',
    '"Imágenes · $images     Videos · $videos     Mostrando · ${filtered.size}"',
    1,
)
hub = hub[:loader_pos] + auto + hub[loader_end:]

# Bridge shell text search to the maintained engine.
if 'intent.getStringExtra("insave_query")' not in main:
    action_pos = main.find('}else if (action == Intent.ACTION_VIEW){')
    if action_pos < 0:
        raise SystemExit('MainActivity ACTION_VIEW branch missing')
    insert_pos = main.find('\n', action_pos) + 1
    insertion = '''            intent.getStringExtra("insave_query")?.trim()?.takeIf { it.isNotEmpty() }?.let { query ->\n                val bundle = Bundle().apply { putString("url", query) }\n                navController.popBackStack(R.id.homeFragment, true)\n                navController.navigate(R.id.homeFragment, bundle)\n                return\n            }\n'''
    main = main[:insert_pos] + insertion + main[insert_pos:]

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
