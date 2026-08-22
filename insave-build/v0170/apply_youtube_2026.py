from pathlib import Path
import hashlib
import urllib.request

# InSave v0.17.1 P0 hardening for YouTube's 2026 PO-token enforcement.
# - Keep dynamic per-video BotGuard generation from v0.16.3.
# - Feed those Web-platform tokens to yt-dlp's currently recommended mweb client.
# - Pin a current immutable yt-dlp release into the Heavy APK so runtime QA does
#   not depend on whatever extractor binary was bundled by the older upstream snapshot.

YTDLP_VERSION = "2026.08.19"
YTDLP_SHA256 = "1fa6733c37ea6fb51c99ad8fe785e7b7e5f3246c9b980230329d4fb72ed8d4d6"
YTDLP_URL = f"https://github.com/yt-dlp/yt-dlp/releases/download/{YTDLP_VERSION}/yt-dlp"

root = Path("upstream/app/src/main/java/com/deniscerri/ytdl")
ytdlp_path = root / "util/extractors/ytdlp/YTDLPUtil.kt"
s = ytdlp_path.read_text()

replacements = {
    'poTokens.removeAll { it.startsWith("web.") }':
        'poTokens.removeAll { it.startsWith("web.") || it.startsWith("mweb.") }',
    'playerClients.add("web")':
        'playerClients.removeAll { it == "web" || it == "mweb" }\n                        playerClients.add("mweb")',
    'poTokens.add("web.player+${tokenResult.playerRequestPoToken}")':
        'poTokens.add("mweb.player+${tokenResult.playerRequestPoToken}")',
    'poTokens.add("web.gvs+$it")':
        'poTokens.add("mweb.gvs+$it")',
    'if (!(dynamicPoTokenApplied && value.playerClient == "web")) {':
        'if (!(dynamicPoTokenApplied && value.playerClient in setOf("web", "mweb"))) {',
    'if (dynamicPoTokenApplied && cl == "web") continue':
        'if (dynamicPoTokenApplied && cl in setOf("web", "mweb")) continue',
}

for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit(f"2026 YouTube hardening anchor missing: {old}")

# Make the intent explicit for future maintenance: web is SABR-only under current
# enforcement, while yt-dlp recommends mweb + GVS provider for ordinary formats.
s = s.replace(
    '// Remove any stale/manual Web tokens before installing the fresh set.',
    '// Remove stale Web/mWeb tokens, then bind the fresh per-video set to mweb.',
    1,
)
ytdlp_path.write_text(s)

# Pin the platform-independent zipimport yt-dlp executable into res/raw. It runs
# through the Heavy APK's bundled Python and is checksum-verified before replacement.
out = Path("upstream/app/src/main/res/raw/ytdlp")
out.parent.mkdir(parents=True, exist_ok=True)
existing_ok = out.exists() and hashlib.sha256(out.read_bytes()).hexdigest() == YTDLP_SHA256
if not existing_ok:
    req = urllib.request.Request(YTDLP_URL, headers={"User-Agent": "InSave-Recovery-Heavy-CI"})
    with urllib.request.urlopen(req, timeout=90) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != YTDLP_SHA256:
        raise SystemExit(
            f"yt-dlp {YTDLP_VERSION} checksum mismatch: expected={YTDLP_SHA256} actual={digest}"
        )
    out.write_bytes(payload)

final = ytdlp_path.read_text()
checks = {
    "mweb player client": 'playerClients.add("mweb")' in final,
    "mweb player token": 'mweb.player+' in final,
    "mweb gvs token": 'mweb.gvs+' in final,
    "per-video provider": 'getWebClientPoToken(videoId)' in final,
    "anonymous tokens": 'poTokens.isNotEmpty() && sharedPreferences.getBoolean("use_cookies"' not in final,
    "stale web/mweb filtered": 'value.playerClient in setOf("web", "mweb")' in final,
    "yt-dlp pinned": hashlib.sha256(out.read_bytes()).hexdigest() == YTDLP_SHA256,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("InSave 2026 YouTube hardening failed: " + ", ".join(failed))

print(f"InSave 2026 YouTube hardening: PASS (mweb + yt-dlp {YTDLP_VERSION})")
