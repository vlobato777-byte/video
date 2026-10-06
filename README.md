# Condo Lua: reel de invierno 2027 (Facebook / Instagram)

Anuncio vertical de 35 s (1080 × 1920) para atraer a residentes de Canadá y Estados Unidos que buscan una estancia de invierno de 3 a 4 meses en Bucerías, Nayarit (enero–abril de 2027).

## Entregables

| Archivo | Qué es |
|---|---|
| `exports/CondoLua_Winter2027_35s_A_apertura-alberca.mp4` | **Versión principal**: abre con la alberca |
| `exports/CondoLua_Winter2027_35s_B_apertura-terraza.mp4` | **Versión B**: abre con la terraza de día. Lo demás es idéntico, para la prueba A/B |
| `exports/storyboard.png` | Hoja de contactos: un cuadro por toma, con su texto |
| `exports/*_preview_guias.mp4` | Vista previa con las zonas de la interfaz de Reels marcadas en rojo |
| `exports/revision/` | Copias ligeras para revisar en el teléfono. **No usar para la pauta** |
| `exports/overlays/` | Textos como PNG transparentes + `.srt`, por si se quiere rearmar en CapCut o Canva |
| `project/condo_lua_reel.json` | **Proyecto editable**: tomas, tiempos, encuadres, color, textos, estilos y música |

## Documentos

1. [Análisis y estrategia de pauta](docs/01-analisis-y-estrategia.md)
2. [Guion y storyboard](docs/02-guion.md)
3. [Copy del anuncio y mensajes](docs/03-copy-anuncio.md) (EN / FR)
4. [Música y licencias](docs/04-musica.md)
5. [Pendientes: material y confirmaciones](docs/05-pendientes.md)
6. [Serie de reels: propuesta](docs/06-serie-de-reels.md)

## Estado

**Lista para pautar en cuanto lleve música** de Meta Sound Collection (ver [docs/04-musica.md](docs/04-musica.md)). Ocho tomas usan cuadros extraídos del preliminar de WhatsApp (`media/source/borrador_whatsapp/`). Se ven bien, pero al agregar cada foto original en la ruta `source` de su toma, el render la usa automáticamente y gana nitidez.

## Cómo renderizar

Requisitos: Python 3.9+, Pillow, numpy y ffmpeg (con `zscale`, para los clips HDR de iPhone). Para fotos HEIC: `pip install pillow-heif`.

```bash
python3 tools/render_reel.py --check                      # valida la línea de tiempo y la zona segura
python3 tools/render_reel.py                              # versiones A y B en calidad final
python3 tools/render_reel.py --version A --preview --guides
python3 tools/render_reel.py --storyboard
python3 tools/render_reel.py --overlays
```

### Editar el proyecto

Cada toma en `shots` define:
- `source`: el archivo original (foto o video).
- `draft`: el respaldo provisional.
- `start` / `end`: posición en la línea de tiempo.
- `from` / `to`: encuadre inicial y final (`cx`, `cy` = centro de 0 a 1; `zoom` ≥ 1). Así se crea el movimiento suave.
- `transition_in`: `cut` o `dissolve`.
- `grade`: `exposure`, `temperature`, `tint`, `contrast`, `saturation`, `shadows`, `highlights`.
- `shade`: oscurecimiento local detrás del texto.
- `only`: `"A"` o `"B"`, para las tomas exclusivas de una versión.

Los textos están en `captions`. Cada uno tiene inicio y fin, posición vertical `y` y líneas con su `style`, que se define en `styles`. El render avisa si algún texto sale de la zona segura de Reels: 14 % superior, 35 % inferior y 6 % a los lados.

## Tipografías

*Cormorant Garamond* (titulares) e *Inter* (información), ambas con licencia SIL Open Font License (ver `assets/fonts/`).
