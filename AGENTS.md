# AGENTS.md — Ciudades(In)Posibles

Portal de **Ciudades(In)Posibles**, un juego emersivo sobre nuestro derecho a co-crear la ciudad, y la app de su asistente, el **Cronista**. El **Cartógrafo** queda como archivo. Lee este archivo antes de hacer cambios. Las decisiones de tono, contenido e identidad visual son del equipo: ante la duda, pregunta.

## Repositorio

Este repositorio contiene solo la web. Cronista, Cartógrafo y `functions/` siguen en disco, pero están fuera de git (ver `.gitignore`) y se respaldan en `~/Desarollo/_respaldos/`.

```
public/        portal · https://ciudadesinposibles.net (HTML + CSS + JS vanilla)
herramientas/  scripts de diseño (mosaico.py genera los SVG del mosaico)
docs/          fuente del contenido; no se publica ni se versiona
firebase.json  Hosting y reglas de Firestore
```

Fuera de git, solo en disco:

```
cartografo/    app · https://cartografo.ciudadesinposibles.net (React + Vite + Tailwind)
cronista/      app · https://cronista.ciudadesinposibles.net (React + Vite + Tailwind)
functions/     Cloud Functions v2 (Node 22) que consultan la IA para las dos apps
```

- Commits pequeños y descriptivos. GitHub `Ciudades-in-Posibles/web` (`origin`, público), directo en `main` o en ramas cortas.
- Nunca subas credenciales. Las apps no usan archivos `.env`: la clave de la IA vive en Secret Manager. `cartografo/data/` está en `.gitignore`.
- **Textos:** todo texto nuevo o reescrito se pasa a revisión del equipo antes de aplicarlo.

## Portal (`public/`)

- HTML semántico, CSS propio con tokens y JS solo como mejora progresiva (el contenido se ve sin JS). Sin frameworks, dependencias ni build salvo que se pida.
- Rutas: `/` · `/manifiesto/` (§ 00 y `coordenada-i/` a `coordenada-v/`) · `/el-juego/` (cómo se juega) · `/cronista/` (tarjeta que abre la app) · `/espacios/` · `/documentacion/` (`referencias/`, `glosario/`, `ciudad-1-5/`) · `/acerca/`.
- Cada página es `carpeta/index.html` y repite cabecera y pie. Un cambio en el menú o el pie va en todas, incluida `404.html`.
- Página nueva: `<link rel="canonical" href="https://ciudadesinposibles.net/<ruta>/">` y entrada en `sitemap.xml`. Las rutas cambiadas redirigen con 301 desde `firebase.json` (`/juego/` → `/el-juego/`, `/asistentes/` → `/cronista/`).
- **Caché de 24 h:** si cambias `styles.css` o `main.js`, sube su `?v=N` en todas las páginas (hoy `/css/styles.css?v=33` y `/js/main.js?v=8`; `aparatos.css`, `cartas.css`, `juego.css`, `portada.css`, `juego.js` y `portada.js` llevan su propio `?v=N`).
- **Contenido:**
  - El Manifiesto es copia fiel de `docs/Manifiesto/*.md`; cada cambio se hace en los dos lados.
  - Las referencias son fichas curadas con citas breves.
  - Coordenadas propias en romano (§ I–V); las del Plan de Cultura se nombran «Coordenada N del Plan».
  - El glosario usa anclas fijas (`/documentacion/glosario/#eep`); crea el `<dt id>` antes de enlazarlo.
  - Lo que falta confirmar se marca con `<!-- Pendiente: … -->`.

## Identidad visual «Mosaico»

- Paleta espectral sobre grafito (`--fondo` #2A2A2D en el tema oscuro): bloques de color (manzanas), negro (calles), cortes diagonales (avenidas), recorte circular y grano.
- En ilustraciones, calles y avenidas curvadas y manzanas como células de esquinas redondeadas, al modo de una imagen de microscopía.
- El color va de fondo con texto negro (crema sobre vinotinto y violeta); nunca texto de color sobre color. Cada sección tiene su clase `c-*` en `<body>` y en las tarjetas.
- Tipografías: Gabarito (titulares y lectura, pesos 400–900) e IBM Plex Mono (etiquetas y datos).
- **Prohibido:** skylines, siluetas de edificios, fotos de stock urbanas, curvas de nivel, mapas y diagramas.
- **Tema claro:** papel `#F5F3EA` con tinta negra. Sigue `prefers-color-scheme` y el botón de la cabecera (`data-tema` en `<html>`, en `localStorage`). Fondo y texto con `--fondo`, `--tinta`, `--tinta-2` y `--superficie`; acentos con `--acento-*` (contraste ≥ 3:1). Los tokens van en la media query y en `[data-tema="claro"]`, idénticos.

## Asistentes

Esta sección describe las apps que viven fuera de este repositorio. Se conserva como referencia.

Dispositivos de juego y relato inspirados en Italo Calvino, con vocabulario separado:

- El **Cronista** asiste la partida. Bajo la lente de cada ronda, los equipos co-crean **espacios**, **puntos** y **vecinos** con fotos y voz (de 1 a 3 fotos por espacio y hasta 3 por punto o vecino), los vuelven **cartas** (código `C-NN`) y arman el **mosaico** de la partida, con versiones. «Crónica» es exclusiva del Cronista.
- El **Cartógrafo** queda como archivo. Sigue publicado para consultar sus cartas y sus relatos cruzados, fuera del portal, y recibe solo correcciones.

Las dos apps comparten comandos: `npm run dev`, `npm test` y `npm run build` (genera `dist/`, lo que se publica). La IA (Gemini 3.8 Flash por OpenRouter) corre en `functions/`: `cronistaDescribirImagen`, `cronistaCrearCarta`, `cartografoCatalogarLoseta` y `cartografoAnalizarTablero`. Las apps las llaman con `httpsCallable` y una sesión de Auth activa. El modelo está fijado en el servidor y la clave vive en Secret Manager (`OPENROUTER_API_KEY`), nunca en el cliente ni en el repositorio. Para cambiarla: `firebase functions:secrets:set OPENROUTER_API_KEY` y `firebase deploy --only functions`.

**Cartógrafo (`cartografo/`):** Firebase Auth con Google y base Firestore `cartografo` (`cartografo/firestore.rules`). En el ticket de la impresora térmica (`src/services/escposFormatter.js`) se escribe sin tildes: `CARTOGRAFO`.

**Cronista (`cronista/`):**
- Quienes juegan entran solo con el código de la partida (Auth anónimo) y juegan como su equipo. Las fotos se firman con el nombre del equipo. Para volver a un equipo se escribe el código y se toca el equipo en la lista. El administrador entra con Google. El email del administrador está en `firestore.rules` y en `authService.js`, y debe coincidir.
- Base Firestore `cronista` con `sesiones` (lente y ajustes de IA), `equipos`, `espacios`, `puntos`, `vecinos`, `registros` (fotos de cada elemento), `cartas`, `contadores`, `mosaicos` y `facilitaciones`; solo los miembros de un equipo escriben en sus espacios.
- Fotos en base64 dentro de cada registro, comprimidas a 1024 px (`src/utils/imagen.js`), sin Storage. Gemini 3.8 Flash las describe (`describirImagen` en `src/config/openrouter.js`).
- Cada pieza tiene su color y su glifo del manual: espacio amarillo, punto menta y vecino lima (`src/config/elementos.js`). Las tarjetas chicas usan la célula suave `manzana--chica`.
- Quien juega se mueve con la barra inferior (Espacios, Puntos, Foto, Vecinos y Mosaico), sin botones «Volver». El punto enlaza a su espacio y a sus vecinos; el vecino, a los puntos que cruza.
- Las listas muestran filas con miniatura (`FilaPieza`). Cada pieza guarda en su documento una `miniatura` de 240 px y menos de 60 KB, que se renueva al subir o borrar fotos. Todas las fotos se ven cuadradas.
- Se pueden borrar un espacio sin fotos ni puntos, un punto sin fotos ni vecinos y un vecino junto con sus fotos.
- Quien facilita abre cada partida en su tablero (`TableroPartida`), con la lente, los equipos y sus piezas. Ahí modera: borra fotos y piezas vacías, sin crear ni tomar fotos.
- **Facilitación invitada:** el administrador crea, cambia o quita desde la partida un enlace `?facilitar=CÓDIGO` (`InvitarFacilitacion`). El código (10 caracteres) es el id de un documento en `facilitaciones` (`{ sessionId }`), que se lee solo por id. Quien lo abre entra con Auth anónimo al tablero en modo `consulta`: ve todo y descarga, sin QR, lente, moderación ni escrituras.
- **Descargas:** cada foto revisada por el filtro de rostros (`ia.estado === 'listo'`), carta y versión del mosaico tiene «Descargar». El tablero baja toda la partida en un .zip (`src/services/exportarPartida.js`, con `jszip` cargado al usarlo), ordenado por equipo y pieza, con `cronica.csv` de comentarios y descripciones.
- `npm run dev` usa el puerto 5174.

**Rostros reconocibles:** ninguna app guarda fotos con caras reconocibles de personas reales (se permiten murales, afiches, estatuas y personas lejanas o de espaldas). `src/config/rostros.js` es idéntico en las dos apps: añade en código la instrucción al prompt de sistema y `verificarRostros` rechaza la foto con `RostrosError`, también si falta el campo. El filtro corre en el cliente, así que una escritura directa en Firestore podría saltárselo.

## Desarrollo y despliegue

```bash
firebase serve --only hosting:principal          # portal en local
firebase hosting:channel:deploy <canal>          # vista previa
firebase deploy --only hosting:principal         # portal en producción
```

- Desde este repositorio se publica solo `hosting:principal`. Cronista, Cartógrafo, Firestore y Functions se despliegan desde sus carpetas en disco, fuera de aquí.
- Producción solo después de revisión. No agregues servicios de Firebase (Storage, bases nuevas…) sin que se pida.
- Pendiente para el rediseño: App Check o un límite por usuario en las funciones, porque hoy responden a cualquier cuenta anónima.
- Dominio en Namecheap (*Advanced DNS*): host relativo (`cartografo`), conserva el TXT SPF del reenvío de correo. `www` redirige al dominio sin www desde Firebase.

## Convenciones

- **Idioma:** español latino neutro, con tildes y lenguaje incluyente («las personas», «quienes habitan la ciudad»). `<html lang="es">`.
- **Nombre:** siempre **Ciudades(In)Posibles**.
- **Redacción:** afirmativa, sin «no es X, sino Y», «en lugar de» ni «más que». Dos puntos solo para enumerar. Vocabulario del juego: juego emersivo, lo (In)Posible, presentes alternativos, a escala de las niñas y los niños, continuo análogo-digital ecológicamente situado. El juego se juega en toda la ciudad.
- **HTML:** etiquetas semánticas, una `h1` por página, encabezados en orden y `alt` en toda imagen (`alt=""` si es decorativa).
- **CSS:** mobile-first, tokens en `:root`, contraste WCAG AA y `prefers-reduced-motion`.
- **Accesibilidad y peso:** navegable con teclado y foco visible, imágenes en WebP o AVIF, Lighthouse antes de publicar cambios importantes.
