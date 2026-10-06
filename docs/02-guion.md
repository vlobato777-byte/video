# Guion y storyboard: reel de 35 s (1080 × 1920)

Los textos en pantalla van en inglés, porque la audiencia es de Canadá y Estados Unidos. Las indicaciones están en español.
La fuente de verdad es [`project/condo_lua_reel.json`](../project/condo_lua_reel.json): cualquier cambio de tiempos o textos se hace ahí y se vuelve a renderizar.

**Tipografía:** titulares en *Cormorant Garamond* SemiBold (serif elegante); información en *Inter* Medium/SemiBold (sans sencilla).
**Paleta del texto:** blanco cálido `#FFFBF4`, arena `#F7DDB5` para las fechas y píldora clara `#F5EDE0` con texto café `#2A1E15` para la llamada a la acción.
**Zona segura de Reels:** el texto queda entre el 14 % superior y el 35 % inferior, con un margen lateral del 6 %. Ningún texto sale de esa zona.

## Versión A: apertura en la alberca (principal)

| Tiempo | Toma | Texto en pantalla | Movimiento y transición | Música |
|---|---|---|---|---|
| 0.0–3.0 | **Alberca**: la toma más luminosa, con poco cielo (encuadre bajo) | **Your winter could look like this.** (serif 104 px) · *Bucerías, Mexico* (entra a los 0.65 s) | Acercamiento lento del 10 al 16 % | Entrada suave, sin golpe |
| 3.0–6.0 | **Terraza privada**, de día: mesa + puerta o ventanal | **Your own private terrace** | Corte. Paneo lateral corto + acercamiento del 4 % | Entra el ritmo |
| 6.0–8.0 | **Sala → comedor → cocina** (`IMG_5857`, original): explica la distribución | **Fully furnished** / **Ground floor** (+0.35 s, de 6.15 a 9.9) | Corte. Acercamiento del 5 % | |
| 8.0–10.0 | **Comedor y sala con la terraza al fondo** (`IMG_5838`, recortada) | (continúa) | Corte. Paneo lateral | |
| 10.0–11.6 | **Recámara principal** | **2 bedrooms · 2 bathrooms** (de 10.15 a 13.9) | Corte. Acercamiento del 5 % | |
| 11.6–12.9 | **Segunda recámara** | (continúa) | Corte. Alejamiento del 5 % | |
| 12.9–14.0 | **Baño** (solo si la toma es buena) | (continúa) | Corte | |
| 14.0–16.2 | **Cocina equipada** (`IMG_5864`, original vertical) | **Equipped kitchen** | Corte. Acercamiento del 6 % | |
| 16.2–18.0 | **Lavadora y secadora** | **In-suite laundry** (aparece con la lavadora) | Corte | |
| 18.0–20.0 | **Alberca al atardecer**: ángulo distinto al de la apertura | **Shared pool & gardens** / **Space to unwind** | Disolvencia de 0.2 s (interior → exterior) | |
| 20.0–22.0 | **Jardines** | (continúa) | Corte. Paneo suave | |
| 22.0–27.0 | **Toma tranquila del departamento**, con zona despejada arriba | **Electricity, water & Wi-Fi included** + píldora **Condo fees included** (+0.6 s) | Disolvencia de 0.2 s. Acercamiento muy lento. Oscurecimiento sutil del 18 % detrás del texto | Bajar la intensidad para leer |
| 27.0–30.0 | **Playa de Bucerías**: `IMG_3349.mov`, atardecer real de enero | **Bucerías beach** | Disolvencia de 0.2 s. Acercamiento del 5 % | Momento emotivo |
| 30.0–35.0 | **Cierre: terraza cálida** (la del cierre actual) | **CONDO LUA** · *Bucerías · Winter 2027* · **January–April · 3–4 month stays** · píldora **Message us for dates & rates** (entradas escalonadas de 0.3 s; quedan fijas hasta el final) | Disolvencia de 0.3 s. Oscurecimiento del 38 % detrás del texto. **Sin fundido a negro**, para que el último cuadro muestre la llamada a la acción | Resolución y salida de 2.5 s |

## Versión B: apertura en la terraza

Es idéntica a la A, salvo de 0 a 3 s:

| Tiempo | Toma | Texto |
|---|---|---|
| 0.0–3.0 | **Mesa de la terraza de día** (`IMG_6032.MOV`, video real con cortinas en movimiento), con un ángulo **distinto** al de 3–6 s | **Your winter could look like this.** · *Bucerías, Mexico* |

Así, cualquier diferencia de resultados se debe solo a la apertura.

## Textos alternativos (según lo que se confirme)

| Situación | Cambiar en el JSON |
|---|---|
| ~~La electricidad tiene tope~~ (confirmado: **sin tope**, no aplica) | — |
| Prefieres el texto original del brief | `c06_alberca`: "Pool nearby" / "Space to unwind" |
| **No hay** toma de baño de calidad | Eliminar `04c_bano` y extender `04b_recamara_2` hasta 14.0 |
| **No hay** toma de lavandería | No sustituirla. Pedir el material. Mientras tanto, "In-suite laundry" puede ir sobre la cocina **solo si** la lavadora está en ese mismo espacio |

## Ritmo de lectura

Ningún texto está en pantalla menos de 2.7 s. El beneficio principal (servicios incluidos) dura 4.7 s y la llamada a la acción final, 3.75 s. Así se lee cómodamente sin sonido.
