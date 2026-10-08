# Reel 30 s: guion, copy y decisiones

Brief: `PROMPT_REEL_TALLER.pdf`. Formato 1080 × 1920 (9:16), 30 fps, 30 s.

## Guion final

| Tiempo | Imagen | Texto en pantalla |
|---|---|---|
| 0–1.7 s | Detalle: un trazo amplio de carbón entra al papel | ¿Cómo dibujarías un sonido? |
| 1.7–4 s | Plano medio: el mismo trazo termina justo en la mano que dibuja | (sigue) |
| 4–8 s | Pausa: ojos cerrados, manos sobre el papel | Respira. Escucha. |
| 8–10.5 s | La mano explora la textura de una corteza | Siente. |
| 10.5–13 s | Detalle: la textura se vuelve una trama nueva | Traza. |
| 13–15 s | Detalle del mismo dibujo: puntos en ritmo | Un sonido. |
| 15–17 s | Detalle: mancha suave y un arco olivo | Una sensación. |
| 17–19 s | Detalle: lazo terracota | Un recuerdo. |
| 19–21.6 s | Plano medio: un trazo más llega a la mano; se ven todas las capas | Capa a capa, descubre tu propio trazo. |
| 21.6–24 s | Plano amplio de la persona y el dibujo completo | No necesitas experiencia previa. |
| 24–30 s | Cierre en crema: trazo de carbón, subrayado terracota, datos y logo | RESPIRA. SIENTE. TRAZA. · Laboratorio de dibujo sensorial · fecha y sede · Reserva: WhatsApp |

**Continuidad:** es un solo dibujo. Cada capa se agrega encima de las anteriores y ninguna desaparece entre tomas. Los planos de detalle muestran ese mismo dibujo, en las mismas posiciones del papel.

**Sonido:** música instrumental original, generada por el script. Tiene un pulso suave y no requiere licencia. Se escucha el roce del carbón cada vez que aparece un trazo en pantalla y un toque por cada punto. La música baja un poco en esos momentos. No hay voz en off. Volumen normalizado a −14 LUFS.

**Textos:** las frases van en etiquetas crema con letra carbón, en Barlow Condensed SemiBold; *No necesitas experiencia previa* va en DM Sans. La puntuación lleva el acento terracota. Todos los textos están dentro de la zona segura de Reels (de 269 a 1248 px de alto). El nombre del taller va en mayúsculas, como en el flyer.

## Imágenes

No hay video ni fotos reales del taller. Las escenas del estudio son **ilustraciones conceptuales** generadas en Canva a partir de la imagen del flyer. Se usan como representación de la actividad y nunca como registro de un taller ya realizado.

- El papel es un **rollo vertical grande sobre un tablero**, como en la foto de la página 4 de la presentación de la clienta. Falta confirmar que en el taller se usará este formato.
- En las escenas el papel está en blanco. El dibujo de carbón se pinta encima con `tools/trazos.py`, en perspectiva y por detrás de manos y brazos, para que las capas se acumulen de verdad.
- **Cuando haya videos reales**, conviene reemplazar las tomas 02, 03, 04, 09 y 10 por planos reales: el cuerpo dibujando en grande, las manos, el papel. Los detalles del dibujo, los textos y el cierre se pueden conservar.

## Copy para la publicación

> ¿Cómo se dibuja un sonido? ¿Qué trazo puede nacer de una textura o de un recuerdo?
>
> En el Laboratorio de dibujo sensorial comenzarás con ejercicios de observación y respiración. Después, te guiaremos por experiencias de escucha, tacto, imaginación y memoria que llevarás al papel.
>
> Cada experiencia dejará una nueva capa. Al superponerlas, descubrirás un dibujo construido desde tu propia percepción.
>
> No necesitas experiencia previa.
>
> Respira. Siente. Traza.
>
> Imparten Carmen Elizondo y Almendra García.
>
> 📍 Concéntrica Artes Aplicadas · Ejército Mexicano 1902, Col. Loma del Gallo, Cd. Madero
> 📅 Jueves 15, 22 y 29 de octubre
> 🕕 6:00 a 8:00 p. m.
> 🎟️ $1,600 · Incluye materiales · Cupo limitado
>
> Reserva tu lugar por WhatsApp: [NÚMERO]
>
> #DibujoSensorial #LaboratorioDeDibujo #TrazoLibre #DibujoEnGrande #Concéntrica

## Portada

`exports/reel/portada_1080x1920.png`: el trazo amplio llega a la mano y el título va en una etiqueta crema dentro de la zona central. El título también queda visible en el recorte 4:5 del perfil (`portada_recorte_4x5.png`).

## Cómo editarlo

- **Textos y tiempos:** `reel.json`. Los datos del cierre salen de `datos.json`. Al llegar el número de WhatsApp, cámbialo en `datos.json` y vuelve a renderizar.
- **Para armarlo en CapCut o Canva:** en `exports/reel/textos/` hay un PNG transparente por cada texto, con sus tiempos en el nombre, un `.srt` y los textos y el logo del cierre.

```bash
python3 tools/reel_laboratorio.py --stills    # portada, storyboard y capas de texto (20 s)
python3 tools/reel_laboratorio.py --preview   # video a media resolución
python3 tools/reel_laboratorio.py             # video final y copia ligera de revisión (~8 min)
```
