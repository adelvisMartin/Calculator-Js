from pathlib import Path
p = Path('upstream/app/src/main/java/com/deniscerri/ytdl/util/extractors/ytdlp/YTDLPUtil.kt')
s = p.read_text()
s = s.replace(
    'if (!value.useOnlyPoToken) {\n                        playerClients.add(value.playerClient)\n                    }',
    'if (!value.useOnlyPoToken && !(dynamicPoTokenApplied && value.playerClient in setOf("web", "mweb"))) {\n                        playerClients.add(value.playerClient)\n                    }',
    1,
)
s = s.replace(
    'if (!(dynamicPoTokenApplied && value.playerClient == "web")) {',
    'if (!(dynamicPoTokenApplied && value.playerClient in setOf("web", "mweb"))) {',
    1,
)
s = s.replace(
    'if (dynamicPoTokenApplied && cl == "web") continue',
    'if (dynamicPoTokenApplied && cl in setOf("web", "mweb")) continue',
    1,
)
p.write_text(s)
assert 'value.playerClient in setOf("web", "mweb")' in s
assert 'cl in setOf("web", "mweb")' in s
print('InSave dynamic-token precedence: PASS')
