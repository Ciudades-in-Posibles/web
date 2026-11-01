# AGENTS.md — Ciudades(In)Posibles

Portal de **Ciudades(In)Posibles**, un juego emersivo sobre nuestro derecho a co-crear la ciudad, y la app de su asistente, el **Cronista**. El **Cartógrafo** queda como archivo. Lee este archivo antes de hacer cambios. Las decisiones de tono, contenido e identidad visual son del equipo: ante la duda, pregunta.

## Repositorio

Este repositorio contiene solo la web: `public/`, `firebase.json` (solo `hosting:principal`), `.firebaserc` y este archivo. Vive en `~/Desarollo/ciudadesinposibles/web/` desde el 1 nov 2026; antes era `~/Desarollo/sociedaddeciudadesinposibles/`.

```
public/        portal · https://ciudadesinposibles.net (HTML + CSS + JS vanilla)
firebase.json  Hosting del portal (target principal)
```

Al lado, en `~/Desarollo/ciudadesinposibles/` y fuera de este repositorio: `cronista/`, `cartografo/` y `functions/` (se publican desde la raíz de esa carpeta, ver su `AGENTS.md`), `docs/` (fuente del contenido, sin publicar ni versionar), `herramientas/` (scripts de diseño: `mosaico.py` genera los SVG del mosaico y `miniatura.html` la `og.png`) y `aplicaciones/` (Transmisor, Visor y Consola, con su propio repo).

- Commits pequeños y descriptivos. GitHub `Ciudades-in-Posibles/web` (`origin`, público), directo en `main` o en ramas cortas.
- Nunca subas credenciales ni correos de administración: el repositorio es público.
- **Textos:** todo texto nuevo o reescrito se pasa a revisión del equipo antes de aplicarlo.

## Portal (`public/`)

- HTML semántico, CSS propio con tokens y JS solo como mejora progresiva (el contenido se ve sin JS). Sin frameworks, dependencias ni build salvo que se pida.
- Rutas: `/` · `/manifiesto/` (§ 00 y `coordenada-i/` a `coordenada-v/`) · `/el-juego/` (cómo se juega) · `/cronista/` (tarjeta que abre la app) · `/espacios/` · `/documentacion/` (`referencias/`, `glosario/`, `ciudad-1-5/`) · `/acerca/`.
- Cada página es `carpeta/index.html` y repite cabecera y pie. Un cambio en el menú o el pie va en todas, incluida `404.html`.
- Página nueva: `<link rel="canonical" href="https://ciudadesinposibles.net/<ruta>/">` y entrada en `sitemap.xml`. Las rutas cambiadas redirigen con 301 desde `firebase.json` (`/juego/` → `/el-juego/`, `/asistentes/` → `/cronista/`).
- **Caché de 24 h:** si cambias `styles.css` o `main.js`, sube su `?v=N` en todas las páginas (hoy `/css/styles.css?v=33` y `/js/main.js?v=8`; `aparatos.css`, `cartas.css`, `juego.css`, `portada.css`, `juego.js` y `portada.js` llevan su propio `?v=N`).
- **Contenido:**
  - El Manifiesto es copia fiel de `../docs/Manifiesto/*.md`; cada cambio se hace en los dos lados.
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

El Cronista (`/cronista/` enlaza a la app) y el Cartógrafo (archivo) viven en `../cronista/` y `../cartografo/`, con sus funciones en `../functions/`. Su descripción y cómo se publican están en `~/Desarollo/ciudadesinposibles/AGENTS.md`.

## Desarrollo y despliegue

```bash
firebase serve --only hosting:principal          # portal en local
firebase hosting:channel:deploy <canal>          # vista previa
firebase deploy --only hosting:principal         # portal en producción
```

- Desde este repositorio se publica solo `hosting:principal`. Cronista, Cartógrafo, sus reglas de Firestore y sus Functions se publican desde `~/Desarollo/ciudadesinposibles/`; Transmisor, Visor y Consola, desde `aplicaciones/`.
- Producción solo después de revisión. No agregues servicios de Firebase (Storage, bases nuevas…) sin que se pida.
- La clave web de Firebase está restringida por sitio web (Google Cloud → Credenciales). Un dominio nuevo hay que sumarlo ahí.
- Dominio en Namecheap (*Advanced DNS*): host relativo (`cartografo`), conserva el TXT SPF del reenvío de correo. `www` redirige al dominio sin www desde Firebase.

## Convenciones

- **Idioma:** español latino neutro, con tildes y lenguaje incluyente («las personas», «quienes habitan la ciudad»). `<html lang="es">`.
- **Nombre:** siempre **Ciudades(In)Posibles**.
- **Redacción:** afirmativa, sin «no es X, sino Y», «en lugar de» ni «más que». Dos puntos solo para enumerar. Vocabulario del juego: juego emersivo, lo (In)Posible, presentes alternativos, a escala de las niñas y los niños, continuo análogo-digital ecológicamente situado. El juego se juega en toda la ciudad.
- **HTML:** etiquetas semánticas, una `h1` por página, encabezados en orden y `alt` en toda imagen (`alt=""` si es decorativa).
- **CSS:** mobile-first, tokens en `:root`, contraste WCAG AA y `prefers-reduced-motion`.
- **Accesibilidad y peso:** navegable con teclado y foco visible, imágenes en WebP o AVIF, Lighthouse antes de publicar cambios importantes.
