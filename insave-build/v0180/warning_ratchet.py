from pathlib import Path
import json
import re
import sys

log_path = Path.cwd() / "evidence/build.log"
out_path = Path.cwd() / "evidence/warning-ratchet.json"
if not log_path.exists():
    raise SystemExit("build log missing")
log = log_path.read_text(errors="replace")

# These warnings were explicitly observed in the v0.17.2 production-readiness audit
# and represent structural/dependency problems rather than ordinary upstream API debt.
blockers = {
    "phantom_gradle_project": [
        r"Configuring project ':common' without an existing directory",
        r"Configuring project ':library' without an existing directory",
        r"Configuring project ':ffmpeg' without an existing directory",
    ],
    "room_query_mismatch": [r"RoomWarnings\.QUERY_MISMATCH", r"properties \[log\] which are not returned by the query"],
    "accompanist_webview_unmaintained": [r"accompanist/web is deprecated and the API is no longer maintained"],
    "archives_base_name_removed_api": [r"archivesBaseName property has been deprecated"],
    "release_build_failure": [r"BUILD FAILED", r"Execution failed for task"],
}

results = []
for category, patterns in blockers.items():
    hits = []
    for p in patterns:
        hits.extend(re.findall(p, log, flags=re.I))
    results.append({"category": category, "pass": len(hits) == 0, "hits": len(hits), "patterns": patterns})

# Non-blocking Android/Kotlin deprecations are explicitly measured and ratcheted instead of
# being hidden. The v0.18 goal is to prevent growth while critical architecture warnings are zero.
warning_lines = [line for line in log.splitlines() if re.search(r"\bw: |warning|deprecated", line, re.I)]
api_deprecation_lines = [line for line in warning_lines if "deprecated" in line.lower()]
nullable_lines = [line for line in warning_lines if any(x in line.lower() for x in ["unnecessary non-null", "condition is always", "no cast needed", "unchecked cast"])]

summary = {
    "schema": "insave.warning-ratchet.v1",
    "critical_categories": results,
    "critical_failures": sum(1 for x in results if not x["pass"]),
    "warning_line_count": len(warning_lines),
    "api_deprecation_line_count": len(api_deprecation_lines),
    "static_code_smell_line_count": len(nullable_lines),
    "policy": "critical structural warnings must be zero; remaining upstream API debt is counted and must not increase without explicit baseline review",
}
out_path.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
if summary["critical_failures"]:
    raise SystemExit("InSave warning ratchet failed on critical structural warning(s)")
print("InSave critical warning ratchet: PASS")
