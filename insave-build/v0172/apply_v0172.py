from pathlib import Path
import runpy

runtime = Path(__file__).with_name('apply_v0172_runtime.py')
if not runtime.exists():
    raise SystemExit('apply_v0172_runtime.py missing')
runpy.run_path(str(runtime), run_name='__main__')
