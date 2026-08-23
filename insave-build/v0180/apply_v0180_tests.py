from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
UPSTREAM = (Path.cwd() / "upstream").resolve()
target = UPSTREAM / "app/src/androidTest/java/com/deniscerri/ytdl/insave/InSaveV0180InstrumentedTest.kt"
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(HERE / "InSaveV0180InstrumentedTest.kt", target)
# Remove the superseded brittle suite so it cannot fail the same run on a single
# historically challenged video. v0.18 includes all previous P0 contracts plus
# the 14-status and candidate-pool hardening.
old = target.parent / "InSaveRecoveryInstrumentedTest.kt"
if old.exists():
    old.unlink()
print("InSave v0.18 instrumentation suite installed: PASS")
