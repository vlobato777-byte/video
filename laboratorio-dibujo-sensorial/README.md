# Laboratorio de dibujo sensorial: campaña (flyer, reel y carrusel)

Taller de dibujo, meditación y exploración del trazo personal. Imparten Carmen Elizondo y Almendra García en Concéntrica Artes Aplicadas.

El flyer define la identidad visual de la campaña. El reel usa la misma identidad y el carrusel también la usará.

## Estado

| Pieza | Estado |
|---|---|
| **Flyer 1080 × 1350** | **Listo en Canva y editable**, con WhatsApp 833 300 8857 |
| Flyer para estados e historias (1080 × 1920) | Pendiente: se adapta del flyer cuando esté aprobado |
| **Reel 30 s (1080 × 1920)** | **Listo para revisión.** Video, portada, copy y capas de texto. La mano dibuja cada trazo en una línea continua (sonido, corteza a ciegas, hilos, recuerdo) |
| Carrusel | Pendiente |

**Flyer en Canva:** diseño *“Flyer taller de dibujo sensorial”* (ID `DAHXYHwz8Oc`) → <https://www.canva.com/d/RT7uJwrJYnRplNE>

Para descargarlo: *Compartir → Descargar → PNG*, tamaño 1080 × 1350.

## Archivos

| Archivo | Qué es |
|---|---|
| `exports/flyer/flyer_canva_vista_previa.png` | Vista previa reducida del flyer guardado en Canva (400 × 500) |
| `exports/flyer/flyer_maqueta.png` | Maqueta local con las tipografías exactas. Muestra dónde van la foto y el logo; la versión final es la de Canva |
| `exports/flyer/canva/papel_1080x1350.png` | Fondo de papel artístico #F4EBDD con textura muy sutil (es el fondo del flyer en Canva) |
| `exports/flyer/canva/trazos_1080x1350.png` | Trazos de carbón sobre transparencia, colocados solo donde no hay texto |
| `exports/flyer/canva/nota_imagen_ilustrativa.png` | Etiqueta “Imagen ilustrativa” para la foto generada |
| `exports/reel/LabDibujoSensorial_Reel_30s.mp4` | **Reel final** 1080 × 1920, 30 fps, con música y sonido de carbón |
| `exports/reel/revision/` | Copia ligera del reel para revisarlo en el teléfono. **No usar para publicar** |
| `exports/reel/portada_1080x1920.png` | Portada del reel (y `portada_recorte_4x5.png`, como se ve en el perfil) |
| `exports/reel/storyboard.png` | Un cuadro por toma, con su texto |
| `exports/reel/textos/` | Textos del reel como PNG transparentes + `.srt`, y los textos y el logo del cierre, para rearmarlo en CapCut o Canva |
| `docs/reel.md` | Guion, copy de la publicación y decisiones del reel |
| `reel.json` | Tomas, tiempos, encuadres y textos del reel (editable) |
| `media/escenas/` | Escenas conceptuales del estudio usadas en el reel (generadas en Canva) |
| `media/mano/mano_carboncillo.png` | Mano con carboncillo recortada (imagen ilustrativa generada en Canva). Es la que dibuja en los planos de detalle del reel |
| `media/logo/concentrica.png` | Logo de Concéntrica con fondo transparente, tomado de la presentación de la clienta |
| `datos.json` | Datos del taller, paleta, tipografías y textos de la campaña |

## Cómo está construido el flyer

**Jerarquía:** 1. *RESPIRA. SIENTE. TRAZA.* · 2. *LABORATORIO DE DIBUJO SENSORIAL* · 3. Foto · 4. Pregunta e invitación · 5. Datos agrupados con el logo · 6. Banda terracota con la reserva por WhatsApp.

**Identidad:** crema #F4EBDD, carbón #272522, terracota #D85B35 y olivo #78834B (en *No necesitas experiencia previa* e *Imparten:*). Títulos en Barlow Condensed SemiBold y cuerpo en DM Sans. Los textos tienen 26 px como mínimo.

**Trazos de carbón** (`tools/trazos.py`):
- un gesto que pasa bajo el nombre del taller y se esconde detrás de la foto;
- un subrayado terracota bajo *TRAZA.*;
- tres ondas de grafito que separan los datos, como una respiración;
- puntos en grupos rítmicos, como un sonido escuchado.

Ninguno pasa por debajo del texto.

**Foto:** la clienta no ha enviado fotos reales del taller, así que la imagen se generó en Canva como **ilustración conceptual** y lleva la etiqueta *Imagen ilustrativa*. No se presenta como registro de una edición anterior. El papel es un pliego vertical grande sujeto a un tablero, como en la foto de la página 4 de la presentación de la clienta.

Cuando haya fotos reales: en Canva, selecciona la foto → *Reemplazar*, y borra la etiqueta *Imagen ilustrativa*.

**Logo:** es el de Concéntrica que viene en la presentación de la clienta, con sus proporciones originales.

## Datos usados y de dónde salen

Vienen de la presentación de Canva de la clienta (*Copia de DIBUJO EN ORIGAMI*, páginas 1 y 4):

- Jueves 15, 22 y 29 de octubre · 6:00 a 8:00 p. m.
- Concéntrica Artes Aplicadas, Ejército Mexicano 1902, Col. Loma del Gallo, Cd. Madero
- $1,600 · Incluye materiales · Cupo limitado

En las páginas 4 y 5 de esa presentación quedan textos ocultos de una edición anterior (*Marzo 24, 25 y 26*). No se usaron.

## Pendientes

1. **Confirmar la ciudad.** *Cd. Madero* se dedujo del C. P. 89460 de la presentación.
2. **Confirmar el costo.** ¿Los $1,600 cubren las tres sesiones? ¿Se puede pagar por sesión?
3. **Confirmar el formato del papel:** pliego vertical sobre tablero o pared, como en la foto.
4. **Fotos o videos reales** del taller o de Carmen y Almendra dibujando. Sustituyen a la ilustración en el flyer, el carrusel y el reel (ver `docs/reel.md`). Las fotos de referencia que mencionaste para el reel no llegaron a esta sesión: solo llegó el PDF del brief.
5. **Tipografías en Canva.** El conector de Canva no muestra los nombres de las fuentes. Al seleccionar un título debería decir *Barlow Condensed*, y en el cuerpo *DM Sans*. Si no, cámbialas con el menú de fuente.
6. En tu Canva quedó también el borrador previo *Flyer taller de dibujo sensorial* de 1080 × 1440 (ID `DAHXYChIPF0`). Ya no se usa y puedes borrarlo.

## Cómo regenerar los gráficos, la maqueta y el reel

Requisitos: Python 3.9+, Pillow, numpy y ffmpeg.

```bash
python3 tools/laboratorio.py flyer          # gráficos del flyer y maqueta
python3 tools/reel_laboratorio.py --stills  # portada, storyboard y textos del reel
python3 tools/reel_laboratorio.py           # reel final (~15 min)
```

Si cambias un dato en `datos.json`, cambia el mismo texto en Canva y vuelve a renderizar el reel. Si quieres ver la foto en la maqueta del flyer, ponla en `media/fotos/principal.jpg`.

Los trazos se generan con una semilla fija: siempre salen iguales. Si cambias los trazos, sube el PNG nuevo y reemplázalo en Canva.

## Tipografías

*Barlow Condensed* y *DM Sans*, ambas con licencia SIL Open Font License (ver `assets/fonts/`).
