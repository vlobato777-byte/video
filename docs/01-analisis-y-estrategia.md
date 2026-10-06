# Condo Lua: análisis del reel y estrategia de pauta

**Objetivo:** generar consultas que incluyan **fechas y duración de estancia** para enero–abril de 2027, sujeto a disponibilidad confirmada.
**Audiencia:** residentes de Canadá y Estados Unidos que buscan pasar el invierno en un lugar cálido (*snowbirds*), con estancias de 3 a 4 meses (mínimo 3, con opción a un 4.º mes).

---

## 1. Material recibido y cómo se usa

| Material | Qué es | Uso en el reel |
|---|---|---|
| `WhatsApp Video 2026-10-05 20.30.48` (35 s) | Preliminar más reciente, **sin textos** y con audio mudo. 14 fotos con zoom y 13 disolvencias de ~0.3 s | Referencia de orden. Se extrajeron cuadros como respaldo provisional |
| `WhatsApp Video 2026-10-05 17.27.34` (30 s) | Versión anterior **con textos** | Referencia de copy. Se tomó un cuadro de la alberca al atardecer |
| `IMG_3349.mov` | Atardecer en la playa. Vertical, HDR, grabado el **2 de enero de 2025** | **Playa (27–30 s)** |
| `IMG_3348.mov` | La misma playa, en horizontal | Descartado: al recortarlo a vertical pierde nitidez |
| `IMG_6032.MOV` | Mesa de la terraza de día, con cortinas en movimiento | **Apertura de la versión B** |
| `IMG_5993`, `IMG_5857`, `IMG_5896`, `IMG_5864` (HEIC) | Comedor → sala → terraza, sala → cocina, segunda recámara y cocina vertical, fotos originales | **Comedor → sala (6–8 s), sala → cocina (8–10 s), segunda recámara (11.6–12.9 s) y cocina (14–16.2 s)** |
| `IMG_5837.HEIC` | Comedor de día, foto original | Alternativa para el comedor |
| `IMG_4126`, `IMG_5694` | Reunión con personas y una carretera | No se usan: no son del departamento |
| Fotos pegadas en el chat | Alberca, jardines, recámaras, baños, cocina, sala, terraza | No llegan como archivo. **Hay que adjuntarlas** (ver [05-pendientes.md](05-pendientes.md)) |
| Mapa de ubicación | Playa Zona Dorada a 11 min / 5.7 km, aeropuerto PVR a 25 min / 13.4 km | Copy. **La playa no queda a distancia caminable** |
| Carpeta de Drive y web | Bloqueadas por la red de este entorno | — |

**Los clips de iPhone están en HDR (HLG, BT.2020, 10 bits).** Si se suben así o se convierten sin cuidado, Facebook los muestra lavados o con rojos "neón". El proyecto los convierte a SDR (BT.709) con mapeo de tonos y compresión suave de gama, para que el atardecer se vea natural.

> **Dato a favor:** el atardecer de la playa se grabó un 2 de enero, en pleno invierno. Por favor confirma que es la playa de Bucerías: se etiqueta así en el video.

---

## 2. Diagnóstico de los preliminares

| Hallazgo en los preliminares | Por qué importa en un anuncio | Solución aplicada |
|---|---|---|
| **Disolvencias en los 13 cambios de toma**, combinadas con zoom | Los muebles de dos espacios se mezclan y el cliente no entiende la distribución | **Cortes limpios.** Solo hay 4 disolvencias de 0.2–0.3 s, entre interior y exterior o hacia el cierre |
| Abre con la terraza **de noche** (preliminar de 35 s) y con el edificio y la alberca (preliminar de 30 s) | De noche, la terraza no se aprecia en un teléfono. El edificio no dice "tu casa de invierno" | A: alberca luminosa. B: terraza **de día** (clip real) |
| La terraza diurna (3–6 s) está tomada con gran angular inclinado | Las líneas torcidas restan credibilidad | Por ahora se mantiene. **Hace falta una foto diurna recta de la terraza** |
| "2 BEDROOMS · 2 BATHROOMS / **Private terrace**" sobre la **recámara** | El texto no coincide con la imagen y el cliente pierde confianza | Cada texto entra con su imagen. "Private terrace" va sobre la terraza |
| Textos en serif delgada, pequeños y en mayúsculas espaciadas ("C O N D O  L U A") | No se leen en un teléfono sin sonido. Fechas y CTA pequeñas | Titulares de 104 px, información de 66 px y CTA en píldora de 54 px. Sombra suave y oscurecimiento localizado |
| "Your winter home in Bucerias" (sin acento) | Detalle de calidad | "Bucerías" en todo el material |
| 5 s sobre un **detalle decorativo** (sillón) | Ocupa el espacio de un beneficio | El sillón se queda porque es una toma tranquila, pero ahora lleva el beneficio principal: servicios incluidos |
| **Sin música** | En Reels, el silencio total se percibe como un error | Pista instrumental con licencia para anuncios (ver [04-musica.md](04-musica.md)) |
| Exportación de WhatsApp a 4 Mbps | Facebook la recomprime y se pierde nitidez | Export a CRF 16 (~5 Mbps con material provisional) desde los originales |

### Observaciones adicionales al brief

1. **"Pool nearby" cambió a "Shared pool & gardens".** Las fotos muestran que la alberca y los jardines son del condominio. "Nearby" la hacía sonar externa y restaba valor. Si prefieres el texto original, se cambia en una línea del JSON.
2. **Versión B: no repetir la misma toma.** En B, de 0 a 6 s hay dos tomas seguidas de terraza. Por eso la apertura usa el clip `IMG_6032` (mesa de día con cortinas en movimiento) y 3–6 s usa el plano amplio de la terraza con el ventanal.
3. **Electricidad sin tope (confirmado).** "Electricity, water & Wi-Fi included" se queda tal cual. Es un diferenciador real: en México la luz es cara cuando se usa el A/C, y muchos anuncios la cobran aparte.
4. **El precio no va en el video, pero sí en el copy.** Para estancias largas, el precio es el primer filtro del cliente. Un "From $X USD/month" en el texto del anuncio reduce las conversaciones que no llegan a nada y sube la proporción de mensajes con fechas reales. El video queda sin precio para que siga sirviendo si la tarifa cambia.
5. **"Condo fees included".** Para un turista estadounidense el término natural es *HOA fees*; para un canadiense, *condo fees*. Se mantiene "Condo fees included", que ambos entienden. En el copy largo se aclara como "Condo (HOA) fees included".
6. **La llamada a la acción ya es correcta.** "Message us for dates & rates" funciona tanto con Messenger como con WhatsApp y pide justo lo que buscamos: fechas.
7. **"Monthly stays" cambió a "3–4 month stays".** Con una estancia mínima de 3 meses, "Monthly stays" atraería a quien busca 1 o 2 meses y llenaría el chat de consultas que no cierran. "3–4 month stays" filtra desde el video, que es justo el objetivo del brief: consultas con duración real.

---

## 3. Estructura del reel (35 s)

Detalle toma por toma en [02-guion.md](02-guion.md). En resumen:

```
0–3   Gancho emocional    Alberca (A) o terraza (B)   "Your winter could look like this."
3–6   Diferenciador       Terraza privada             "Your own private terrace"
6–18  Prueba funcional    Sala · recámaras · cocina   furnished · ground floor · 2+2 · kitchen · laundry
18–22 Entorno             Alberca y jardines          "Shared pool & gardens · Space to unwind"
22–27 Beneficio clave     Toma tranquila (5 s)        "Electricity, water & Wi-Fi included" + "Condo fees included"
27–30 Destino             Playa de Bucerías (real)    "Bucerías beach"
30–35 Cierre + CTA        Terraza cálida              CONDO LUA · Winter 2027 · Jan–Apr · Message us
```

---

## 4. Estrategia de pauta en Meta

### 4.1 Categoría especial de anuncio: vivienda (*Housing*)

Meta exige declarar la categoría especial **Housing** en los anuncios de "renta de vivienda o vivienda temporal" dirigidos a Estados Unidos o Canadá. Una renta de 3 a 4 meses encaja en esa definición: no es un hotel. **Recomiendo declararla.** Si no se declara, el anuncio puede ser rechazado y la cuenta puede recibir restricciones.

Consecuencias prácticas:
- No se puede segmentar por edad, género ni código postal. El radio mínimo es de 15 millas (~25 km).
- La segmentación detallada por intereses es limitada.
- **Por eso el creativo es el que segmenta.** "Your winter…", "Winter 2027" y "3–4 month stays" hacen que el público se autoseleccione: a quien no busca una estancia de invierno no le interesa. Conviene dejar que Meta optimice (Advantage+ audience) dentro de los países y regiones elegidos.

### 4.2 Configuración recomendada

| Elemento | Recomendación |
|---|---|
| Objetivo | **Interacción → Apps de mensajes**, con **WhatsApp y Messenger** activos: Meta lleva a cada persona a la app que usa. Requiere vincular el WhatsApp Business a la página |
| Alternativa | **Clientes potenciales → Formulario instantáneo** con preguntas obligatorias: fecha de llegada, número de meses, número de huéspedes y correo. Úsala si no hay disponibilidad para responder chats en minutos. **Requiere un enlace a la política de privacidad** (por ejemplo, una página en mymatiaricondo.com); sin él, Meta no deja publicar el formulario |
| Ubicaciones | Canadá y Estados Unidos. Prioridad: provincias y estados de invierno frío (BC, Alberta, Saskatchewan, Manitoba, Ontario, Quebec; Minnesota, Wisconsin, Michigan, Illinois, Washington, Oregon, Colorado, Nueva York, Nueva Inglaterra) |
| Idioma | Inglés. Agrega un conjunto en francés para Quebec solo si alguien puede atender en francés (copy en [03-copy-anuncio.md](03-copy-anuncio.md)) |
| Ubicaciones del anuncio | Reels y Stories de Facebook e Instagram (9:16). Si se quiere aparecer en el feed, conviene una versión 4:5 adicional |
| Prueba A/B | Usa la herramienta *A/B test* de Meta, o pon cada versión en su propio conjunto de anuncios, idéntico en todo lo demás y con el mismo presupuesto. **No las pongas juntas en un mismo conjunto**: ahí Meta no reparte el presupuesto por igual, sino que concentra la entrega en la que predice mejor, y la comparación de aperturas deja de ser justa |
| Presupuesto de prueba | Orientativo: USD 10–15 diarios por versión durante 7 días. Después se apaga la perdedora y el presupuesto pasa a la ganadora |
| Calendario | **Lanzar cuanto antes.** Para enero–abril, muchos *snowbirds* deciden entre octubre y diciembre, antes de las fiestas |

### 4.3 Métricas para decidir

| Métrica | Qué indica | Referencia |
|---|---|---|
| Tasa de gancho (reproducciones de 3 s ÷ impresiones) | Si la apertura detiene el scroll: **es la que decide entre A y B** | > 25–30 % |
| ThruPlay ÷ reproducciones de 3 s | Si el contenido retiene | > 15–20 % |
| Costo por conversación iniciada | Eficiencia del anuncio | Comparar A vs B |
| **% de conversaciones con fechas y duración** | Calidad real (objetivo del brief) | Registrar a mano en una hoja: fecha, versión, fechas pedidas, meses, huéspedes, estado |

### 4.4 Atención de mensajes

La pauta solo funciona si se responde rápido: idealmente en menos de 15 minutos, en inglés. En [03-copy-anuncio.md](03-copy-anuncio.md) están el saludo automático, las preguntas frecuentes (*ice-breakers*) y respuestas listas para copiar.

---

## 5. Precisión y cumplimiento

- No usar nunca "all-inclusive", "beachfront", "ocean view", "walk to the beach" ni "steps to the beach": la playa queda a 11 min en auto.
- No anunciar gimnasio, alberca climatizada, acceso sin escalones ni distancias sin verificar. "Ground floor" es un hecho; "step-free" no lo es.
- Todas las imágenes son reales: no se agregan vistas, amenidades ni espacios con IA. Si falta una toma (cocina, lavandería), se pide en lugar de sustituirla.
- La playa se identifica como "Bucerías beach" para distinguirla del condominio.
- La música debe tener licencia para anuncios pagados. Las canciones "en tendencia" de Reels **no** sirven para anuncios de empresa.
- Exportar siempre desde los archivos originales, no desde el video descargado de WhatsApp: cada recompresión le resta calidad.
