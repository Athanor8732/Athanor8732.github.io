# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Què és això

Web personal estàtic de Marc Cerdà i Domènech (geocientífic marí, UB). HTML/CSS/JS fet a mà, sense framework ni generador de site global — cada pàgina és un `index.html` autosuficient. Repo **privat** (`Athanor8732/marc-links`); GitHub Pages **desactivat** per decisió (pendent de re-publicar com a `Athanor8732.github.io` quan la versió estigui acabada).

## Arquitectura (actualitzada agost 2026)

La web abans tenia tot el CSS i JS inline duplicat a cada pàgina (~260 línies × 8). Després de la consolidació:

- **`css/styles.css`** — full d'estils base compartit (variables, reset, topbar+nav, gauge, prose, timeline, cards, CTD rig, side-promo, reveal, focus-visible, skip-link, prefers-reduced-motion, print). Carregat per totes les pàgines via `<link>`.
- **`css/fonts.css`** — `@font-face` per EB Garamond (títols) i Inter (body), self-hosted a `/fonts/*.woff2` (variable fonts, ~300KB total).
- **`js/ctd-rig.js`** — animació del CTD rosette (abans inline a 7 pàgines). Pausa el RAF quan el rig no és visible. Respecta `prefers-reduced-motion`.
- **`js/reveal.js`** — observador de scroll-reveal per als elements `.reveal`.
- **`vendor/leaflet/`** — Leaflet 1.9.4 self-hosted (CSS + JS + imatges), en lloc de CDN unpkg.
- **`templates/`** — partials HTML (`topbar.html`, `ctd-rig.html`, `side-promo.html`, `head.html`) amb marcadors `{DEPTH}`.
- **Cada pàgina** manté només el CSS específic inline (pàgines de projecte: `.pt-card`, `.method-grid`, etc.; home: `.profile`, `.porthole`, `.sonar`, etc.).

### Topbar amb navegació horitzontal
La topbar ara inclou nav horitzontal (Recerca, Publicacions, Docència, Premsa, Bloc, Contacte) a desktop, hamburger menu a móbil (`@media max-width:680px`). El link de la pàgina actual es marca amb `aria-current="page"`.

### Skip-link i accessibilitat
Cada pàgina té `<a class="skip-link" href="#main">` i `<div class="wrap" id="main">`. Focus-visible global. `prefers-reduced-motion` desactiva totes les animacions.

## Comandes

Previsualització local (servidor estàtic):
```bash
python3 -m http.server 8000 --bind 127.0.0.1   # http://127.0.0.1:8000/
```

Generar el bloc des del Markdown:
```bash
python3 scripts/build_blog.py
```

Actualitzar dades científiques des d'OpenAlex (es pot executar a mà; el workflow ho fa setmanalment):
```bash
python3 scripts/update_scholarly_data.py   # opcional: MAILTO=correu@example.org
```

Reinjectar partials HTML a les pàgines (després d'editar `templates/`):
```bash
python3 scripts/build_pages.py            # processa totes les pàgines
python3 scripts/build_pages.py --check    # dry-run
```

No hi ha build global, ni tests, ni linter. Els scripts són stdlib-only (cap `pip install`).

## Arquitectura

### Pàgines
Cada secció és un directori amb `index.html`: `index.html` (home), `sobre-mi/`, `recerca/`, `publicacions/`, `docencia/`, `premsa/`, `contacte/`, `blog/`, `impas-garraf/`, `emicreuer-bcn/`. Tots comparteixen el tema submarí (fons negre, accent `#39ffb0`, tipografia EB Garamond pels títols, Inter pel cos) definit a `css/styles.css`. El CSS específic de cada pàgina es manté inline al seu `<style>`.

### Stats data-driven (bloc inline `#stats-inline` + `update_scholarly_data.py`)
Qualsevol element `<... data-stat="KEY">` s'omple en runtime des d'un bloc JS inline (`<script id="stats-inline">`) que `update_scholarly_data.py` escriu directament al HTML de les 3 pàgines amb gauge (home, recerca, publicacions). El valor que hi ha a l'HTML entre les etiquetes és el **fallback estàtic** (es mostra sense JS). Convenció: el fallback ha de ser un valor realista, no un placeholder.

No hi ha `fetch` ni fitxer extern `stats.js` — tot el codi i les dades van inline al HTML, de manera que el navegador no pot cachar cap fitxer per separat. `data/stats.json` es manté al repo com a font de dades pel workflow, però no es consumeix al runtime.

`stats.json` barreja dos origens:
- **Camps automàtics** (els escriu `update_scholarly_data.py`): `publications`, `citations`, `hIndex`, `updated`, `source`.
- **Camps manuals** (del CV, l'script **no els toca** — definit a `MANUAL_STATS`): `projects`, `campaigns`, `campaignsDetailed`, `seaDays`, `intlCoauthorship`, `researchLines`, `researchLinesLabel`, `citeScoreTop`. Aquests s'editen a mà.

El bloc `#stats-inline` s'inclou a `index.html`, `recerca/index.html` i `publicacions/index.html` (les pàgines amb gauge). Tot el codi i les dades van inline — no hi ha `fetch` ni fitxer extern.

### Publicacions data-driven (`data/publications.json` + `js/publications.js`)
`publicacions/index.html` té una llista `<div class="pub-list">` que `js/publications.js` substitueix en runtime per les targetes del JSON. El bloc `.pub-list` del HTML és **fallback estàtic** i, a diferència dels stats, **és regenerat automàticament per `update_scholarly_data.py`** (mateix format que el JS). No l'editis a mà: els canvis van a `publications.json` i es propaguen executant l'script.

### Bloc (`content/posts/*.md` → `scripts/build_blog.py`)
Els articles viuen com a Markdown amb frontmatter a `content/posts/YYYY-MM-DD-slug.md`. Camps del frontmatter: `title`, `slug`, `date`, `date_display`, `excerpt`, `image`, `image_alt`, `source_url`, `source_note`. Al cos, els paràgrafs separats per línia en blanc esdevenen `<p>`; una línia que comenci per `> ` es renderitza com a `<blockquote>`. `build_blog.py` regenera `blog/index.html` i `blog/<slug>/index.html`. No hi ha fallback estàtic del bloc — cal executar l'script per veure els canvis.

## Automatització de dades científiques (OpenAlex)

`scripts/update_scholarly_data.py` + `.github/workflows/update-scholarly-data.yml` (cron dilluns 03:17 UTC + `workflow_dispatch`).

Font: **OpenAlex** (author id `A5002623148`), sense clau API, accessible des de qualsevol IP. (Es va descartar Scopus: la API key sola dona `AUTHORIZATION_ERROR` fora de la xarxa UB; caldria `insttoken` institucional.)

Lògica **híbrida** (seed curat + automàtic):
- `publications.json` és el seed curat (llistes d'autors, JIF i quartil del CV, `auto:false`). Per cada obra d'OpenAlex amb DOI:
  - Si el DOI ja és al seed → només s'actualitza `citations`.
  - Si és nova i és `article`/`review` → s'afegeix amb `auto:true` (autors en nom complet, `quartile:"—"`, `jif:""`) per curar-la després.
- DOIs homònims o erronis: afegir-los al set `EXCLUDE_DOIS`.
- Sense DOI → s'ignora (OpenAlex té duplicats sense DOI; així evitem doble recompte).

Després d'escriure el JSON, l'script també:
1. Regenera el bloc `.pub-list` de `publicacions/index.html` (`update_publications_html`).
2. Refresca els fallbacks del gauge `data-stat="publications|citations|hIndex"` a `index.html`, `recerca/index.html`, `publicacions/index.html` (`update_gauge_fallbacks`).

El workflow fa commit dels 5 fitxers (bot `github-actions[bot]`) i és **idempotent** (no commita si no hi ha diff).

### Convenis i gotchas
- `norm(s)` translitera diacritics via `unicodedata.normalize("NFKD")` + eliminar combining marks, perquè `Cerdà`→`cerda` (no `cerd`). No fer servir un regex directe sobre la cadena accentuada.
- Els JIF s'escriuen amb **coma decimal** (`"10,0"`, `"2,6"`) seguint el format del CV.
- `intlCoauthorship` (55,6%) és un camp manual del CV derivat de Scopus; a `recerca/index.html` va etiquetat `(Scopus)`, no prové d'OpenAlex.
- Els claims estàtics tipus «articles Q1» o «Totes en el 25% superior» **no** s'actualitzen sols: si la composició de publicacions canvia, revisa-los a mà.
- Pages desactivat: la URL pública no està publicada. Per reactivar: renombrar el repo a `Athanor8732.github.io` + activar Pages + actualitzar el remot local.

## SEO i metadades (Fase 4)

`scripts/build_seo.py` afegeix a cada pàgina:
- `<meta name="description">` (descripció específica per pàgina, definida al propi script)
- Open Graph (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `og:locale=ca_ES`)
- Twitter Card (`summary_large_image`)
- `<link rel="canonical">` (URL base: `https://athanor8732.github.io`)
- JSON-LD structured data: `Person` a la home, `ItemList`+`ScholarlyArticle` a publicacions, `ResearchProject` a les pàgines de projecte
- `sitemap.xml` i `robots.txt` a l'arrel

El script és **idempotent** (neteja els tags SEO existents abans d'inserir-los). Per actualitzar les metadades, editar la dict `PAGES` al script i executar-lo.

### Favicons i PWA (Fase 5)
- `img/favicon.svg` — logo SVG (font de veritat)
- `img/favicon.ico` — multi-resolució (16, 32, 48)
- `img/favicon-32x32.png`, `img/favicon-16x16.png` — PNG
- `img/apple-touch-icon.png` — 180×180
- `img/og-image.png` — 1200×630 per Open Graph
- `manifest.json` — PWA bàsica (theme color, icons)
- Totes les pàgines enllacen aquests fitxers al `<head>`

### Accessibilitat (Fase 3)
- Skip-link + `id="main"` a totes les pàgines
- `aria-current="page"` automàtic al nav link de la topbar
- `aria-current="true"` dinàmic a la nav lateral de les pàgines de projecte
- `lang="la"` als noms científics en cursiva
- `prefers-reduced-motion` desactiva totes les animacions
- `:focus-visible` global amb outline cyan

### Normalització de publications.json (Fase 6)
Tots els camps són sempre presents (cap és `null`): `doi`, `authors`, `title`, `journal`, `volume`, `issue`, `pages`, `year`, `jif`, `quartile`, `citations`, `openalexId`, `scopusId`, `issn`, `auto`. Els camps buits són `""` (string buit), no `null`. `update_scholarly_data.py` ara també escriu `scopusId:""` i `issn:""` a les noves entrades automàtiques.

## Memòria entre sessions

Hi ha una memòria de projecte (`project_web_personal_marc_links`) a nivell d'usuari que registra el context no obvi d'aquest repo (decisió OpenAlex vs Scopus, pendent de re-publicar, valors actuals). Si canvien decisions de fons, actualitza-la.