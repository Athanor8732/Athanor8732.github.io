# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Què és això

Web personal estàtic de Marc Cerdà i Domènech (geocientífic marí, UB). HTML/CSS/JS fet a mà, sense framework ni generador de site global — cada pàgina és un `index.html` autosuficient. Repo **públic** (`Athanor8732/Athanor8732.github.io`); publicat a **https://cerdadomenech.cat/** via GitHub Pages (branch `main`, arrel). `athanor8732.github.io` hi continua redirigint.

## Arquitectura (actualitzada agost 2026)

La web abans tenia tot el CSS i JS inline duplicat a cada pàgina (~260 línies × 8). Després de la consolidació i la reestructuració d'agost 2026:

- **`css/styles.css`** — full d'estils base compartit (variables, reset, topbar+nav, gauge, prose, timeline, cards, CTD rig, side-promo, reveal, focus-visible, skip-link, prefers-reduced-motion, print). Carregat per totes les pàgines via `<link>`.
- **`css/fonts.css`** — `@font-face` per Inter (body i títols), self-hosted a `/fonts/*.woff2` (variable font).
- **`js/ctd-rig.js`** — animació del CTD rosette (abans inline a 7 pàgines). Pausa el RAF quan el rig no és visible. Respecta `prefers-reduced-motion`.
- **`js/reveal.js`** — observador de scroll-reveal per als elements `.reveal`.
- **`vendor/leaflet/`** — Leaflet 1.9.4 self-hosted (CSS + JS + imatges), en lloc de CDN unpkg.
- **`templates/`** — partials HTML (`topbar.html`, `ctd-rig.html`, `side-promo.html`, `head.html`) amb marcadors `{DEPTH}`.
- **Cada pàgina** manté només el CSS específic inline (pàgines de projecte: `.pt-card`, `.method-grid`, etc.; home: `.profile`, `.porthole`, `.sonar`, etc.).

### Topbar (dues files)
- **Fila superior**: nom centrat ("Marc Cerdà i Domènech · Geociències Marines") amb logo SVG; hamburger a la dreta (només mòbil, `position:absolute` dins `.topbar-brand-row`).
- **Fila inferior**: nav horitzontal (Sobre mi, Recerca, Publicacions, Docència, Mitjans, Bloc, Contacte) amb `justify-content:space-between` ocupant tot l'ample (`--wrap`, 648px), lletra 0.82rem.
- **Submenus**: Recerca i Docència tenen submenus desplegables (hover a escriptori, tap a mòbil). Estructura: `<div class="nav-item has-submenu"><a>…</a><div class="submenu">…</div></div>`. El JS `hamburger-init` (injectat per `build_pages.py`/`build_blog.py`) gestiona el toggle mòbil amb la classe `.mobile-open`.
- El link de la pàgina actual es marca amb `aria-current="page"` (`build_pages.py` comprova si ja existeix abans d'injectar-lo — mai duplicar).

### Versió anglesa (`/en/`, setembre 2026)
Tota la web existeix en dues llengües: el català a l'arrel i l'anglès sota **`/en/`** (10 pàgines, amb els slugs traduïts: `en/about/`, `en/research/`, `en/publications/`, `en/teaching/`, `en/teaching/resources/`, `en/media/`, `en/contact/`, `en/impas-garraf/`, `en/emicreuer-bcn/`). El **bloc no es tradueix** (articles d'opinió en català): la nav anglesa hi enllaça amb `hreflang="ca"` i un `title` que ho avisa.

- **Font de veritat de la correspondència**: `PAGE_MAP` a `scripts/build_pages.py`. `build_seo.py` l'importa — no duplicar el mapa enlloc.
- **Template**: `templates/topbar.en.html` (nav i slugs en anglès). `build_pages.py` tria el template segons si la ruta comença per `en/`.
- **Selector CA/EN**: marcador `{LANG_SWITCH}` als dos templates; `render_lang_switch()` el pinta amb l'enllaç a la pàgina equivalent (les pàgines sense equivalent van a la portada de l'altra llengua). Estils `.lang-switch` a `styles.css`: a la dreta de la fila del nom, i a l'esquerra en mòbil (el hamburger ocupa la dreta).
- **Àncores traduïdes**: `#research-lines`, `#campaigns`, `#projects`, `#courses`, i a les pàgines de projecte `#overview`, `#scope`, `#methods|#methodology`, `#work-packages`, `#consortium`, `#results`, `#fieldwork`, `#origin`, `#team`.
- **Convencions de traducció**: noms d'institucions en anglès (University of Barcelona, Catalan Water Agency, Institute for Catalan Studies); «professor lector» → *Assistant Professor*; PT→WP, IP→PI, DAS→SGD. **No es tradueixen**: títols reals d'articles, de TFG ni de peces de premsa (a `mitjans`/`media` es mantenen en la llengua original, avisat al subtítol).
- **Números**: en anglès, separador decimal amb punt i milers amb coma (55.6%, 1,249, €199,630). `stats_for_lang()` a `update_scholarly_data.py` fa la conversió automàtica dels camps de stats.

### Cache-busting dels actius
GitHub Pages serveix `css/` i `js/` amb `cache-control: max-age=600`: sense res més, un canvi de CSS no arriba als visitants recurrents (ni a tu mateix mentre revises) fins a 10 minuts després. `build_pages.py` afegeix `?v=<hash md5 curt del fitxer>` als enllaços de `css/fonts.css`, `css/styles.css`, `js/ctd-rig.js`, `js/reveal.js` i `js/publications.js` (`VERSIONED_ASSETS` + `version_assets()`), i `build_blog.py` fa el mateix amb `asset_version()`, que importa de `build_pages`. Si canvies un d'aquests fitxers, **executa `build_pages.py`** perquè el hash es refresqui a totes les pàgines.

### La topbar es resincronitza (no només s'injecta)
`build_pages.py` ja no depèn dels marcadors `<!-- @partial:topbar -->` (es consumeixen a la primera passada). Si la pàgina ja té una topbar injectada, `find_topbar_block()` la localitza per recompte de `<div>`/`</div>` i la **substitueix** pel template renderitzat. Per tant, editar `templates/topbar*.html` + executar `build_pages.py` ara sí que propaga el canvi a totes les pàgines. L'script és idempotent (executar-lo dos cops no canvia res).

### Footer unificat
Totes les pàgines comparteixen el mateix footer: logos UB/GMAR + "← Torna al perfil" + llicència CC BY-NC-SA 4.0. Els estils són globals a `styles.css` (`footer .affil`, `.footer-mark`, `.cc-notice`). No afegir text de font per pàgina.

### Targetes de la portada (substitueixen els side-promos)
El 18-09-2026 es van **eliminar els bàners laterals** (`.side-promos`, fixats a l'esquerra) de les dues portades, i amb ells el template `side-promo.html`, el seu partial a `build_pages.py` i tot el CSS `.side-promo*`. Al seu lloc, la portada porta **dos blocs de targetes en una sola columna** (`.cards`, sense variant en graella):

- **Projectes** — IMPAS-Garraf i EMICREUER-BCN, amb l'etiqueta «Projecte actiu»/«Nou projecte» dins de `.desc`.
- **Perfils** — Sobre mi, ORCID, Scopus, ResearchGate i GitHub.

Reutilitza el component `.card` global (el mateix de «Perfil a bases de dades» a sobre-mi), amb un modificador de color per targeta (`c-gold` es va afegir per a ResearchGate). Una columna, mai dues: es va provar `.cards.grid-2` el 18-09-2026 i es va descartar. La selecció és **curada a propòsit**: no repeteix seccions de la topbar més enllà de Sobre mi.

### Skip-link i accessibilitat
Cada pàgina té `<a class="skip-link" href="#main">` i `<div class="wrap" id="main">`. Focus-visible global. `prefers-reduced-motion` desactiva totes les animacions (inclosos rigs DAS/liner dels projectes). `@media print` amaga rigs, side-promos i nav vertical.

## Reestructuració de contingut (agost 2026)

Decisions estructurals aplicades — no reintroduir els blocs eliminats:

- **Home**: portal d'entrada (profile+porthole amb la frase `.pitch`, gauge data-driven, bio, quote, graella `.cards.grid-2` «Projectes i perfils», últim article, subscribe). ❌ SENSE franja de fotos ni llista d'articles secundaris: es van provar el 18-09-2026 i es van descartar. ❌ SENSE "Perfil investigador" (mogut a sobre-mi) ni "Contacte i detalls" (duplicava contacte) ni "Afiliació" (al footer) ni la secció de cards "Seccions" (redundant amb la topbar).
- **Sobre mi**: bio llarga (el Premi Carmina Virgili s'hi explica dins del tercer paràgraf; ❌ **sense bàner `.award`**, que només va a recerca), timelines Formació/Trajectòria, i secció **"Perfil a bases de dades"** (ORCID, ResearchGate, Scopus, GitHub). ❌ SENSE secció "Docència" (duplicava la pàgina; l'enllaç va al cta-row).
- **Docència**: stats amb el patró global **`.gauge`** (mai `.teach-stats`, eliminat).
- **Projectes** (impas-garraf, emicreuer-bcn): estructura pròpia rica (hero, nav vertical scroll-spy, mapes Leaflet); footer unificat sense logos duplicats (la banda `.affil-title` temàtica ja els porta).

## Subagents OpenCode (`.opencode/agents/`)

Dos subagents de revisió, mode `subagent`, `edit: deny` (només llegeixen i proposen):

- **`redaccio`** — revisa gramàtica, concisió, to (seriós però atractiu), coherència terminològica i anglicismes del text català. Mai no modifica dades factuals (nombres, dates, noms, DOIs).
- **`disseny`** — audita sistema de disseny, coherència entre pàgines, jerarquia tipogràfica, espaiat, color/contrast WCAG i responsivitat. Respecta el tema submarí (no redissenyar paleta ni identitat). No inclou figures ni dades.

Invocació: `task(prompt="...", subagent_type="...")`. Cal reiniciar opencode perquè els detecti si es modifiquen.

Convencions visuals derivades de l'auditoria: usar sempre `var(--sans)` (mai `Georgia,serif` directe), variables de color amb triplet `-rgb` a `:root` (`--coral-rgb`, `--sand-rgb`, `--gold-rgb`, `--indigo-rgb`, `--karst(-rgb)`, `--cyan-rgb`), grids de projecte col·lapsen a 1 columna <640px, microtextos amb opacity ≥0.85 sobre `--muted` (contrast AA).

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

Reinjectar/resincronitzar partials HTML a totes les pàgines, catalanes i angleses (després d'editar `templates/`):
```bash
python3 scripts/build_pages.py            # processa totes les pàgines
python3 scripts/build_pages.py --check    # dry-run
```

**Ordre dels scripts.** `build_blog.py` regenera `blog/index.html` des de zero i, en fer-ho, n'esborra els tags SEO; `build_pages.py` versiona els actius i resincronitza topbars. Quan n'executis més d'un, fes-ho sempre en aquest ordre:

```bash
python3 scripts/build_blog.py && python3 scripts/build_pages.py && python3 scripts/build_seo.py
```

No hi ha build global, ni tests, ni linter. Els scripts són stdlib-only (cap `pip install`).

## Arquitectura

### Pàgines
Cada secció és un directori amb `index.html`: `index.html` (home), `sobre-mi/`, `recerca/`, `publicacions/`, `docencia/`, `docencia/recursos-docents/`, `mitjans/`, `contacte/`, `blog/` (generat), `impas-garraf/`, `emicreuer-bcn/`. Tots comparteixen el tema submarí (fons negre, accent `#39ffb0`, tipografia Inter) definit a `css/styles.css`. El CSS específic de cada pàgina es manté inline al seu `<style>`.

### Stats data-driven (bloc inline `#stats-inline` + `update_scholarly_data.py`)
Qualsevol element `<... data-stat="KEY">` s'omple en runtime des d'un bloc JS inline (`<script id="stats-inline">`) que `update_scholarly_data.py` escriu directament al HTML de les 6 pàgines amb gauge (home, recerca i publicacions, i les tres equivalents angleses). El valor que hi ha a l'HTML entre les etiquetes és el **fallback estàtic** (es mostra sense JS). Convenció: el fallback ha de ser un valor realista, no un placeholder.

No hi ha `fetch` ni fitxer extern `stats.js` — tot el codi i les dades van inline al HTML, de manera que el navegador no pot cachar cap fitxer per separat. `data/stats.json` es manté al repo com a font de dades pel workflow, però no es consumeix al runtime.

`stats.json` barreja dos origens:
- **Camps automàtics** (els escriu `update_scholarly_data.py`): `publications`, `citations`, `hIndex`, `updated`, `source`.
- **Camps manuals** (del CV, l'script **no els toca** — definit a `MANUAL_STATS`): `projects`, `campaigns`, `campaignsDetailed`, `seaDays`, `intlCoauthorship`, `researchLines`, `researchLinesLabel`, `citeScoreTop`, i les variants angleses `researchLinesLabel_en` i `source_en`. Aquests s'editen a mà.

El bloc `#stats-inline` s'inclou a les **6 pàgines amb gauge**: `index.html`, `recerca/index.html`, `publicacions/index.html` i les tres equivalents de `/en/`. Tot el codi i les dades van inline — no hi ha `fetch` ni fitxer extern. A les pàgines angleses el bloc porta els valors passats per `stats_for_lang()`: les claus amb sufix `_en` de `stats.json` (`researchLinesLabel_en`, `source_en`) substitueixen les catalanes i la coma decimal passa a punt.

### Publicacions data-driven (`data/publications.json` + `js/publications.js`)
`publicacions/index.html` i `en/publications/index.html` tenen una llista `<div class="pub-list">` que `js/publications.js` substitueix en runtime per les targetes del JSON. El JS mira `document.documentElement.lang`: en anglès, etiqueta «cited by:» (en comptes de «cites:») i JIF amb punt decimal. El bloc `.pub-list` del HTML és **fallback estàtic** i, a diferència dels stats, **és regenerat automàticament per `update_scholarly_data.py`** (mateix format que el JS). No l'editis a mà: els canvis van a `publications.json` i es propaguen executant l'script.

### Portada: el darrer article es genera
El bloc de l'últim article viu entre els marcadors `<!-- @blog-highlights:start|end -->` de `index.html` i `en/index.html` i el genera **`build_blog.py`** a partir dels Markdown (`HIGHLIGHT_EXTRA` articles compactes addicionals; **0** = només el destacat, que és com ha de quedar). Abans estava escrit a mà i calia recordar-se'n a cada article nou. **No editar-lo a mà**: es regenera.

### Dependències de `cerdadomenech.blog` (caduca cap a l'abril del 2027)
El bloc antic de WordPress i el seu domini desapareixen cap a l'abril del 2027. La web **ja no en carrega cap imatge** (les quatre de recerca es van baixar a `img/recerca/` el 18-09-2026) i els cinc articles hi són tots. Només hi queden **3 enllaços de cortesia** («llegeix l'original a…») als `source_url` de `recuperar-sobiranies`, `salvador-illa-politiques-climatiques` i `empremta-climatica-ia`. Quan el domini caduqui, cal repuntar-los al mitjà original (Espai Fàbrica, Línia Xarxa) o treure'ls del frontmatter. `render_post()` treu el nom del mitjà de la pròpia URL, així que canviar el `source_url` ja canvia l'etiqueta.

### Feed RSS (`feed.xml`)
`build_blog.py` genera `feed.xml` a l'arrel a partir dels mateixos Markdown (RSS 2.0, `SITE_URL` al mateix script). És **la via de subscripció del lloc**: el bloc de WordPress (`cerdadomenech.blog`) i la seva llista de correu desapareixen amb aquell domini, així que la portada ja no promet correu — ofereix llegir el bloc i subscriure-s'hi per RSS. L'enllaç `<link rel="alternate" type="application/rss+xml">` del `<head>` el manté `ensure_feed_link()` de `build_pages.py` a les 24 pàgines (el template `head.html` sol no bastaria: els marcadors `@partial:head` es van consumir fa temps).

### Bloc (`content/posts/*.md` → `scripts/build_blog.py`)
Els articles viuen com a Markdown amb frontmatter a `content/posts/YYYY-MM-DD-slug.md`. Camps del frontmatter: `title`, `slug`, `date`, `date_display`, `excerpt`, `image`, `image_alt`, `source_url`, `source_note`, i els **opcionals `title_en` i `excerpt_en`**, que només fa servir la portada anglesa per explicar de què va l'article (els articles no es tradueixen). Si no hi són, la portada anglesa cau al títol i l'entradeta en català. Al cos, els paràgrafs separats per línia en blanc esdevenen `<p>`; una línia que comenci per `> ` es renderitza com a `<blockquote>`. `build_blog.py` regenera `blog/index.html` i `blog/<slug>/index.html`. No hi ha fallback estàtic del bloc — cal executar l'script per veure els canvis.

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

El workflow fa commit de 8 fitxers —`data/stats.json`, `data/publications.json` i les 6 pàgines amb gauge (3 catalanes + 3 angleses)— amb el bot `github-actions[bot]`, i és **idempotent** (no commita si no hi ha diff).

### Convenis i gotchas
- `norm(s)` translitera diacritics via `unicodedata.normalize("NFKD")` + eliminar combining marks, perquè `Cerdà`→`cerda` (no `cerd`). No fer servir un regex directe sobre la cadena accentuada.
- Els JIF s'escriuen amb **coma decimal** (`"10,0"`, `"2,6"`) seguint el format del CV.
- `intlCoauthorship` (55,6%) és un camp manual del CV derivat de Scopus; a `recerca/index.html` va etiquetat `(Scopus)`, no prové d'OpenAlex.
- Els claims estàtics tipus «articles Q1» o «Totes en el 25% superior» **no** s'actualitzen sols: si la composició de publicacions canvia, revisa-los a mà.
- Publicació: el repo és `Athanor8732.github.io` (públic) i Pages serveix la branch `main` a https://cerdadomenech.cat/. Cada push a `main` es publica sol (build ~1 min).

## SEO i metadades (Fase 4)

`scripts/build_seo.py` afegeix a cada pàgina:
- `<meta name="description">` (descripció específica per pàgina, definida al propi script)
- Open Graph (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `og:locale=ca_ES`)
- Twitter Card (`summary_large_image`)
- `<link rel="canonical">` (URL base: `https://cerdadomenech.cat`, a `BASE_URL`)
- JSON-LD structured data: `Person` a la home, `ItemList`+`ScholarlyArticle` a publicacions, `ResearchProject` a les pàgines de projecte
- `<link rel="alternate" hreflang="ca|en|x-default">` a cada parella CA/EN i `og:locale:alternate`
- `sitemap.xml` (21 URLs: 11 catalanes + 10 angleses) i `robots.txt` a l'arrel

El script és **idempotent** (neteja els tags SEO existents abans d'inserir-los). Per actualitzar les metadades, editar la dict `PAGES` al script i executar-lo.

### Pes de les imatges (optimització 18-09-2026)
Les fotografies es guarden **a 1300px d'ample com a màxim** (la columna de contingut fa 648px, el doble per a pantalles retina) i en JPEG de qualitat 82; les d'article, a 1000px. `img/marc.jpg` (400×400, 19 KB) és la foto del perfil que carrega la portada — es mostra a 112px; `img/marc.png` (900×900) es conserva **només** com a `og:image` per a les previsualitzacions socials, i cap pàgina no la carrega. Amb això la portada va de 508 KB a **125 KB**. Si hi afegeixes fotos noves, passa-les per la mateixa mida i qualitat.

### Favicons i PWA (Fase 5)
- `img/favicon.svg` — logo SVG (font de veritat)
- `img/favicon.ico` — multi-resolució (16, 32, 48)
- `img/favicon-32x32.png`, `img/favicon-16x16.png` — PNG
- `img/apple-touch-icon.png` — 180×180
- `img/og-image.png` — 1200×630 per Open Graph
- `manifest.json` — PWA bàsica (theme color, icons)
- Totes les pàgines enllacen aquests fitxers al `<head>`

### Accessibilitat (Fase 3 + auditoria agost 2026)
- Skip-link + `id="main"` a totes les pàgines
- `aria-current="page"` automàtic al nav link de la topbar (mai duplicat — `build_pages.py` el deduplica)
- `aria-current="true"` dinàmic a la nav lateral de les pàgines de projecte
- `lang="la"` als noms científics en cursiva
- `prefers-reduced-motion` desactiva totes les animacions, inclosos els rigs DAS (impas-garraf) i liner (emicreuer-bcn)
- `:focus-visible` global amb outline cyan
- Contrast AA: microtextos (`hero-credit`, `nav-label`) amb opacity ≥0.85 sobre `--muted`
- Grids de projecte col·lapsen a 1 columna <640px; breakpoints principals: 880/680/640/520

### Normalització de publications.json (Fase 6)
Tots els camps són sempre presents (cap és `null`): `doi`, `authors`, `title`, `journal`, `volume`, `issue`, `pages`, `year`, `jif`, `quartile`, `citations`, `openalexId`, `scopusId`, `issn`, `auto`. Els camps buits són `""` (string buit), no `null`. `update_scholarly_data.py` ara també escriu `scopusId:""` i `issn:""` a les noves entrades automàtiques.

## Publicació

- **URL pública**: https://cerdadomenech.cat/ (GitHub Pages, branch `main`, arrel). Domini propi des del 18-09-2026, registrat a DonDominio; `athanor8732.github.io` hi redirigeix i cap enllaç antic es trenca.
- **El fitxer `CNAME`** de l'arrel (una línia: `cerdadomenech.cat`) el va crear GitHub en desar el domini a Settings → Pages i és el que lliga el domini amb el repo. **No esborrar-lo mai**: sense ell, Pages torna a servir només a `athanor8732.github.io`. Cap script de build el toca (només processen `.html`, `.css`, `.js` i `.json`).
- Cada `git push` a `main` es publica automàticament (~1 min de build). Verificar amb `gh api repos/Athanor8732/Athanor8732.github.io/pages -q .status`.
- Previsualització local abans de pujar: `python3 -m http.server 8000 --bind 127.0.0.1`.
- El repo va canviar de nom de `marc-links` a `Athanor8732.github.io` (agost 2026) i és públic; el remot local ja apunta al nou nom.

## Memòria entre sessions

Hi ha una memòria de projecte (`project_web_personal_marc_links`) a nivell d'usuari que registra el context no obvi d'aquest repo (decisió OpenAlex vs Scopus, valors actuals). Si canvien decisions de fons, actualitza-la.