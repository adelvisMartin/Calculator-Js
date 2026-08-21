from pathlib import Path

p = Path('upstream/app/src/main/java/com/deniscerri/ytdl/insave/InSaveHubActivity.kt')
s = p.read_text()

# Password-mask the optional API key field.
if 'import android.text.InputType\n' not in s:
    anchor = 'import android.provider.MediaStore\n'
    if anchor not in s:
        raise SystemExit('MediaStore import anchor missing')
    s = s.replace(anchor, anchor + 'import android.text.InputType\n', 1)

advanced_anchor = '''        root.addView(card().apply {
            addView(sectionTitle("Avanzado"))
'''

provider_card = '''        root.addView(card().apply {
            addView(sectionTitle("Fallback de emergencia"))
            addView(body("Opcional. InSave funciona con sus motores locales sin esto. Configura únicamente una instancia Cobalt propia por HTTPS; nunca se usa una instancia pública por defecto."))

            val endpointInput = EditText(this@InSaveHubActivity).apply {
                hint = "https://tu-cobalt.example.com/"
                setHintTextColor(MUTED)
                setTextColor(TEXT)
                textSize = 13.5f
                setText(prefs.getString(InSaveCobaltResolver.PREF_ENDPOINT, "").orEmpty())
                backgroundTintList = ColorStateList.valueOf(ACCENT)
            }
            addView(endpointInput)

            val apiKeyInput = EditText(this@InSaveHubActivity).apply {
                hint = "API key opcional"
                setHintTextColor(MUTED)
                setTextColor(TEXT)
                textSize = 13.5f
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
                setText(prefs.getString(InSaveCobaltResolver.PREF_API_KEY, "").orEmpty())
                backgroundTintList = ColorStateList.valueOf(ACCENT)
            }
            addView(apiKeyInput)

            addView(horizontalButtons(
                smallButton("Guardar") {
                    val rawEndpoint = endpointInput.text.toString().trim().trimEnd('/')
                    val parsed = runCatching { Uri.parse(rawEndpoint) }.getOrNull()
                    val localHost = parsed?.host in setOf("127.0.0.1", "localhost", "10.0.2.2")
                    if (rawEndpoint.isNotBlank() && parsed?.scheme?.lowercase() != "https" && !localHost) {
                        toast("El fallback remoto debe usar HTTPS.")
                        return@smallButton
                    }
                    prefs.edit().apply {
                        if (rawEndpoint.isBlank()) remove(InSaveCobaltResolver.PREF_ENDPOINT)
                        else putString(InSaveCobaltResolver.PREF_ENDPOINT, rawEndpoint)
                        val key = apiKeyInput.text.toString().trim()
                        if (key.isBlank()) remove(InSaveCobaltResolver.PREF_API_KEY)
                        else putString(InSaveCobaltResolver.PREF_API_KEY, key)
                    }.apply()
                    toast(if (rawEndpoint.isBlank()) "Fallback remoto desactivado." else "Endpoint Cobalt propio guardado.")
                },
                smallButton("Probar") {
                    lifecycleScope.launch(Dispatchers.IO) {
                        val ok = InSaveCobaltResolver(this@InSaveHubActivity).health()
                        withContext(Dispatchers.Main) {
                            toast(if (ok) "Endpoint Cobalt disponible." else "Endpoint no disponible o no configurado.")
                        }
                    }
                }
            ))
            addView(secondaryButton("Desactivar fallback") {
                prefs.edit()
                    .remove(InSaveCobaltResolver.PREF_ENDPOINT)
                    .remove(InSaveCobaltResolver.PREF_API_KEY)
                    .apply()
                endpointInput.setText("")
                apiKeyInput.setText("")
                toast("InSave vuelve a usar únicamente motores locales.")
            })
        })
'''

if 'sectionTitle("Fallback de emergencia")' not in s:
    if advanced_anchor not in s:
        raise SystemExit('Settings advanced card anchor missing')
    s = s.replace(advanced_anchor, provider_card + advanced_anchor, 1)

p.write_text(s)

checks = {
    'endpoint UI': 'InSaveCobaltResolver.PREF_ENDPOINT' in s,
    'key UI': 'InSaveCobaltResolver.PREF_API_KEY' in s,
    'https guard': 'fallback remoto debe usar HTTPS' in s,
    'health test': 'InSaveCobaltResolver(this@InSaveHubActivity).health()' in s,
    'disable route': 'InSave vuelve a usar únicamente motores locales.' in s,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('InSave provider settings contract failed: ' + ', '.join(failed))
print('InSave provider settings contract: PASS')
