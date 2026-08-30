#!/usr/bin/env python3
"""
build_seo.py — afegeix metadades SEO a totes les pàgines HTML.

Afegeix:
  - <meta name="description">
  - Open Graph (og:title, og:description, og:image, og:url, og:type, og:locale)
  - Twitter Card (summary_large_image)
  - <link rel="canonical">
  - JSON-LD structured data (Person a la home, ItemList a publicacions,
    ResearchProject a les pàgines de projecte)

Ús:
  python3 scripts/build_seo.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://athanor8732.github.io"

# ---- Metadades per pàgina ----
PAGES = {
    "index.html": {
        "title": "Marc Cerdà i Domènech · Geociències Marines",
        "description": "Investigador en geociències marines i professor lector a la Universitat de Barcelona. Metalls antropogènics, hidrogeologia costanera i governança marina.",
        "type": "website",
        "image": "img/marc.png",
        "jsonld": "person",
    },
    "sobre-mi/index.html": {
        "title": "Sobre mi · Marc Cerdà i Domènech",
        "description": "Trajectòria acadèmica i professional de Marc Cerdà i Domènech, investigador en geociències marines i professor lector a la UB.",
        "type": "profile",
        "image": "img/marc.png",
    },
    "recerca/index.html": {
        "title": "Recerca · Marc Cerdà i Domènech",
        "description": "Línies de recerca, campanyes oceanogràfiques i projectes de Marc Cerdà i Domènech: metalls antropogènics, hidrogeologia costanera i governança marina.",
        "type": "website",
        "image": "img/marc.png",
    },
    "publicacions/index.html": {
        "title": "Publicacions · Marc Cerdà i Domènech",
        "description": "Articles en revistes indexades amb avaluació externa. 16 publicacions, 276 citacions, índex h de 7. Mètriques d'OpenAlex i AQU Catalunya.",
        "type": "article",
        "image": "img/marc.png",
        "jsonld": "publications",
    },
    "docencia/index.html": {
        "title": "Docència · Marc Cerdà i Domènech",
        "description": "Trajectòria docent de Marc Cerdà i Domènech a la Universitat de Barcelona i la Universitat Carlemany. 1.249 hores, 17 assignatures, 8 treballs dirigits.",
        "type": "website",
        "image": "img/marc.png",
    },
    "docencia/recursos-docents/index.html": {
        "title": "Recursos docents · Marc Cerdà i Domènech",
        "description": "Recursos i materials per a la docència en ciències del mar i geociències marines: repositoris, eines i referències.",
        "type": "website",
        "image": "img/marc.png",
    },
    "mitjans/index.html": {
        "title": "Mitjans · Marc Cerdà i Domènech",
        "description": "Articles d'opinió, entrevistes i xerrades sobre ciència, clima i polítiques ambientals. Columna a Línia Xarxa des de 2019.",
        "type": "website",
        "image": "img/marc.png",
    },
    "contacte/index.html": {
        "title": "Contacte · Marc Cerdà i Domènech",
        "description": "Contacte de Marc Cerdà i Domènech, professor lector al Departament de Dinàmica de la Terra i de l'Oceà, Universitat de Barcelona.",
        "type": "website",
        "image": "img/marc.png",
    },
    "blog/index.html": {
        "title": "Bloc · Marc Cerdà i Domènech",
        "description": "Reflexions sobre ciència marina, clima i polítiques ambientals. Articles de Marc Cerdà i Domènech.",
        "type": "website",
        "image": "img/marc.png",
    },
    "impas-garraf/index.html": {
        "title": "IMPAS-Garraf · Marc Cerdà i Domènech",
        "description": "Projecte d'investigació sobre els impactes de la descàrrega d'aigua subterrània als ecosistemes marins del Garraf. Finançat per l'Agència Catalana de l'Aigua (2024–2027).",
        "type": "website",
        "image": "img/impas/hero-campanya.jpg",
        "jsonld": "project_impas",
    },
    "emicreuer-bcn/index.html": {
        "title": "EMICREUER-BCN · Marc Cerdà i Domènech",
        "description": "Projecte sobre les emissions atmosfèriques dels creuers al port de Barcelona. Inventari 2012–2025, metodologia Tier 3 EMEP/EEA.",
        "type": "website",
        "image": "img/emicreuer/port-ciutat.jpg",
        "jsonld": "project_emicreuer",
    },
}

# ---- JSON-LD ----
def jsonld_person():
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Marc Cerdà i Domènech",
        "jobTitle": "Professor Lector en Geociències Marines",
        "worksFor": {
            "@type": "CollegeOrUniversity",
            "name": "Universitat de Barcelona",
        },
        "url": BASE_URL + "/",
        "image": BASE_URL + "/img/marc.png",
        "sameAs": [
            "https://orcid.org/0000-0001-5053-755X",
            "https://twitter.com/elpiratavell",
            "https://bsky.app/profile/elpiratavell.bsky.social",
            "https://www.linkedin.com/in/marc-cerd%C3%A0-i-dom%C3%A8nech-0a748849/",
            "https://www.scopus.com/pages/authors/57193928271",
            "https://www.researchgate.net/profile/Marc-Cerda-Domenech",
        ],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "C/ Martí Franquès, s/n",
            "addressLocality": "Barcelona",
            "postalCode": "08028",
            "addressCountry": "ES",
        },
    }


def jsonld_publications():
    pubs_path = ROOT / "data" / "publications.json"
    if not pubs_path.exists():
        return None
    data = json.loads(pubs_path.read_text(encoding="utf-8"))
    items = []
    for p in data.get("publications", [])[:20]:
        item = {
            "@type": "ScholarlyArticle",
            "name": p.get("title", ""),
            "author": p.get("authors", "").replace("<b>", "").replace("</b>", ""),
            "datePublished": str(p.get("year", "")),
            "isPartOf": {"@type": "Journal", "name": p.get("journal", "")},
        }
        if p.get("doi"):
            item["url"] = "https://doi.org/" + p["doi"]
        items.append(item)
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Publicacions de Marc Cerdà i Domènech",
        "numberOfItems": len(data.get("publications", [])),
        "itemListElement": items,
    }


def jsonld_project(project_key):
    if project_key == "project_impas":
        return {
            "@context": "https://schema.org",
            "@type": "ResearchProject",
            "name": "IMPAS-Garraf",
            "description": "IMPactes de la descàrrega d'Aigua Subterrània als ecosistemes mediterranis marins: identificació i quantificació dels fluxos de contaminants a les aigües costaneres del Garraf.",
            "funder": {"@type": "Organization", "name": "Agència Catalana de l'Aigua"},
            "funding": "RDI001/24/000039",
            "startDate": "2024",
            "endDate": "2027",
            "url": BASE_URL + "/impas-garraf/",
        }
    elif project_key == "project_emicreuer":
        return {
            "@context": "https://schema.org",
            "@type": "ResearchProject",
            "name": "EMICREUER-BCN",
            "description": "EMIssions atmosfèriques dels CREUERs al port de Barcelona. Inventari 2012–2025 amb metodologia Tier 3 EMEP/EEA.",
            "funder": {"@type": "Organization", "name": "GMAR-UB (projecte propi)"},
            "startDate": "2012",
            "endDate": "2025",
            "url": BASE_URL + "/emicreuer-bcn/",
        }
    return None


def build_meta_tags(page_path, meta):
    """Construeix els tags SEO per a una pàgina."""
    rel = page_path.relative_to(ROOT)
    depth = len(rel.parts) - 1
    prefix = "../" * depth if depth > 0 else ""
    url_path = str(rel).replace("\\", "/")
    canonical = f"{BASE_URL}/{url_path}" if depth > 0 else f"{BASE_URL}/"
    image_url = BASE_URL + "/" + meta["image"]
    prefix_img = prefix if depth > 0 else ""

    tags = []
    tags.append(f'<meta name="description" content="{meta["description"]}" />')
    tags.append(f'<link rel="canonical" href="{canonical}" />')
    # Open Graph
    tags.append('<meta property="og:site_name" content="Marc Cerdà i Domènech" />')
    tags.append(f'<meta property="og:title" content="{meta["title"]}" />')
    tags.append(f'<meta property="og:description" content="{meta["description"]}" />')
    tags.append(f'<meta property="og:url" content="{canonical}" />')
    tags.append(f'<meta property="og:image" content="{image_url}" />')
    tags.append(f'<meta property="og:type" content="{meta["type"]}" />')
    tags.append('<meta property="og:locale" content="ca_ES" />')
    # Twitter Card
    tags.append('<meta name="twitter:card" content="summary_large_image" />')
    tags.append(f'<meta name="twitter:title" content="{meta["title"]}" />')
    tags.append(f'<meta name="twitter:description" content="{meta["description"]}" />')
    tags.append(f'<meta name="twitter:image" content="{image_url}" />')

    return "\n  ".join(tags)


def build_jsonld(meta):
    """Construeix el bloc JSON-LD per a una pàgina."""
    key = meta.get("jsonld")
    if not key:
        return None
    if key == "person":
        return jsonld_person()
    elif key == "publications":
        return jsonld_publications()
    elif key.startswith("project_"):
        return jsonld_project(key)
    return None


def process_page(page_path, meta):
    html = page_path.read_text(encoding="utf-8")

    # Evitar reprocessar
    if 'name="description"' in html and 'og:title' in html:
        # Eliminar tags SEO existents per reinsertar-los (idempotent)
        html = re.sub(r'\s*<meta name="description"[^>]*/>', '', html)
        html = re.sub(r'\s*<link rel="canonical"[^>]*/>', '', html)
        html = re.sub(r'\s*<meta property="og:[^>]*/>', '', html)
        html = re.sub(r'\s*<meta name="twitter:[^>]*/>', '', html)
        html = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', '', html, flags=re.DOTALL)

    meta_tags = build_meta_tags(page_path, meta)

    # Inserir abans de </head>
    insert = "\n  " + meta_tags + "\n  "

    # JSON-LD
    jsonld = build_jsonld(meta)
    if jsonld:
        jsonld_str = json.dumps(jsonld, ensure_ascii=False, indent=2)
        insert += f'<script type="application/ld+json">\n{jsonld_str}\n  </script>\n  '

    html = html.replace("</head>", insert + "</head>", 1)
    page_path.write_text(html, encoding="utf-8")


def main():
    for page_rel, meta in PAGES.items():
        page_path = ROOT / page_rel
        if not page_path.exists():
            print(f"  AVÍS: no existeix {page_rel}")
            continue
        process_page(page_path, meta)
        print(f"  OK: {page_rel}")

    # Sitemap
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page_rel in PAGES:
        path = page_rel if page_rel != "index.html" else ""
        url = f"{BASE_URL}/{path}" if path else f"{BASE_URL}/"
        sitemap.append(f"  <url><loc>{url}</loc></url>")
    sitemap.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")
    print("  OK: sitemap.xml")

    # robots.txt
    robots = f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    print("  OK: robots.txt")

    print("<<< SEO completat.")


if __name__ == "__main__":
    main()