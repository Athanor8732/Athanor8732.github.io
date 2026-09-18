#!/usr/bin/env python3
"""Actualitza les dades científiques de la web des d'OpenAlex.

OpenAlex és una font oberta i lliure (sense clau API) que es pot consultar
des de qualsevol IP, inclosos els runners de GitHub Actions.

Consultes:
  - Author  -> h-index, cited_by_count i works_count globals de l'autor
  - Works   -> llista d'obres atribuïdes a l'autor (articles/reviews amb DOI)

Estratègia de merge (híbrid curat + automàtic):
  - data/publications.json és un seed curat (llistes d'autors, JIF i quartil
    revisats manualment a partir del CV). OpenAlex només hi afegeix:
      * recompte de cites actualitzat (cited_by_count) per als DOI existents
      * publicacions noves no presents al seed (amb autors i dades d'OpenAlex)
  - data/stats.json: s'actualitzen només els camps automàtics
    (publications, citations, hIndex, updated, source); els manuals es respecten.

Ús:
  python3 scripts/update_scholarly_data.py
  # opcional (polic pool d'OpenAlex): MAILTO=el-teu@correu.cat
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

# ---- Configuració ----
AUTHOR_ID = "A5002623148"              # OpenAlex author id (Marc Cerdà-Domènech)
ALLOWED_TYPES = {"article", "review"}  # tipus d'obra que compten com a publicació
EXCLUDE_DOIS = set()                   # DOIs a ignorar (homònims, errades, etc.)
BASE = "https://api.openalex.org"
MAILTO = os.environ.get("MAILTO", "").strip()  # recomanat per al polite pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_PATH = os.path.join(ROOT, "data", "stats.json")
PUBS_PATH = os.path.join(ROOT, "data", "publications.json")

# Camps de stats.json que l'script no toca (valors manuals del CV).
MANUAL_STATS = {
    "projects", "campaigns", "campaignsDetailed", "seaDays",
    "intlCoauthorship", "researchLines", "researchLinesLabel", "citeScoreTop",
    # Variants angleses (les fan servir les pàgines de /en/); vegeu stats_for_lang()
    "researchLinesLabel_en", "source_en",
}


def _q():
    return f"mailto={urllib.parse.quote(MAILTO)}&" if MAILTO else ""


def get(url, tries=3):
    """GET JSON amb reintent i backoff. Inclou el cos de l'error HTTP."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            last = RuntimeError(f"HTTP {e.code} a {url}: {body[:400]}")
            if e.code in (401, 403, 404):
                raise last
            time.sleep(1.0 * (i + 1))
        except Exception as e:  # xarxa, timeout...
            last = e
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"no s'ha pogut obtenir {url}: {last}")


def norm_doi(doi):
    if not doi:
        return ""
    d = doi.strip().lower()
    for p in ("https://doi.org/", "http://doi.org/"):
        if d.startswith(p):
            d = d[len(p):]
    return d


def norm(s):
    """Normalitza per comparar: minúscules, sense diacrítics ni separadors."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s)


def today():
    return date.today().isoformat()


# ---- API OpenAlex ----
def author_metrics():
    data = get(f"{BASE}/authors/{AUTHOR_ID}?{_q()}")
    name = data.get("display_name", "")
    if "cerda" not in norm(name):
        print(f"  AVÍS: el perfil d'OpenAlex és «{name}» (comprova l'ID).", file=sys.stderr)
    ss = data.get("summary_stats", {}) or {}
    return {
        "hIndex": int(ss.get("h_index", 0) or 0),
        "citations": int(data.get("cited_by_count", 0) or 0),
        "works": int(data.get("works_count", 0) or 0),
    }


def author_works():
    """Totes les obres de l'autor (paginació per cursor)."""
    fields = ("id,doi,title,publication_year,publication_date,cited_by_count,"
              "type,primary_location,biblio,authorships")
    works = []
    cursor = "*"
    while True:
        url = (f"{BASE}/works?filter=author.id:{AUTHOR_ID}&per-page=200"
               f"&sort=publication_date:desc&select={fields}&cursor={cursor}&{_q()}")
        data = get(url)
        results = data.get("results", []) or []
        works.extend(results)
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not results:
            break
        time.sleep(0.2)
    return works


def format_authors(authorships):
    """Llista d'autors (raw_author_name) amb l'autor objectiu en negreta."""
    if not authorships:
        return ""
    parts = []
    for a in authorships:
        name = a.get("raw_author_name") or (a.get("author", {}) or {}).get("display_name", "") or ""
        if not name:
            continue
        aid = ((a.get("author", {}) or {}).get("id", "") or "")
        if AUTHOR_ID in aid or "cerda" in norm(name):
            name = f"<b>{name}</b>"
        parts.append(name)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " & " + parts[-1]


def pages_str(biblio):
    biblio = biblio or {}
    fp = (biblio.get("first_page") or "").strip()
    lp = (biblio.get("last_page") or "").strip()
    if fp and lp and fp != lp:
        return f"{fp}-{lp}"
    return fp or lp


# ---- Fallback estàtic de la llista de publicacions ----
# Regenera el bloc <div class="pub-list">...</div> de publicacions/index.html
# a partir del JSON, perquè la pàgina es vegi correcta fins i tot sense JS
# (o si falla el fetch). El format replica exactament el que pinta js/publications.js.
PUBS_HTML = os.path.join(ROOT, "publicacions", "index.html")
PUBS_HTML_PAGES = [
    (PUBS_HTML, "ca"),
    (os.path.join(ROOT, "en", "publications", "index.html"), "en"),
]


def hesc(s):
    """Escapa HTML per a text (no per a authors, que és HTML curat)."""
    return (str(s) if s is not None else "").replace("&", "&amp;") \
        .replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_static_card(p, lang="ca"):
    journal = hesc(p.get("journal", ""))
    vol = p.get("volume", "") or ""
    issue = p.get("issue", "") or ""
    pages = p.get("pages", "") or ""
    jline = "<b>" + journal + "</b>"
    if vol:
        jline += ", " + hesc(vol)
    if issue:
        jline += "(" + hesc(issue) + ")"
    if pages:
        jline += ", " + hesc(pages)
    year = hesc(p.get("year", ""))
    jif = p.get("jif", "") or ""
    if lang == "en":
        jif = jif.replace(",", ".")
    quartile = p.get("quartile", "") or ""
    q = ""
    if jif and quartile:
        q = "JIF " + hesc(jif) + " · " + hesc(quartile)
    elif quartile:
        q = hesc(quartile)
    elif jif:
        q = "JIF " + hesc(jif)
    cites = hesc(p.get("citations", 0))
    doi = (p.get("doi", "") or "").strip()
    out = [
        '      <div class="pub-card">',
        '        <p class="authors">' + (p.get("authors", "") or "") + '</p>',
        '        <p class="title">' + hesc(p.get("title", "")) + '</p>',
        '        <div class="meta">',
        '          <span>' + jline + '</span>',
    ]
    qspan = '<span>' + q + '</span>' if q else ''
    cited_label = "cited by: " if lang == "en" else "cites: "
    out.append('          <span>' + year + '</span>' + qspan + '<span>' + cited_label + cites + '</span>')
    if doi:
        out.append('          <a class="doi" href="https://doi.org/' + hesc(doi) +
                   '" target="_blank" rel="noopener">DOI →</a>')
    out.append('        </div>')
    out.append('      </div>')
    return "\n".join(out)


def stats_for_lang(stats, lang):
    """Stats per a una llengua: aplica les claus X_en i passa la coma decimal a punt."""
    out = {k: v for k, v in stats.items() if not k.endswith("_en")}
    if lang != "en":
        return out
    for k, v in stats.items():
        if k.endswith("_en"):
            out[k[:-3]] = v
    # 55,6% → 55.6% (separador decimal anglès)
    for k, v in list(out.items()):
        if isinstance(v, str) and re.fullmatch(r"\d+,\d+%?", v):
            out[k] = v.replace(",", ".")
    return out


def update_publications_html(pubs):
    """Torna a generar el bloc .pub-list de la pàgina catalana i de l'anglesa."""
    for path, lang in PUBS_HTML_PAGES:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        cards = "\n\n".join(render_static_card(p, lang) for p in pubs)
        block = '<div class="pub-list">\n\n' + cards + '\n\n    </div>'
        pattern = re.compile(r'<div class="pub-list">.*?\n    </div>', re.DOTALL)
        new_html, n = pattern.subn(lambda m: block, html, count=1)
        rel = os.path.relpath(path, ROOT)
        if n != 1:
            print(f"  AVÍS: no s'ha trobat el bloc .pub-list a {rel} "
                  "(no s'ha modificat el HTML).", file=sys.stderr)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"    HTML: regenerades {len(pubs)} targetes a {rel}")


# Pàgines amb gauge de stats: s'hi refresquen els valors de fallback (sense JS).
GAUGE_HTML = [
    (os.path.join(ROOT, "index.html"), "ca"),
    (os.path.join(ROOT, "recerca", "index.html"), "ca"),
    (os.path.join(ROOT, "publicacions", "index.html"), "ca"),
    (os.path.join(ROOT, "en", "index.html"), "en"),
    (os.path.join(ROOT, "en", "research", "index.html"), "en"),
    (os.path.join(ROOT, "en", "publications", "index.html"), "en"),
]
# Camps automàtics que apareixen com a fallback numèric al gauge.
GAUGE_KEYS = ("publications", "citations", "hIndex")


def update_gauge_fallbacks(stats):
    """Actualitza els valors de fallback del gauge i el bloc inline de stats a les 3 pàgines."""
    changed = 0
    for path, lang in GAUGE_HTML:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        lang_stats = stats_for_lang(stats, lang)

        def repl(m, lang_stats=lang_stats):
            key = m.group(1)
            val = lang_stats.get(key, m.group(2))
            return f'data-stat="{key}">{val}<'

        new_html, n = re.subn(
            r'data-stat="(publications|citations|hIndex)">([^<]*)<', repl, html)

        # Bloc inline únic: JSON + codi JS en un sol <script>
        stats_json = json.dumps(lang_stats, ensure_ascii=False)
        inline_block = (
            '<script id="stats-inline">\n'
            '  (function () {\n'
            '    var stats = ' + stats_json + ';\n'
            '    document.querySelectorAll("[data-stat]").forEach(function (el) {\n'
            '      var key = el.getAttribute("data-stat");\n'
            '      if (stats[key] !== undefined) el.textContent = stats[key];\n'
            '    });\n'
            '  })();\n'
            '</script>\n  '
        )
        if '<script id="stats-inline">' in new_html:
            new_html = re.sub(
                r'<script id="stats-inline">.*?</script>\s*',
                inline_block, new_html, flags=re.S)
        else:
            # Elimina etiquetes antiques (stats-data blob + stats.js extern)
            new_html = re.sub(
                r'<script type="application/json" id="stats-data">.*?</script>\s*', '', new_html, flags=re.S)
            new_html = re.sub(r'<script src="js/stats\.js"[^>]*></script>\s*', '', new_html)
            new_html = re.sub(r'<script src="\.\./js/stats\.js"[^>]*></script>\s*', '', new_html)
            # Insereix el bloc inline abans del primer <script src que quedi (ctd-rig.js, etc.)
            m2 = re.search(r'<script src="', new_html)
            if m2:
                pos = m2.start()
                new_html = new_html[:pos] + inline_block + new_html[pos:]
            else:
                new_html = new_html.replace('</body>', inline_block + '</body>', 1)

        if n and new_html != html:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_html)
            changed += n
    if changed:
        print(f"    HTML: refrescats {changed} fallbacks de gauge "
              "(publications/citations/hIndex)")


# ---- Merge ----
def main():
    print(">>> Mètriques globals de l'autor (OpenAlex)...")
    m = author_metrics()
    print(f"    h-index={m['hIndex']}  cites={m['citations']}  obres={m['works']}")

    print(">>> Obres de l'autor...")
    works = author_works()
    print(f"    {len(works)} obres trobades")

    # Seed curat
    seed = {"publications": []}
    if os.path.exists(PUBS_PATH):
        with open(PUBS_PATH, encoding="utf-8") as f:
            seed = json.load(f)
    by_doi = {}
    no_doi_seed = []
    for p in seed.get("publications", []):
        d = norm_doi(p.get("doi"))
        if d:
            by_doi[d] = dict(p)
        else:
            no_doi_seed.append(dict(p))

    new_entries = []
    seen = set(by_doi)
    for w in works:
        doi = norm_doi(w.get("doi"))
        wtype = w.get("type", "") or ""
        if doi and doi in by_doi:
            # Actualitza cites; la resta és curada
            by_doi[doi]["citations"] = int(w.get("cited_by_count", 0) or 0)
            continue
        if not doi or wtype not in ALLOWED_TYPES or doi in EXCLUDE_DOIS or doi in seen:
            continue
        # Publicació nova no present al seed
        pl = w.get("primary_location") or {}
        src = pl.get("source") or {}
        biblio = w.get("biblio") or {}
        entry = {
            "doi": w.get("doi", "").replace("https://doi.org/", "").replace("http://doi.org/", ""),
            "authors": format_authors(w.get("authorships") or []),
            "title": w.get("title", "") or "",
            "journal": src.get("display_name", "") or "",
            "volume": (biblio.get("volume") or "").strip(),
            "issue": (biblio.get("issue") or "").strip(),
            "pages": pages_str(biblio),
            "year": int(w.get("publication_year", 0) or 0),
            "jif": "",
            "quartile": "—",   # OpenAlex no aporta quartil: es cura manualment
            "citations": int(w.get("cited_by_count", 0) or 0),
            "openalexId": (w.get("id", "") or "").replace("https://openalex.org/", ""),
            "scopusId": "",
            "issn": "",
            "auto": True,
        }
        new_entries.append(entry)
        seen.add(doi)
        print(f"    + NOVA: {entry['title'][:75]} ({entry['year']})")

    merged = list(by_doi.values()) + no_doi_seed + new_entries
    merged.sort(key=lambda p: (p.get("year", 0), str(p.get("doi"))), reverse=True)

    # Escriu publications.json
    out_pubs = {"updated": today(), "publications": merged}
    with open(PUBS_PATH, "w", encoding="utf-8") as f:
        json.dump(out_pubs, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Regenera el fallback estàtic de la llista a publicacions/index.html
    update_publications_html(merged)

    # Actualitza stats.json (només camps automàtics)
    stats = {}
    if os.path.exists(STATS_PATH):
        with open(STATS_PATH, encoding="utf-8") as f:
            stats = json.load(f)
    stats["publications"] = len(merged)
    stats["citations"] = m["citations"]
    stats["hIndex"] = m["hIndex"]
    stats["updated"] = today()
    stats["source"] = "OpenAlex (autor A5002623148), complementat amb el currículum AQU Catalunya"
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Refresca els valors de fallback del gauge a les 3 pàgines
    update_gauge_fallbacks(stats)

    print(f"<<< Fet. Publicacions: {len(merged)} (noves: {len(new_entries)}). "
          f"stats -> pubs={len(merged)} cites={m['citations']} h={m['hIndex']}")


if __name__ == "__main__":
    main()