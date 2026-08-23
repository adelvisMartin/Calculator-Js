from pathlib import Path
import runpy

hub_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
hub = hub_path.read_text()

# Normalize the final automatic-status RecyclerView by position. This avoids
# depending on variable names that changed across recovery patches.
recycler_hint = 'overScrollMode = View.OVER_SCROLL_NEVER'
pos = hub.find(recycler_hint)
if pos >= 0:
    hub = hub[:pos] + 'overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS' + hub[pos + len(recycler_hint):]

    nested_old = 'isNestedScrollingEnabled = false'
    nested_pos = hub.find(nested_old, pos, pos + 800)
    if nested_pos >= 0:
        hub = hub[:nested_pos] + 'isNestedScrollingEnabled = true' + hub[nested_pos + len(nested_old):]

    size_old = 'LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT'
    size_pos = hub.find(size_old, pos, pos + 1600)
    if size_pos >= 0:
        hub = hub[:size_pos] + 'LinearLayout.LayoutParams.MATCH_PARENT, dp(540)' + hub[size_pos + len(size_old):]

# The runtime patch uses this harmless marker only to delimit the generated
# automatic-status block. Put it directly before the normalized RecyclerView.
marker = 'val automaticGranted = automaticStatusAccessGranted()'
if marker not in hub:
    normalized_hint = 'overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS'
    marker_pos = hub.find(normalized_hint)
    if marker_pos >= 0:
        line_start = hub.rfind('\n', 0, marker_pos) + 1
        hub = hub[:line_start] + '            // val automaticGranted = automaticStatusAccessGranted()\n' + hub[line_start:]

hub_path.write_text(hub)

runtime = Path(__file__).with_name('apply_v0172_runtime.py')
if not runtime.exists():
    raise SystemExit('apply_v0172_runtime.py missing')
runpy.run_path(str(runtime), run_name='__main__')
