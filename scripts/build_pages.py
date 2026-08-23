#!/usr/bin/env python3
"""
build_pages.py — injecta partials HTML compartits a totes les pàgines.

Els partials viuen a templates/ i contenen marcadors {DEPTH} que són
substituïts pel prefix de ruta relativa corresponent a cada pàgina.

Marcadors suportats dins del HTML de cada pàgina:
  <!-- @partial:head -->          → <link> a css/fonts.css + css/styles.css
  <!-- @partial:topbar -->        → topbar amb logo + nav horitzontal
  <!-- @partial:ctd-rig -->       → SVG del CTD rosette + depth display
  <!-- @partial:side-promo -->    → side-promo d'IMPAS-Garraf
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
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
SKIP_PAGES = {"blog"}  # blog/ és generat per build_blog.py

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
    """Retorna l'identificador de pàgina per a aria-current (ex: 'recerca', 'publicacions')."""
    rel = page_path.relative_to(ROOT)
    if len(rel.parts) == 1:
        return "home"
    return rel.parts[0]


def inject_partials(html, depth, page_id):
    """Substitueix els marcadors <!-- @partial:X --> pel HTML del template."""
    templates = {
        "head": load_template("head"),
        "topbar": load_template("topbar"),
        "ctd-rig": load_template("ctd-rig"),
        "side-promo": load_template("side-promo"),
    }

    for name, tmpl in templates.items():
        marker = f"<!-- @partial:{name} -->"
        rendered = tmpl.replace("{DEPTH}", depth)
        html = html.replace(marker, rendered)

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


def add_skip_link(html):
    """Afegeix un skip-link just després de <body>."""
    skip = '<a class="skip-link" href="#main">Salta al contingut</a>\n  '
    # Si ja hi és, no el duplica
    if 'class="skip-link"' in html:
        return html
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
    """Afegeix un petit script inline per al hamburger menu."""
    if "topbar-toggle" not in html:
        return html
    if "hamburger-init" in html:
        return html
    script = """<script id="hamburger-init">
    (function(){
      var btn=document.querySelector('.topbar-toggle');if(!btn)return;
      var nav=document.getElementById('topbar-nav');if(!nav)return;
      btn.addEventListener('click',function(){
        var open=nav.classList.toggle('open');
        btn.setAttribute('aria-expanded',open);
      });
    })();
  </script>
  """
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
                      ["head", "topbar", "ctd-rig", "side-promo", "footer"])
    has_reveal = bool(re.search(r'class="[^"]*\breveal\b', html))
    has_topbar = "topbar-toggle" in html
    if not (has_markers or has_reveal or has_topbar):
        return False

    depth = depth_for(page_path)
    page_id = page_id_for(page_path)

    html = inject_partials(html, depth, page_id)
    html = add_skip_link(html)
    html = add_main_id(html)
    html = add_ctd_script(html, depth)
    html = add_reveal_script(html, depth)
    html = add_hamburger_script(html)

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