from pathlib import Path
import hashlib
import json
import re
import sys
import uuid

workspace = Path.cwd()
upstream = workspace / "upstream"
evidence = workspace / "evidence"
evidence.mkdir(parents=True, exist_ok=True)
report = evidence / "gradle-runtime-dependencies.txt"
if not report.exists():
    raise SystemExit("Gradle dependency report missing: evidence/gradle-runtime-dependencies.txt")

text = report.read_text(errors="replace")
components = {}

# Gradle tree lines generally contain group:name:version, possibly -> selectedVersion.
coord = re.compile(r'([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+):([^\s()]+)(?:\s+->\s+([^\s()]+))?')
for match in coord.finditer(text):
    group, name, requested, selected = match.groups()
    version = (selected or requested).rstrip(',')
    if version in {"(*)", "FAILED"} or version.startswith("project"):
        continue
    key = (group, name, version)
    components[key] = {
        "type": "library",
        "group": group,
        "name": name,
        "version": version,
        "bom-ref": f"pkg:maven/{group}/{name}@{version}",
        "purl": f"pkg:maven/{group}/{name}@{version}",
    }

# Explicit native/runtime assets that do not appear as ordinary Maven coordinates.
ytdlp = upstream / "app/src/main/res/raw/ytdlp"
ytdlp_sha = hashlib.sha256(ytdlp.read_bytes()).hexdigest() if ytdlp.exists() else None
extra = [
    {
        "type": "application",
        "name": "yt-dlp",
        "version": "2026.08.19",
        "bom-ref": "pkg:generic/yt-dlp@2026.08.19",
        "purl": "pkg:generic/yt-dlp@2026.08.19",
        "hashes": ([{"alg": "SHA-256", "content": ytdlp_sha}] if ytdlp_sha else []),
        "properties": [{"name": "insave.role", "value": "embedded extractor runtime"}],
    },
    {
        "type": "library",
        "name": "FFmpeg Android runtime",
        "version": "0.18.1-wrapper",
        "bom-ref": "pkg:generic/insave-ffmpeg-runtime@0.18.1-wrapper",
        "purl": "pkg:generic/insave-ffmpeg-runtime@0.18.1-wrapper",
        "properties": [{"name": "insave.role", "value": "embedded native media processing"}],
    },
    {
        "type": "library",
        "name": "Python Android runtime",
        "version": "embedded",
        "bom-ref": "pkg:generic/insave-python-runtime@embedded",
        "purl": "pkg:generic/insave-python-runtime@embedded",
        "properties": [{"name": "insave.role", "value": "yt-dlp execution runtime"}],
    },
    {
        "type": "library",
        "name": "aria2c Android runtime",
        "version": "0.18.1-wrapper",
        "bom-ref": "pkg:generic/insave-aria2c-runtime@0.18.1-wrapper",
        "purl": "pkg:generic/insave-aria2c-runtime@0.18.1-wrapper",
    },
    {
        "type": "library",
        "name": "QuickJS Android runtime",
        "version": "embedded",
        "bom-ref": "pkg:generic/insave-quickjs-runtime@embedded",
        "purl": "pkg:generic/insave-quickjs-runtime@embedded",
        "properties": [{"name": "insave.role", "value": "JavaScript extractor support"}],
    },
]

metadata_component = {
    "type": "application",
    "name": "InSave",
    "version": "0.18.0-Hardening-QA",
    "bom-ref": "pkg:apk/com.adelvis.insave.recovery@0.18.0-Hardening-QA",
    "properties": [
        {"name": "insave.upstream", "value": "deniscerri/ytdlnis@c6084ed4f110efd4ba0c3f82bb16723b6529c8f0"},
        {"name": "insave.distribution", "value": "Recovery/QA Heavy"},
    ],
}

all_components = sorted(components.values(), key=lambda c: (c.get("group", ""), c["name"], c["version"])) + extra
bom = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.6",
    "serialNumber": f"urn:uuid:{uuid.uuid4()}",
    "version": 1,
    "metadata": {"component": metadata_component},
    "components": all_components,
}

out = evidence / "InSave-v0.18.0-SBOM.cdx.json"
out.write_text(json.dumps(bom, indent=2, ensure_ascii=False) + "\n")
summary = {
    "maven_components": len(components),
    "embedded_runtime_components": len(extra),
    "total_components": len(all_components),
    "yt_dlp_sha256": ytdlp_sha,
    "output": str(out),
}
(evidence / "sbom-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
if ytdlp_sha != "1fa6733c37ea6fb51c99ad8fe785e7b7e5f3246c9b980230329d4fb72ed8d4d6":
    raise SystemExit("embedded yt-dlp digest does not match the pinned Recovery contract")
if len(components) < 20:
    raise SystemExit(f"resolved dependency graph unexpectedly small: {len(components)} Maven components")
print("InSave CycloneDX SBOM: PASS")
