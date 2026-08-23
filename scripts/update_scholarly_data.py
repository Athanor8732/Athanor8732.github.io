#!/usr/bin/env python3
"""Actualitza les dades científiques de la web des de Scopus.

Consultes a les API d'Elsevier:
  - Author Retrieval   -> h-index i cited-by-count globals de l'autor
  - Scopus Search      -> llista de documents atribuïts a l'autor
  - Abstract Retrieval -> llista d'autors de les publicacions noves
  - Serial Title       -> quartil CiteScore de les revistes noves

Estratègia de merge (hibrid curat + automàtic):
  - data/publications.json és un seed curat (llistes d'autors, JIF, quartil
    revisats manualment a partir del CV). Scopus només hi afegeix:
      * recompte de cites actualitzat (citedby-count) per als DOI existents
      * publicacions noves no presents al seed (amb autors i quartil de Scopus)
  - data/stats.json: s'actualitzen només els camps automàtics
    (publications, citations, hIndex, updated, source); els manuals es respecten.

Ús:
  SCOPUS_API_KEY=... [SCOPUS_INSTTOKEN=...] python3 scripts/update_scholarly_data.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

# ---- Configuració ----
AUTHOR_ID = "57193928271"
ALLOWED_SUBTYPES = {"ar", "re"}        # Article, Review (els que compten com a publicació)
EXCLUDE_DOIS = set()                   # DOIs a ignorar (homònims, errades, etc.)
BASE = "https://api.elsevier.com"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_PATH = os.path.join(ROOT, "data", "stats.json")
PUBS_PATH = os.path.join(ROOT, "data", "publications.json")

API_KEY = os.environ.get("SCOPUS_API_KEY", "").strip()
INST_TOKEN = os.environ.get("SCOPUS_INSTTOKEN", "").strip()
if not API_KEY:
    print("ERROR: falta la variable d'entorn SCOPUS_API_KEY", file=sys.stderr)
    sys.exit(2)

# Camps de stats.json que l'script no toca (valors manuals del CV).
MANUAL_STATS = {
    "projects", "campaigns", "campaignsDetailed", "seaDays",
    "intlCoauthorship", "researchLines", "researchLinesLabel", "citeScoreTop",
}


def _headers():
    h = {"Accept": "application/json", "X-ELS-APIKey": API_KEY}
    if INST_TOKEN:
        h["X-ELS-InstToken"] = INST_TOKEN
    return h


def get(url, tries=3):
    """GET JSON amb reintent i backoff."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # xarxa, 429, 5xx...
            last = e
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"no s'ha pogut obtenir {url}: {last}")


def norm_doi(doi):
    if not doi:
        return ""
    d = doi.strip().lower()
    return d.replace("https://doi.org/", "").replace("http://doi.org/", "")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def today():
    return date.today().isoformat()


# ---- API Scopus ----
def author_metrics():
    data = get(f"{BASE}/content/author/?author_id={AUTHOR_ID}")
    prof = data.get("author-retrieval-profile", [])
    if not prof:
        raise RuntimeError("perfil d'autor buit")
    cd = prof[0].get("coredata", {})
    return {
        "hIndex": int(cd.get("h-index", 0) or 0),
        "citations": int(cd.get("cited-by-count", 0) or 0),
        "docCount": int(cd.get("document-count", 0) or 0),
    }


def scopus_docs():
    """Tots els documents de l'autor (paginat)."""
    docs = []
    start = 0
    q = urllib.parse.quote(f"AU-ID({AUTHOR_ID})")
    fields = ("dc:creator,dc:title,prism:publicationName,prism:volume,"
              "prism:issueIdentifier,prism:pageRange,prism:coverDate,prism:doi,"
              "citedby-count,prism:issn,prism:eIssn,subtype,subtypeDescription")
    while True:
        url = (f"{BASE}/content/search/scopus?query={q}&sort=-coverDate"
               f"&count=25&start={start}&fields={fields}")
        data = get(url)
        sr = data.get("search-results", {})
        total = int(sr.get("opensearch:totalResults", 0) or 0)
        entries = sr.get("entry", [])
        if not entries:
            break
        if isinstance(entries, dict):
            entries = [entries]
        docs.extend(entries)
        start += len(entries)
        if start >= total or not entries:
            break
        time.sleep(0.4)
    return docs


def abstract_authors(scopus_id):
    """Llista d'autors formatada ("Surname, F. I.") amb l'autor objectiu en negreta."""
    if not scopus_id:
        return None
    try:
        data = get(f"{BASE}/content/abstract/scopus_id/{scopus_id}")
    except Exception:
        return None
    resp = data.get("abstracts-retrieval-response", {})
    auth = resp.get("authors", {}).get("author", [])
    if isinstance(auth, dict):
        auth = [auth]
    parts = []
    for a in auth:
        sn = a.get("ce:surname") or ""
        gn = a.get("ce:given-name") or ""
        if not sn:
            pn = a.get("preferred-name", {})
            sn = pn.get("ce:surname", "")
            gn = gn or pn.get("ce:given-name", "")
        initials = " ".join(w[0].upper() + "." for w in gn.split() if w)
        name = f"{sn}, {initials}" if initials else sn
        if str(a.get("@auid", "")) == AUTHOR_ID or "cerda" in norm(sn):
            name = f"<b>{name}</b>"
        parts.append(name)
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " & " + parts[-1]


def _find_quartile(obj):
    """Cerca recursiva d'un 'Q[1-4]' dins l'objecte Serial Title."""
    if isinstance(obj, dict):
        for v in obj.values():
            r = _find_quartile(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_quartile(v)
            if r:
                return r
    elif isinstance(obj, str):
        m = re.fullmatch(r"Q[1-4]", obj.strip())
        if m:
            return m.group(0)
    return None


def serial_quartile(issn):
    if not issn:
        return ""
    try:
        data = get(f"{BASE}/content/serial/title/issn:{issn}")
        entries = data.get("serial-metadata-response", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        for e in entries:
            q = _find_quartile(e)
            if q:
                return q
    except Exception:
        pass
    return ""


# ---- Merge ----
def main():
    print(">>> Mètriques globals de l'autor...")
    m = author_metrics()
    print(f"    h-index={m['hIndex']}  cites={m['citations']}  docs={m['docCount']}")

    print(">>> Llista de documents de Scopus...")
    docs = scopus_docs()
    print(f"    {len(docs)} documents trobats")

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
    for e in docs:
        if not isinstance(e, dict) or "error" in e:
            continue
        doi = norm_doi(e.get("prism:doi"))
        sub = e.get("subtype", "") or ""
        if doi and doi in by_doi:
            # Actualitza cites (i guardem l'Scopus ID); la resta és curada
            cb = e.get("citedby-count")
            if cb is not None:
                by_doi[doi]["citations"] = int(cb)
            ident = e.get("dc:identifier", "") or ""
            if ident:
                by_doi[doi]["scopusId"] = ident.replace("SCOPUS_ID:", "")
            continue
        if not doi or sub not in ALLOWED_SUBTYPES or doi in EXCLUDE_DOIS:
            continue
        # Publicació nova no present al seed
        sid = (e.get("dc:identifier", "") or "").replace("SCOPUS_ID:", "")
        time.sleep(0.4)
        authors = abstract_authors(sid) or (e.get("dc:creator") or "")
        issn = e.get("prism:issn") or e.get("prism:eIssn") or ""
        quartile = serial_quartile(issn)
        entry = {
            "doi": e.get("prism:doi", doi),
            "authors": authors,
            "title": e.get("dc:title", "") or "",
            "journal": e.get("prism:publicationName", "") or "",
            "volume": e.get("prism:volume", "") or "",
            "issue": e.get("prism:issueIdentifier", "") or "",
            "pages": e.get("prism:pageRange", "") or "",
            "year": int((e.get("prism:coverDate", "") or "0")[:4] or 0),
            "jif": "",
            "quartile": quartile or "—",
            "citations": int(e.get("citedby-count", 0) or 0),
            "scopusId": sid,
            "issn": issn,
            "auto": True,
        }
        new_entries.append(entry)
        print(f"    + NOVA: {entry['title'][:75]} ({entry['year']})")

    merged = list(by_doi.values()) + no_doi_seed + new_entries
    merged.sort(key=lambda p: (p.get("year", 0), str(p.get("doi"))), reverse=True)

    # Escriu publications.json
    out_pubs = {"updated": today(), "publications": merged}
    with open(PUBS_PATH, "w", encoding="utf-8") as f:
        json.dump(out_pubs, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Actualitza stats.json (només camps automàtics)
    stats = {}
    if os.path.exists(STATS_PATH):
        with open(STATS_PATH, encoding="utf-8") as f:
            stats = json.load(f)
    stats["publications"] = len(merged)
    stats["citations"] = m["citations"]
    stats["hIndex"] = m["hIndex"]
    stats["updated"] = today()
    stats["source"] = "Scopus (autor 57193928271) · Curriculum vitae AQU Catalunya"
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"<<< Fet. Publicacions: {len(merged)} (noves: {len(new_entries)}). "
          f"stats -> pubs={len(merged)} cites={m['citations']} h={m['hIndex']}")


if __name__ == "__main__":
    main()