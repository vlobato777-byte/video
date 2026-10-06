# Pendientes: material y confirmaciones

## A. Material que falta para la versión final

El render actual ya es publicable como **versión de revisión**. Muchas tomas salen de cuadros del video de WhatsApp (`media/source/borrador_whatsapp/`), que tienen menor calidad. Para la exportación final hay que reemplazarlas por las **fotos originales**.

| Toma | Estado | Qué falta (archivo original) |
|---|---|---|
| 01A Alberca (0–3 s) | Cuadro del borrador | ⏳ **Foto vertical de la alberca con camastros al atardecer** |
| 02 Terraza privada (3–6 s) | Cuadro del borrador (gran angular inclinado) | ⏳ **Foto diurna y recta de la terraza** con la mesa y el ventanal |
| 03a Comedor → sala → terraza (6–8 s) | ✅ `IMG_5993` original | — |
| 03b Sala → cocina (8–10 s) | ✅ `IMG_5857` original | — |
| 04a Recámara principal | Cuadro del borrador | ⏳ Foto de la cama king con A/C y la ventana al patio |
| 04b Segunda recámara | ✅ `IMG_5896` original | — |
| 04c Baño | Cuadro del borrador | ⏳ Baño con regadera y luz cálida en el plafón |
| 05a Cocina | ✅ `IMG_5864` original | — |
| 05b Lavandería | Cuadro del borrador | ⏳ Lavadora y secadora |
| 06a Alberca al atardecer | Cuadro del borrador de 30 s | ⏳ (puede ser la misma de 01A en otro encuadre, o la panorámica de la alberca con los dos edificios) |
| 06b Jardines | Cuadro del borrador | Opcional: jardín con andador y palmeras. Alternativa: `IMG_6083` |
| 07 Toma tranquila | Cuadro del borrador | ⏳ Sillón con manta mostaza junto al ventanal |
| 08 Playa | ✅ `IMG_3349.mov` original (HDR) | — |
| 09 Cierre | Cuadro del borrador | ⏳ Terraza de noche (copas, vela, luces) |
| 01B Terraza (versión B) | ✅ `IMG_6032.MOV` original | — |

**Faltan 8 archivos para la versión 35 s definitiva** (marcados con ⏳). La versión actual ya se puede publicar; con los originales gana nitidez.

> ⚠️ **Fotos con marca de IA:** dos de las imágenes que pegaste en el chat (la terraza de noche con copas y vela, y el baño con regadera) tienen en la esquina inferior derecha el destello de cuatro puntas que agrega Google Gemini al editar. El brief pide no añadir nada con IA. Envía la **foto original sin editar** o confirma que la edición solo ajustó la luz, sin agregar ni quitar elementos.

**Cómo enviarlos:** adjunta los archivos en el chat (como hiciste con `IMG_5837.HEIC` y los `.MOV`). Las imágenes **pegadas** dentro del mensaje no llegan como archivo y no se pueden usar en el video. Los HEIC sirven tal cual.
**Drive:** si prefieres la carpeta completa, agrega `drive.google.com` y `drive.usercontent.google.com` a los dominios permitidos del entorno (menú del entorno → Edit → Network access → Custom). Los pasos están en https://code.claude.com/docs/en/cloud-environments#network-access

> `IMG_4126` (reunión con personas) no se usa ni se sube al repositorio. `IMG_5694` (autopista a Guadalajara) queda guardada para el reel de la región (ver [06-serie-de-reels.md](06-serie-de-reels.md)).

## B. Datos por confirmar (afectan al video o al copy)

| # | Pregunta | Dónde impacta |
|---|---|---|
| 1 | **¿La electricidad tiene tope?** (kWh o pesos al mes) | Texto 22–27 s y copy |
| 2 | **Tarifa mensual** enero–abril 2027 y moneda (USD/CAD/MXN) | Copy y respuestas |
| 3 | **Estancia mínima** (¿1, 2 o 3 meses?) y si se aceptan estancias parciales (p. ej., solo febrero–marzo) | Copy |
| 4 | Depósito, forma de pago, cancelación y limpieza | Respuestas |
| 5 | Ocupación máxima y camas (king + 2 individuales/matrimoniales) | Copy |
| 6 | ¿Se aceptan mascotas? ¿Se permite fumar? | Respuestas (*snowbirds* con perro es un caso común) |
| 7 | Velocidad del Wi-Fi (Mbps) | Copy (atrae a trabajadores remotos) |
| 8 | Estacionamiento: ¿cuántos lugares? ¿techado? | Copy |
| 9 | Vigilancia: ¿caseta 24/7? | Copy |
| 10 | **Nombre comercial:** el brief dice "Condo Lua", el mapa dice "Lua Condo (Matiari)" y la web es *mymatiaricondo.com* | Video, copy y página. Hay que usar el mismo nombre en todo |
| 11 | Destino del anuncio: **WhatsApp** (número de WhatsApp Business vinculado a la página) o **Messenger** | Botón del anuncio |
| 12 | Distancias del mapa: Zona Dorada Bucerías 11 min / 5.7 km, Fibba Beach 15 min / 7.6 km, aeropuerto PVR 25 min / 13.4 km, supermercados La Comer, Mega Soriana y Walmart. **¿Son en auto y están verificadas en Google Maps?** | Copy (se citan como "about … drive") |

## C. Decisiones ya tomadas con base en el material

- **La playa queda a 11 minutos en auto**, así que el video la etiqueta como "Bucerías beach" en una escena separada y el copy dice "drive". Nunca "walk to the beach".
- La alberca **es del condominio** (se ve en las fotos), por eso el texto cambió de "Pool nearby" a **"Shared pool & gardens"**. Si prefieres el texto original, se cambia en una línea del JSON.
- La lavandería **existe y está en el material** (lavadora y secadora apiladas), así que "In-suite laundry" va sobre esa toma.
