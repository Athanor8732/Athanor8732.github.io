#!/usr/bin/env python3
"""
build_pages.py — injecta partials HTML compartits a totes les pàgines.

Els partials viuen a templates/ i contenen marcadors {DEPTH} que són
substituïts pel prefix de ruta relativa corresponent a cada pàgina.

Marcadors suportats dins del HTML de cada pàgina:
  <!-- @partial:head -->          → <link> a css/fonts.css + css/styles.css
  <!-- @partial:topbar -->        → topbar amb logo + nav horitzontal
  <!-- @partial:ctd-rig -->       → SVG del CTD rosette + depth display
  <!-- @partial:footer -->        → footer genèric (no usat per ara)

Ús:
  python3 scripts/build_pages.py            # processa totes les pàgines
  python3 scripts/build_pages.py --check    # només mostra què canviaria (dry-run)

També afegeix:
  - skip-link al principi del <body>
  - <script src="js/ctd-rig.js" defer> al final del <body> (si hi ha @partial:ctd-rig)
  - <script src="js/reveal.js" defer> al final del <body> (si hi ha elements .reveal)
  - aria-current="page" automàtic al link de la nav corresponent
"""
import argparse
import hashlib
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
SKIP_PAGES = {"blog"}  # blog/ és generat per build_blog.py

# Correspondència entre la versió catalana i l'anglesa de cada pàgina.
# Clau = ruta relativa a l'arrel (català), valor = equivalent en anglès.
PAGE_MAP = {
    "index.html": "en/index.html",
    "sobre-mi/index.html": "en/about/index.html",
    "recerca/index.html": "en/research/index.html",
    "publicacions/index.html": "en/publications/index.html",
    "docencia/index.html": "en/teaching/index.html",
    "docencia/recursos-docents/index.html": "en/teaching/resources/index.html",
    "mitjans/index.html": "en/media/index.html",
    "contacte/index.html": "en/contact/index.html",
    "impas-garraf/index.html": "en/impas-garraf/index.html",
    "emicreuer-bcn/index.html": "en/emicreuer-bcn/index.html",
}
EN_TO_CA = {v: k for k, v in PAGE_MAP.items()}

SKIP_LINK_TEXT = {"ca": "Salta al contingut", "en": "Skip to content"}

# Actius amb ?v=<hash> perquè un canvi de CSS/JS arribi als navegadors a l'instant.
# GitHub Pages serveix aquests fitxers amb cache-control: max-age=600, i sense
# el paràmetre els visitants recurrents veuen la versió antiga fins a 10 minuts.
VERSIONED_ASSETS = ("css/fonts.css", "css/styles.css",
                    "js/ctd-rig.js", "js/reveal.js", "js/publications.js")


def asset_version(rel_path):
    """Hash curt del contingut d'un actiu, per fer de número de versió."""
    p = ROOT / rel_path
    if not p.exists():
        return None
    return hashlib.md5(p.read_bytes()).hexdigest()[:8]


def version_assets(html, depth):
    """Posa (o refresca) ?v=<hash> als enllaços de CSS i JS de la pàgina."""
    for rel in VERSIONED_ASSETS:
        v = asset_version(rel)
        if not v:
            continue
        attr = "href" if rel.endswith(".css") else "src"
        html = re.sub(
            rf'{attr}="{re.escape(depth)}{re.escape(rel)}(?:\?v=[0-9a-f]+)?"',
            f'{attr}="{depth}{rel}?v={v}"',
            html,
        )
    return html

# ---- Partials ----
def load_template(name):
    p = TEMPLATES / f"{name}.html"
    if not p.exists():
        raise FileNotFoundError(f"Template no trobat: {p}")
    return p.read_text(encoding="utf-8")


def depth_for(page_path):
    """Retorna el prefix de ruta relativa (../ repetides) per arribar a l'arrel."""
    rel = page_path.relative_to(ROOT)
    depth = len(rel.parts) - 1  # directoris = parts - 1 (el fitxer)
    return "../" * depth if depth > 0 else ""


def page_id_for(page_path):
    """Retorna l'identificador de pàgina per a aria-current (ex: 'recerca', 'research')."""
    parts = page_path.relative_to(ROOT).parts
    if parts and parts[0] == "en":
        parts = parts[1:]  # en/research/index.html → research
    if len(parts) <= 1:
        return "home"
    return parts[0]


def lang_for(page_path):
    """'en' per a les pàgines sota en/, 'ca' per a la resta."""
    rel = page_path.relative_to(ROOT).as_posix()
    return "en" if rel.startswith("en/") else "ca"


def counterpart_for(page_path):
    """Ruta (relativa a l'arrel) de la mateixa pàgina en l'altra llengua, o None."""
    rel = page_path.relative_to(ROOT).as_posix()
    return PAGE_MAP.get(rel) or EN_TO_CA.get(rel)


def render_lang_switch(page_path, depth):
    """Selector CA/EN de la topbar, amb l'enllaç a la pàgina equivalent."""
    rel = page_path.relative_to(ROOT).as_posix()
    lang = lang_for(page_path)
    other = counterpart_for(page_path)

    if lang == "ca":
        ca_href, en_href = rel, other
    else:
        ca_href, en_href = other, rel
    # Pàgines sense equivalent (blog): el salt d'idioma va a la portada de l'altra llengua
    ca_href = ca_href or "index.html"
    en_href = en_href or "en/index.html"

    def link(code, href, is_current):
        attrs = f' aria-current="true"' if is_current else ""
        cls = " class=\"is-current\"" if is_current else ""
        code_lang = "ca" if code == "CA" else "en"
        return (f'<a href="{depth}{href}" hreflang="{code_lang}" lang="{code_lang}"'
                f'{cls}{attrs}>{code}</a>')

    label = "Idioma" if lang == "ca" else "Language"
    return (
        f'<div class="lang-switch" role="group" aria-label="{label}">'
        + link("CA", ca_href, lang == "ca")
        + '<span class="lang-sep" aria-hidden="true">/</span>'
        + link("EN", en_href, lang == "en")
        + "</div>"
    )


def find_topbar_block(html):
    """Retorna (inici, fi) del bloc <div class="topbar">…</div> ja injectat, o None."""
    start = html.find('<div class="topbar">')
    if start == -1:
        return None
    # Recompte de <div>/</div> per trobar el tancament corresponent
    i, level = start, 0
    tag = re.compile(r"<(/?)div\b", re.I)
    while True:
        m = tag.search(html, i)
        if not m:
            return None
        level += -1 if m.group(1) else 1
        i = m.end()
        if level == 0:
            end = html.find(">", i) + 1
            return start, end


def inject_partials(html, depth, page_id, page_path):
    """Substitueix els marcadors <!-- @partial:X --> pel HTML del template."""
    lang = lang_for(page_path)
    topbar_name = "topbar.en" if lang == "en" else "topbar"
    templates = {
        "head": load_template("head"),
        "topbar": load_template(topbar_name),
        "ctd-rig": load_template("ctd-rig"),
    }
    lang_switch = render_lang_switch(page_path, depth)

    rendered_topbar = None
    for name, tmpl in templates.items():
        marker = f"<!-- @partial:{name} -->"
        rendered = tmpl.replace("{DEPTH}", depth).replace("{LANG_SWITCH}", lang_switch)
        if name == "topbar":
            rendered_topbar = rendered
        html = html.replace(marker, rendered)

    # Si la topbar ja estava injectada (sense marcador), la resincronitza amb el
    # template: així els canvis a templates/ es propaguen a totes les pàgines.
    if "<!-- @partial:topbar -->" not in html and rendered_topbar is not None:
        span = find_topbar_block(html)
        if span:
            start, end = span
            html = html[:start] + rendered_topbar.strip() + html[end:]

    # aria-current al nav link corresponent
    if page_id != "home":
        # Marca el link data-nav="page_id" amb aria-current (si encara no el té)
        pattern = rf'data-nav="{page_id}"(?! aria-current)'
        if re.search(pattern, html):
            html = re.sub(
                rf'(<a href="[^"]*" data-nav="{page_id}")',
                r'\1 aria-current="page"',
                html,
            )

    return html


def add_skip_link(html, lang="ca"):
    """Afegeix un skip-link just després de <body>, en la llengua de la pàgina."""
    skip = f'<a class="skip-link" href="#main">{SKIP_LINK_TEXT[lang]}</a>\n  '
    # Si ja hi és, només en corregeix el text
    if 'class="skip-link"' in html:
        return re.sub(r'(<a class="skip-link" href="#main">)[^<]*(</a>)',
                      r'\g<1>' + SKIP_LINK_TEXT[lang] + r'\g<2>', html, count=1)
    # Insereix just després de <body ...>
    html = re.sub(r'(<body[^>]*>\s*)', r'\1' + skip, html, count=1)
    return html


def add_main_id(html):
    """Afegeix id="main" al primer .wrap si no en té."""
    if 'id="main"' in html:
        return html
    html = html.replace('<div class="wrap"', '<div class="wrap" id="main"', 1)
    return html


def add_ctd_script(html, depth):
    """Afegeix <script src="js/ctd-rig.js" defer> abans de </body> si hi ha ctd-rig."""
    if "ctd-rig.js" in html:
        return html
    if 'id="ctd-rosette"' not in html:
        return html
    tag = f'<script src="{depth}js/ctd-rig.js" defer></script>\n  '
    html = html.replace("</body>", tag + "</body>", 1)
    return html


def add_reveal_script(html, depth):
    """Afegeix <script src="js/reveal.js" defer> si hi ha elements .reveal."""
    if "reveal.js" in html:
        return html
    if not re.search(r'class="[^"]*\breveal\b', html):
        return html
    tag = f'<script src="{depth}js/reveal.js" defer></script>\n  '
    html = html.replace("</body>", tag + "</body>", 1)
    return html


def add_hamburger_script(html):
    """Afegeix o actualitza el script inline del hamburger menu i submenus."""
    if "topbar-toggle" not in html:
        return html
    script = """<script id="hamburger-init">
    (function(){
      var btn=document.querySelector('.topbar-toggle');if(!btn)return;
      var nav=document.getElementById('topbar-nav');if(!nav)return;
      btn.addEventListener('click',function(){
        var open=nav.classList.toggle('open');
        btn.setAttribute('aria-expanded',open);
      });
      document.querySelectorAll('.nav-item.has-submenu > a').forEach(function(link){
        link.addEventListener('click',function(e){
          if(window.innerWidth <= 680){
            e.preventDefault();
            link.parentElement.classList.toggle('mobile-open');
          }
        });
      });
    })();
  </script>
  """
    if "hamburger-init" in html:
        # Substitueix el script existent pel nou (amb suport de submenus)
        html = re.sub(
            r'<script id="hamburger-init">.*?</script>',
            lambda _m: script.rstrip(),
            html,
            flags=re.DOTALL,
        )
        return html
    html = html.replace("</body>", script + "</body>", 1)
    return html


def process_page(page_path, dry_run=False):
    """Processa una pàgina: injecta partials, skip-link, scripts."""
    rel = page_path.relative_to(ROOT)

    # Saltar blog (generat per build_blog.py) i templates (són partials, no pàgines)
    if len(rel.parts) > 1 and rel.parts[0] in SKIP_PAGES:
        return False
    if rel.parts[0] == "templates":
        return False

    html = page_path.read_text(encoding="utf-8")

    # Processar si té marcadors de partial, elements .reveal, o topbar
    has_markers = any(f"<!-- @partial:{m} -->" in html for m in
                      ["head", "topbar", "ctd-rig", "footer"])
    has_reveal = bool(re.search(r'class="[^"]*\breveal\b', html))
    has_topbar = "topbar-toggle" in html
    if not (has_markers or has_reveal or has_topbar):
        return False

    depth = depth_for(page_path)
    page_id = page_id_for(page_path)

    html = inject_partials(html, depth, page_id, page_path)
    html = add_skip_link(html, lang_for(page_path))
    html = add_main_id(html)
    html = add_ctd_script(html, depth)
    html = add_reveal_script(html, depth)
    html = add_hamburger_script(html)
    html = version_assets(html, depth)

    if dry_run:
        return True

    page_path.write_text(html, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description="Injecta partials HTML a les pàgines.")
    ap.add_argument("--check", action="store_true", help="Dry-run: no escriure fitxers")
    args = ap.parse_args()

    pages = sorted(ROOT.rglob("*.html"))
    changed = 0
    for p in pages:
        if process_page(p, dry_run=args.check):
            changed += 1
            print(f"  {'DRY-RUN' if args.check else 'OK'}: {p.relative_to(ROOT)}")

    action = "comprovades" if args.check else "processades"
    print(f"<<< {changed} pàgines {action}.")


if __name__ == "__main__":
    main()