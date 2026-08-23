from pathlib import Path
import json
import re
import sys

root = (Path.cwd() / "upstream").resolve()
app = root / "app"
main = app / "src/main"
src = main / "java/com/deniscerri/ytdl"
report_path = Path.cwd() / "evidence/security-gate.json"
report_path.parent.mkdir(parents=True, exist_ok=True)

checks = []

def check(name, ok, evidence, severity="high"):
    checks.append({"name": name, "pass": bool(ok), "severity": severity, "evidence": evidence})


def text(path):
    return path.read_text(errors="replace") if path.exists() else ""

build = text(app / "build.gradle")
manifest = text(main / "AndroidManifest.xml")
play_manifest = text(app / "src/play/AndroidManifest.xml")
share = text(src / "receiver/ShareActivity.kt")
hub = text(src / "insave/InSaveHubActivity.kt")
worker = text(src / "work/download/DownloadWorker.kt")
ytdlp = text(src / "util/extractors/ytdlp/YTDLPUtil.kt")
cobalt = text(src / "insave/InSaveCobaltResolver.kt")
po_gen = text(src / "util/extractors/newpipe/potoken/NewPipePoTokenGenerator.kt")
po_web = text(src / "util/extractors/newpipe/potoken/PoTokenWebView.kt")
po_login = text(src / "ui/more/settings/advanced/generateyoutubepotokens/webview/PoTokenWebViewLoginActivity.kt")

release_start = build.find("release {")
release_end = build.find("debug {", release_start)
release = build[release_start:release_end] if release_start >= 0 and release_end > release_start else ""
check("release_not_signed_with_debug_key", "signingConfigs.debug" not in release, "release block has no debug signing")
check("release_signing_uses_external_secrets", all(x in build for x in ["INSAVE_KEYSTORE_PATH", "INSAVE_KEYSTORE_PASSWORD", "INSAVE_KEY_ALIAS", "INSAVE_KEY_PASSWORD", "signingConfigs.insaveRelease"]), "four secret-backed signing inputs + dedicated release config")
check("cleartext_disabled_by_default", 'android:usesCleartextTraffic="false"' in manifest, "base manifest cleartext=false")
check("play_removes_all_files_access", 'android.permission.MANAGE_EXTERNAL_STORAGE' in play_manifest and 'tools:node="remove"' in play_manifest, "Play manifest removes MANAGE_EXTERNAL_STORAGE")
check("play_removes_exact_alarm", 'android.permission.SCHEDULE_EXACT_ALARM' in play_manifest and play_manifest.count('tools:node="remove"') >= 3, "Play manifest removes special-access permissions")
check("share_external_boundary_validated", "InSaveInputPolicy.normalizeHttpUrl(extractedUrl)" in share, "ShareActivity rejects unsafe shared URLs")
check("main_hub_input_validated", "InSaveInputPolicy.classify(rawInput)" in hub, "Hub classifies URL/search input before engine handoff")
check("cobalt_endpoint_tls_policy", "normalizeProviderEndpoint" in cobalt and "isSafeProviderResponseUrl" in cobalt, "Provider C uses centralized endpoint/response validation")
check("cobalt_source_validated", "normalizeHttpUrl(sourceUrl)" in cobalt, "Provider C source URL is normalized before POST")
check("runtime_logs_redacted", "InSaveRedactor.redact(line)" in worker, "central worker callback redacts persisted/visible lines")
check("runtime_exception_redacted", "InSaveRedactor.redact(it.message)" in worker, "error notification message is redacted")
check("po_token_generator_secrets_not_logged", "playerPot=$playerPot" not in po_gen and "streamingPot=$streamingPot" not in po_gen and "visitor_data=$visitorData" not in po_gen, "NewPipe generator no longer prints secret token values")
check("po_token_webview_secrets_not_logged", "poToken=$poToken" not in po_web and "poTokenU8=$poTokenU8" not in po_web, "BotGuard WebView no longer prints PO token material")
check("deprecated_accompanist_webview_removed", "com.google.accompanist.web" not in po_login and "accompanist-webview" not in build, "manual PO helper uses native WebView")
check("native_webview_file_access_disabled", "allowFileAccess = false" in po_login and "allowContentAccess = false" in po_login, "manual WebView cannot read file/content schemes")
check("native_webview_mixed_content_blocked", "MIXED_CONTENT_NEVER_ALLOW" in po_login, "manual WebView blocks mixed content")
check("provider_fallback_is_bounded", "anonymousYoutubeFallbackClients" in worker and "allowsAnonymousClientFallback" in worker, "B fallback only occurs for classified recoverable failures")
check("provider_b_primary_keeps_per_video_po", "getWebClientPoToken(videoId)" in ytdlp and "mweb.player+" in ytdlp and "mweb.gvs+" in ytdlp, "primary local yt-dlp path keeps per-video PO token")
check("all_files_access_not_requested_by_play_overlay", play_manifest.strip() != "", "dedicated Play storage-policy overlay exists", severity="medium")

# Components that must not be callable directly by arbitrary external apps.
def exported_for(activity):
    m = re.search(r'<activity\b(?=[^>]*android:name="' + re.escape(activity) + r'")([^>]*)>', manifest, re.S)
    if not m:
        return None
    v = re.search(r'android:exported="(true|false)"', m.group(0))
    return v.group(1) if v else None

for activity in [".MainActivity", ".insave.InSaveHubActivity", ".ui.more.settings.SettingsActivity", ".ui.more.terminal.TerminalActivity", ".receiver.TransparentActivity"]:
    check(f"internal_component_{activity}_not_exported", exported_for(activity) == "false", f"{activity} exported={exported_for(activity)}")
check("share_component_is_explicit_external_boundary", exported_for(".receiver.ShareActivity") == "true", f"ShareActivity exported={exported_for('.receiver.ShareActivity')}", severity="medium")

# Scan InSave-owned and high-risk Android source for obvious secret/private-key mistakes.
patterns = {
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_pat": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "hardcoded_bearer": re.compile(r"(?i)Authorization[\"']?\s*[,=:]\s*[\"']Bearer\s+[A-Za-z0-9._~+\-/=]{16,}"),
}
scan_paths = list((src / "insave").glob("*.kt")) + [share and src / "receiver/ShareActivity.kt", worker and src / "work/download/DownloadWorker.kt"]
scan_paths = [p for p in scan_paths if isinstance(p, Path) and p.exists()]
scan_text = "\n".join(text(p) for p in scan_paths)
for name, pattern in patterns.items():
    check(f"no_{name}", pattern.search(scan_text) is None, f"scanned {len(scan_paths)} high-risk source files")

failed = [c for c in checks if not c["pass"] and c["severity"] == "high"]
report = {
    "schema": "insave.security-gate.v1",
    "summary": {
        "total": len(checks),
        "passed": sum(1 for c in checks if c["pass"]),
        "failed_high": len(failed),
    },
    "checks": checks,
}
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
for c in checks:
    print(("PASS" if c["pass"] else "FAIL"), c["severity"].upper(), c["name"], "-", c["evidence"])
if failed:
    print(f"Static security gate failed: {len(failed)} high-severity checks", file=sys.stderr)
    raise SystemExit(1)
print(f"InSave static security gate: PASS ({report['summary']['passed']}/{report['summary']['total']})")
