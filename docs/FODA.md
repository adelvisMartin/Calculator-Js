# InSave — FODA profundo y matriz estratégica

## Contexto

Este FODA evalúa InSave como producto Android de descarga/gestión multimedia y guardado de Estados, específicamente en su etapa Recovery Heavy. Distingue capacidades técnicas reales de preparación comercial/producción.

## Fortalezas

### F1. Resiliencia de extracción multi-proveedor

La cadena A/NewPipe -> B/yt-dlp local -> C/Cobalt opcional evita que una sola tecnología sea un punto único de fallo. La generación dinámica ligada al video y el fallback local son ventajas importantes frente a arquitecturas que dependen por completo de una API externa.

### F2. Runtime local completo

Python, yt-dlp, QuickJS, FFmpeg/FFprobe y aria2c permiten mantener capacidades de descarga/conversión sin trasladar por defecto URLs o historial del usuario a un backend propio. Esto favorece privacidad, operación offline parcial y autonomía técnica.

### F3. Modelo batch independiente

Cada elemento de playlist/lista puede convertirse en un trabajo independiente. Esto limita el radio de fallo y permite retry/cancelación por elemento.

### F4. Recuperación deliberada de UX útil

La estrategia Recovery no pretende reemplazar todo por una plantilla nueva: conserva el flujo simple de Inicio, Estados, Descargas, Seguidores y Ajustes y recupera comportamientos históricos como Estados automáticos y búsqueda de canciones.

### F5. Estados WhatsApp + Business como diferenciador

InSave integra una utilidad local que normalmente aparece como una app separada. La combinación de descarga multimedia + Estados puede reducir el cambio de contexto para el usuario.

### F6. Cultura de gate funcional

Existe una regla explícita de que compilar no equivale a funcionar. Los gates P0 persiguen conversiones reales, múltiples MP3, descubrimiento de Estados y navegación Android.

### F7. Capacidad de recuperación/rollback conceptual

El uso de una fuente upstream fijada y una línea LKG facilita reconstruir una base conocida mientras se diagnostican regresiones.

## Debilidades

### D1. Fuente canónica basada en parches textuales

Es la mayor debilidad estructural. La aplicación InSave no es todavía un árbol fuente plenamente propio: se recompone encima de un proyecto externo mediante scripts. Eso dificulta mantenimiento, revisión, merges, onboarding y escalabilidad.

### D2. APK Universal muy pesada

El runtime completo y cuatro ABI convierten el Universal en un artefacto grande. Es válido como Recovery/QA, pero penaliza distribución, instalación y actualizaciones si se usa como entrega normal.

### D3. Firma release no profesional

La configuración upstream asigna el release a una signing config de debug. Impide considerar el binario como release de producción confiable.

### D4. Permiso de almacenamiento amplio

La experiencia automática de Estados es cómoda, pero el acceso amplio a almacenamiento aumenta superficie de privacidad y complica distribución por Play.

### D5. Deuda Gradle/Android

Existen APIs y configuraciones deprecadas, directorios de proyecto faltantes advertidos por Gradle y warnings que pueden convertirse en fallos con versiones futuras.

### D6. Dependencias heterogéneas

Hay diferencias de versión entre componentes youtubedl-android/FFmpeg y librerías antiguas/deprecadas. Falta gobernanza formal de SBOM, vulnerabilidades y licencias.

### D7. CI demasiado acoplado a grep/texto

Varios falsos FAIL posteriores a compilaciones correctas provinieron de verificaciones de texto/nombre de archivo. Esto reduce confianza en el pipeline.

### D8. Documentación histórica inconsistente

Hasta esta auditoría el README de la rama seguía describiendo una calculadora JavaScript. Es una señal de deuda de gobernanza y dificultaba que un tercero entendiera el proyecto.

### D9. Matriz física insuficiente

La intención OEM/MIUI es correcta, pero todavía hace falta consolidar una matriz repetible de teléfonos reales y versiones Android antes de declarar Stable.

## Oportunidades

### O1. Convertir Recovery en un producto Android propio y modular

Materializar los parches en un repositorio InSave limpio permitiría módulos por feature/provider/runtime, code ownership y actualizaciones upstream controladas.

### O2. AAB + delivery por ABI

Mantener el Universal como artefacto QA y usar App Bundle/splits en producción reduciría drásticamente la carga para cada usuario sin eliminar el runtime necesario.

### O3. Producto local-first diferenciado

Una propuesta simple —buscar/pegar, audio/video, batch, Estados, biblioteca local— puede ser más clara que exponer opciones técnicas de yt-dlp.

### O4. Observabilidad privada y diagnóstico exportable

Un paquete de diagnóstico redactado con versiones de proveedor/runtime, error tipado y estado de almacenamiento puede reducir muchísimo el tiempo de soporte sin enviar datos sensibles automáticamente.

### O5. Automatización de compatibilidad con proveedores

Los cambios frecuentes de YouTube justifican contract tests programados contra videos públicos configurables y health checks por proveedor. Eso puede detectar roturas antes de que lleguen al usuario.

### O6. Flavors de distribución

Separar Recovery Sideload, Production Sideload y Play permitiría adaptar permisos, packaging y actualizaciones a cada canal sin deformar la UX principal.

### O7. Reproductor/biblioteca offline más fuerte

Como el archivo ya está local, InSave puede aumentar valor con cola, metadatos, búsqueda local, favoritos y reproducción consistente sin depender de la plataforma de origen.

### O8. Seguridad de supply chain como ventaja de confianza

Firma profesional, SBOM, checksums, runtime firmado y changelog verificable pueden diferenciar una utilidad sideload legítima de APKs opacas de procedencia dudosa.

## Amenazas

### A1. Cambios continuos de YouTube

SABR, firmas, clientes, PO tokens y políticas anti-bot pueden romper cualquier extractor sin aviso. Es la amenaza técnica externa principal.

### A2. Cambios en almacenamiento WhatsApp/Android

WhatsApp puede mover rutas o Android restringir más el acceso a `Android/media`, deteriorando el descubrimiento automático.

### A3. Políticas Google Play

El permiso All files access está restringido. Un diseño técnicamente funcional puede ser rechazado si no cumple la política del canal.

### A4. Riesgo legal/ToS/copyright

La descarga de contenido puede tener limitaciones contractuales o legales según fuente, contenido y jurisdicción. El producto debe evitar promesas de elusión de DRM/autenticación.

### A5. Upstream abandonado o incompatible

Si la base YTDLnis cambia profundamente o queda sin mantenimiento, una arquitectura basada en parches puede quedar bloqueada.

### A6. Dependencias nativas vulnerables

Un FFmpeg/Python/QuickJS/aria2c desactualizado amplía la exposición potencial. El gran runtime exige una política de actualizaciones y CVE más rigurosa.

### A7. Compromiso de firma/supply chain

Una clave debug o una actualización de runtime sin integridad suficiente puede permitir suplantación o código manipulado.

### A8. Fricción de tamaño

Un Universal de cientos de MB puede generar abandono, falta de espacio, tiempos de transferencia altos o mayor sospecha del usuario.

### A9. Competidores maduros

Apps consolidadas tienen UX, marca, distribución y soporte establecidos. InSave no debe competir solo por “descargar”, sino por simplicidad, local-first, resiliencia y transparencia.

## Matriz estratégica

### Estrategias FO — usar fortalezas para capturar oportunidades

**FO1.** Convertir la cadena multi-proveedor en una interfaz pública interna estable y modular. Así la resiliencia actual se transforma en escalabilidad real.

**FO2.** Mantener el Universal Heavy como artefacto de recuperación y aprovechar AAB/splits para distribución optimizada.

**FO3.** Usar la biblioteca local + Estados + batch como propuesta de producto coherente, manteniendo configuración técnica fuera del flujo principal.

**FO4.** Transformar los gates reales Android en un sistema preventivo de compatibilidad por proveedor.

### Estrategias DO — usar oportunidades para corregir debilidades

**DO1.** Migrar de scripts de sustitución a un fork/repositorio InSave propio con módulos y pruebas de caracterización.

**DO2.** Crear flavors de almacenamiento/distribución para resolver la tensión entre Estados automáticos y política Play.

**DO3.** Introducir version catalog, Dependabot/Renovate, SBOM y escáner de dependencias para controlar la heterogeneidad actual.

**DO4.** Sustituir gates grep por tests de interfaz pública, tests instrumentados y metadatos de artefactos.

### Estrategias FA — usar fortalezas para reducir amenazas

**FA1.** Ante cambios YouTube, mantener proveedores desacoplados, token por video, fixtures públicos reemplazables y circuit breaker.

**FA2.** Ante cambios WhatsApp/Android, encapsular descubrimiento detrás de `StatusDataSource`, permitiendo sustituir direct path por SAF/MediaStore sin reescribir UI.

**FA3.** Ante dependencias externas, conservar LKG verificable y rollback de runtime.

**FA4.** Ante competencia, priorizar experiencia rápida, sin login para contenido público y con biblioteca offline antes que acumular opciones técnicas visibles.

### Estrategias DA — minimizar debilidades y evitar amenazas

**DA1.** No publicar en producción una APK firmada con debug ni con un permiso de alto riesgo sin revisión del canal.

**DA2.** No continuar aumentando indefinidamente el volumen de parches Recovery; establecer fecha/milestone de migración a fuente propia.

**DA3.** No ejecutar auto-updates de runtime sin hash/firma y rollback.

**DA4.** Reducir deuda de Gradle/deprecaciones antes de que una actualización obligatoria de toolchain convierta warnings en errores.

## Prioridad estratégica recomendada

1. **Confiabilidad del candidato v0.17.2 y QA físico.**
2. **Firma/seguridad/distribución.**
3. **Migración a código fuente InSave propio.**
4. **Modularización y provider contracts.**
5. **Supply-chain + SBOM + dependency governance.**
6. **AAB/flavors y reducción del costo de distribución.**
7. **Performance, accesibilidad y refinamiento visual.**
8. **Nuevas features.**

La prioridad correcta es robustecer antes de expandir: añadir más plataformas mientras la base siga siendo patch-driven aumenta exponencialmente el costo de mantenimiento.
