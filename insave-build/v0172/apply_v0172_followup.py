from pathlib import Path

root = Path('upstream/app/src/main/java/com/deniscerri/ytdl')
hub_path = root / 'insave/InSaveHubActivity.kt'
main_path = root / 'MainActivity.kt'

hub = hub_path.read_text()
main = main_path.read_text()

# P0 UX follow-up from physical-phone QA:
# - expose a real live search field for WhatsApp/Business statuses
# - never truncate the status repository to an arbitrary item cap
# - bridge plain song/artist queries from the InSave shell into HomeFragment
#   using the same navigation argument consumed by the maintained engine.

if 'import androidx.core.widget.doAfterTextChanged\n' not in hub:
    anchor = 'import androidx.documentfile.provider.DocumentFile\n'
    if anchor not in hub:
        raise SystemExit('DocumentFile import anchor missing')
    hub = hub.replace(anchor, anchor + 'import androidx.core.widget.doAfterTextChanged\n', 1)

# Add the status search only inside the granted-access branch so the compact
# connection screen remains uncluttered when the user has not authorized a tree.
if 'hint = "Buscar estados"' not in hub:
    anchor = '''        } else {\n            val info = TextView(this).apply {\n'''
    replacement = '''        } else {\n            val statusSearch = EditText(this).apply {\n                hint = "Buscar estados"\n                setSingleLine(true)\n                textSize = 15f\n                setTextColor(TEXT)\n                setHintTextColor(MUTED)\n                background = rounded(Color.rgb(44, 35, 46), 18)\n                setPadding(dp(14), dp(11), dp(14), dp(11))\n            }\n            root.addView(statusSearch, LinearLayout.LayoutParams(\n                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT\n            ).apply { setMargins(0, dp(8), 0, dp(6)) })\n            val info = TextView(this).apply {\n'''
    if anchor not in hub:
        raise SystemExit('status granted branch anchor missing')
    hub = hub.replace(anchor, replacement, 1)

# Wire live filtering and pass the current query into every refresh.
load_call = '            loadStatuses(stored, info, recycler)\n'
if 'statusSearch.doAfterTextChanged' not in hub:
    replacement = '''            statusSearch.doAfterTextChanged { editable ->\n                loadStatuses(stored, info, recycler, editable?.toString().orEmpty())\n            }\n            loadStatuses(stored, info, recycler, statusSearch.text.toString())\n'''
    if load_call not in hub:
        raise SystemExit('loadStatuses call anchor missing')
    hub = hub.replace(load_call, replacement, 1)

# The historical .take(180) cap can hide valid statuses. RecyclerView already
# virtualizes rows, so keep every discovered status and filter in memory.
hub = hub.replace('                ?.take(180)\n', '', 1)

sig_old = '    private fun loadStatuses(tree: Uri, info: TextView, recycler: RecyclerView) {\n'
sig_new = '    private fun loadStatuses(tree: Uri, info: TextView, recycler: RecyclerView, query: String = "") {\n'
if sig_old in hub:
    hub = hub.replace(sig_old, sig_new, 1)
elif sig_new not in hub:
    raise SystemExit('loadStatuses signature missing')

filter_old = '''            val filtered = all.filter {\n                if (filterSnapshot == StatusFilter.IMAGES) it.mime.startsWith("image/") else it.mime.startsWith("video/")\n            }\n'''
filter_new = '''            val querySnapshot = query.trim()\n            val filtered = all.filter { item ->\n                val matchesType = if (filterSnapshot == StatusFilter.IMAGES) {\n                    item.mime.startsWith("image/")\n                } else {\n                    item.mime.startsWith("video/")\n                }\n                matchesType && (querySnapshot.isBlank() || item.name.contains(querySnapshot, ignoreCase = true))\n            }\n'''
if filter_old in hub:
    hub = hub.replace(filter_old, filter_new, 1)
elif 'item.name.contains(querySnapshot, ignoreCase = true)' not in hub:
    raise SystemExit('status filtering anchor missing')

# Make the result count explicit so the user can see that the list is filtered
# rather than silently truncated.
info_old = '                    info.text = "Imágenes · $images     Videos · $videos"\n'
info_new = '                    info.text = "Imágenes · $images     Videos · $videos     Mostrando · ${filtered.size}"\n'
if info_old in hub:
    hub = hub.replace(info_old, info_new, 1)

# The shell sends a plain song/artist with insave_query. MainActivity natively
# feeds HomeFragment through a navigation argument called "url", so bridge the
# extra before the existing ACTION_VIEW destination switch.
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
    'status uncapped': '?.take(180)' not in hub,
    'status name filter': 'item.name.contains(querySnapshot, ignoreCase = true)' in hub,
    'plain search bridge': 'intent.getStringExtra("insave_query")' in main and 'putString("url", query)' in main,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave v0.17.2 follow-up gate failed: ' + ', '.join(failed))

print('InSave v0.17.2 follow-up compatibility gate: PASS')
