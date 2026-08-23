# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Què és això

Web personal estàtic de Marc Cerdà i Domènech (geocientífic marí, UB). HTML/CSS/JS fet a mà, sense framework ni generador de site global — cada pàgina és un `index.html` autosuficient amb el CSS inline. Repo **privat** (`Athanor8732/marc-links`); GitHub Pages **desactivat** per decisió (pendent de re-publicar com a `Athanor8732.github.io` quan la versió estigui acabada).

## Comandes

Previsualització local (servidor estàtic):
```bash
python3 -m http.server 8000 --bind 127.0.0.1   # http://127.0.0.1:8000/
```

Generar el bloc des del Markdown (veure més avall):
```bash
python3 scripts/build_blog.py
```

Actualitzar dades científiques des d'OpenAlex (es pot executar a mà; el workflow ho fa setmanalment):
```bash
python3 scripts/update_scholarly_data.py   # opcional: MAILTO=correu@example.org
```

No hi ha build global, ni tests, ni linter. Els dos scripts són stdlib-only (cap `pip install`).

## Arquitectura

### Pàgines
Cada secció és un directori amb `index.html`: `index.html` (home), `sobre-mi/`, `recerca/`, `publicacions/`, `docencia/`, `premsa/`, `contacte/`, `blog/`, `impas-garraf/`, `emicreuer-bcn/`. Tots comparteixen el tema submarí (fons negre, accent `#39ffb0`, tipografia Georgia pels títols) definit amb les mateixes variables CSS arrel, replicades inline a cada fitxer. No hi ha full d'estils compartit: el CSS es reescriu (o s'importa) a cada pàgina.

### Stats data-driven (`data/stats.json` + `js/stats.js`)
Qualsevol element `<... data-stat="KEY">` s'omple en runtime des de `data/stats.json` (fetch + `textContent`). El valor que hi ha a l'HTML entre les etiquetes és el **fallback estàtic** (es mostra sense JS o si falla el fetch). Convenció: el fallback ha de ser un valor realista, no un placeholder.

`stats.json` barreja dos origens:
- **Camps automàtics** (els escriu `update_scholarly_data.py`): `publications`, `citations`, `hIndex`, `updated`, `source`.
- **Camps manuals** (del CV, l'script **no els toca** — definit a `MANUAL_STATS`): `projects`, `campaigns`, `campaignsDetailed`, `seaDays`, `intlCoauthorship`, `researchLines`, `researchLinesLabel`, `citeScoreTop`. Aquests s'editen a mà.

`js/stats.js` s'inclou a `index.html`, `recerca/index.html` i `publicacions/index.html` (les pàgines amb gauge).

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

## Memòria entre sessions

Hi ha una memòria de projecte (`project_web_personal_marc_links`) a nivell d'usuari que registra el context no obvi d'aquest repo (decisió OpenAlex vs Scopus, pendent de re-publicar, valors actuals). Si canvien decisions de fons, actualitza-la.