from pathlib import Path
import runpy

# Compatibility normalization for reconstructed v0.17 status UI. Some prior
# recovery patches inline the access check and therefore omit the exact local
# variable name expected by the v0.17.2 runtime patch. Insert a harmless marker
# immediately before the automatic-state RecyclerView so the runtime patch can
# operate on the final generated block rather than depending on an older source
# spelling.
hub_path = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
hub = hub_path.read_text()
marker = 'val automaticGranted = automaticStatusAccessGranted()'
if marker not in hub:
    recycler_hint = 'overScrollMode = View.OVER_SCROLL_NEVER'
    pos = hub.find(recycler_hint)
    if pos >= 0:
        line_start = hub.rfind('\n', 0, pos) + 1
        hub = hub[:line_start] + '            // val automaticGranted = automaticStatusAccessGranted()\n' + hub[line_start:]
        hub_path.write_text(hub)

runtime = Path(__file__).with_name('apply_v0172_runtime.py')
if not runtime.exists():
    raise SystemExit('apply_v0172_runtime.py missing')
runpy.run_path(str(runtime), run_name='__main__')
