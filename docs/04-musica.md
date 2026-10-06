# Música: brief y licencias

El archivo preliminar no tiene audio, y el render actual lleva una pista de audio en silencio. La música se agrega al proyecto en cuanto tengas la pista con licencia.

## Qué buscar

| Aspecto | Indicación |
|---|---|
| Carácter | Cálido, sereno, residencial y ligeramente optimista. "Tarde tranquila en la terraza", no "fiesta en la playa" |
| Instrumentación | Guitarra acústica o nylon, piano suave, percusión ligera (shaker, rim). Toques de bossa o *lo-fi* acústico |
| Tempo | 80–100 BPM |
| Voz | **Ninguna** (instrumental), para no competir con los textos |
| Estructura ideal | Entrada suave (0–3 s) → ritmo constante (3–27 s) → pequeño impulso en la playa (27 s) → resolución en el cierre (30–35 s) |
| Mezcla | El render la normaliza a −14 LUFS, con entrada de 0.4 s y salida de 2.5 s |

**Búsquedas sugeridas:** `acoustic warm`, `bossa chill`, `sunset acoustic`, `calm guitar`, `relaxing travel`, `tropical acoustic`.

## Dónde conseguirla (con licencia para anuncios)

1. **Meta Sound Collection (recomendada, gratis).** Es la biblioteca libre de regalías de Meta y se puede usar en publicaciones y anuncios **dentro de Facebook e Instagram** (no sirve para YouTube ni para tu web). Se descarga desde Meta Business Suite (Todas las herramientas → *Sound Collection*). Creator Studio ya no existe.
2. **Bibliotecas de pago** (Artlist, Epidemic Sound, Musicbed, Soundstripe). Verifica que **tu plan cubra anuncios pagados**: en general, los planes personales o "creator" no los cubren.
3. **No usar** las canciones "en tendencia" de la biblioteca de Reels: son para uso personal, no para anuncios de empresa.

## Decisión: Meta Sound Collection

**Paso a paso para elegir la pista:**
1. Entra a **Meta Business Suite → Todas las herramientas → Sound Collection** con la cuenta de la página.
2. Filtra por **Música** y busca con los términos de arriba (por ejemplo, `acoustic` o `bossa`). Si hay filtros de género y estado de ánimo, usa *Acoustic / Latin / Ambient* y *Calm / Happy*.
3. Escucha los primeros 5 segundos de cada opción: deben entrar suaves y sin voz.
4. Descarga 2 o 3 candidatas en MP3 y **adjúntalas en este chat**. Las mezclo en el video, elijo con qué sección arranca cada una para que el cambio a la playa caiga en el compás y te mando las versiones finales para que escojas.

**Opción rápida (sin re-render):** al crear el anuncio en Ads Manager, en la sección de creativo, marca **Agregar música** y elige una pista de Sound Collection. Funciona, pero la mezcla y el punto de inicio no se pueden controlar.

## Cómo agregarla al proyecto

1. Guarda el archivo (WAV o MP3 de buena calidad) en `media/music/`, por ejemplo `media/music/pista.wav`.
2. En `project/condo_lua_reel.json`, cambia `"music": { "file": null, ...}` por `"file": "media/music/pista.wav"`. Con `offset` puedes empezar la canción en otro punto.
3. Vuelve a renderizar: `python3 tools/render_reel.py`.

**Alternativa:** sube el video sin música y elige una pista en Ads Manager (*Agregar música*). Es más rápido, pero la pista puede variar según la ubicación y no controlas la mezcla. Recomiendo integrarla en el video.

Guarda el comprobante de la licencia (captura o PDF) junto con el proyecto.
