#!/usr/bin/env python3
"""
Generador estàtic del bloc de cerdadomenech (local).

Com afegir un article nou:
  1. Crea un fitxer .md a content/posts/ amb el format AAAA-MM-DD-slug.md
  2. Omple la capçalera (frontmatter) i el text a sota, separat per línies en blanc.
     Una línia que comença per "> " es renderitza com a cita destacada.
  3. Executa: python3 scripts/build_blog.py
     Això regenera blog/index.html i blog/<slug>/index.html
"""
import re
import html
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
BLOG_DIR = ROOT / "blog"

CYAN = "#39ffb0"

def favicon_tags(depth):
    """Genera els tags de favicon amb ruta relativa segons la profunditat."""
    p = "../" * depth
    return (
        f'<link rel="icon" type="image/svg+xml" href="{p}img/favicon.svg" />\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{p}img/favicon-32x32.png" />\n'
        f'<link rel="apple-touch-icon" sizes="180x180" href="{p}img/apple-touch-icon.png" />\n'
        f'<link rel="manifest" href="{p}manifest.json" />\n'
        f'<meta name="theme-color" content="#000705" />'
    )

# CSS específic del bloc (el CSS base va a css/styles.css)
CSS = """
.posts{ display:flex; flex-direction:column; gap:16px; }
.post-card{
  display:flex; gap:18px; text-decoration:none; color:inherit;
  background:var(--panel); border:1px solid var(--panel-border); border-left:3px solid var(--cyan);
  border-radius:10px; padding:18px; transition:transform .15s ease, box-shadow .15s ease;
}
.post-card:hover{ transform:translateY(-2px); box-shadow:0 10px 26px -10px var(--cyan); }
.post-card img{ width:110px; height:110px; object-fit:cover; border-radius:8px; flex:0 0 auto; }
.post-card .meta{ text-transform:uppercase; letter-spacing:0.08em; font-size:0.66rem; color:var(--cyan); font-weight:700; margin:0 0 6px; }
.post-card h2{ font-family:var(--sans); font-size:1.1rem; margin:0 0 6px; color:#fff; }
.post-card p.excerpt{ margin:0; color:var(--muted); font-size:0.85rem; line-height:1.5; }
.article-hero{ width:100%; max-height:340px; object-fit:cover; border-radius:12px; margin-bottom:26px; }
.article-meta{ text-align:center; color:var(--muted); font-size:0.8rem; margin:0 0 34px; text-transform:uppercase; letter-spacing:0.06em; }
.article-body p{ font-size:1.02rem; line-height:1.75; color:#dbe6e8; margin:0 0 22px; }
.article-body blockquote{
  margin:32px 0; padding:4px 0 4px 22px; border-left:3px solid var(--cyan);
  font-family:var(--sans); font-style:italic; font-size:1.2rem; color:#fff;
}
.source-note{
  margin-top:40px; padding-top:20px; border-top:1px solid var(--panel-border);
  color:var(--muted); font-size:0.82rem; text-align:center;
}
.source-note a{ color:var(--cyan); text-decoration:none; }
"""

LOGO_SVG = """<svg class="mark" viewBox="0 0 40 40" fill="none" stroke="currentColor">
  <circle cx="20" cy="20" r="17" stroke-width="1.1" opacity="0.7"/>
  <g stroke-width="1.1" opacity="0.5">
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(0 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(30 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(60 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(90 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(120 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(150 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(180 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(210 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(240 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(270 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(300 20 20)"/>
    <line x1="20" y1="3" x2="20" y2="6" transform="rotate(330 20 20)"/>
  </g>
  <path d="M12,27 L12,13 Q16,20 20,23 Q24,20 28,13 L28,27" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="20" cy="4.5" r="1.1" fill="currentColor" stroke="none"/>
</svg>"""


def topbar(depth):
    prefix = "../" * depth
    template_path = ROOT / "templates" / "topbar.html"
    tmpl = template_path.read_text(encoding="utf-8")
    tmpl = tmpl.replace("{DEPTH}", prefix)
    # Selector d'idioma: el bloc només existeix en català, així que EN va a la
    # portada anglesa (mateixa convenció que build_pages.render_lang_switch).
    lang_switch = (
        '<div class="lang-switch" role="group" aria-label="Idioma">'
        f'<a href="index.html" hreflang="ca" lang="ca" class="is-current" aria-current="true">CA</a>'
        '<span class="lang-sep" aria-hidden="true">/</span>'
        f'<a href="{prefix}en/index.html" hreflang="en" lang="en">EN</a>'
        '</div>'
    )
    tmpl = tmpl.replace("{LANG_SWITCH}", lang_switch)
    # Marca el link del bloc com a pàgina actual
    tmpl = tmpl.replace(
        f'<a href="{prefix}blog/index.html" data-nav="blog">',
        f'<a href="{prefix}blog/index.html" data-nav="blog" aria-current="page">',
    )
    return tmpl


# ?v=<hash> igual que a build_pages.py, perquè els canvis de CSS no quedin
# encallats als 10 minuts de cache de GitHub Pages.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pages import asset_version  # noqa: E402

HEAD_LINKS = ('<link rel="stylesheet" href="{prefix}css/fonts.css?v=' + (asset_version("css/fonts.css") or "") + '" />\n'
              '<link rel="stylesheet" href="{prefix}css/styles.css?v=' + (asset_version("css/styles.css") or "") + '" />')

HAMBURGER_SCRIPT = """<script id="hamburger-init">
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
  </script>"""


def parse_post(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    fm_raw, body_raw = m.group(1), m.group(2)
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    fm["date"] = datetime.strptime(fm["date"], "%Y-%m-%d").date()

    blocks = [b.strip() for b in re.split(r"\n\s*\n", body_raw.strip()) if b.strip()]
    html_parts = []
    for b in blocks:
        if b.startswith(">"):
            quote = b.lstrip(">").strip()
            html_parts.append(f"<blockquote>{html.escape(quote)}</blockquote>")
        else:
            html_parts.append(f"<p>{html.escape(b)}</p>")
    fm["body_html"] = "\n".join(html_parts)
    return fm


def render_index(posts):
    cards = []
    for p in posts:
        cards.append(f"""      <a class="post-card" href="{p['slug']}/index.html">
        <img src="../{p['image']}" alt="{html.escape(p['image_alt'])}" width="110" height="110" loading="lazy" />
        <div>
          <p class="meta">{p['date_display']}</p>
          <h2>{html.escape(p['title'])}</h2>
          <p class="excerpt">{html.escape(p['excerpt'])}</p>
        </div>
      </a>""")
    return f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Bloc · Marc Cerdà i Domènech</title>
{favicon_tags(1)}
{HEAD_LINKS.format(prefix='../')}
<style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#main">Salta al contingut</a>
  <div class="wrap" id="main">
    {topbar(1)}
    <h1 class="page-title">Bloc</h1>
    <p class="page-sub">Reflexions sobre ciència marina, clima i polítiques ambientals</p>
    <div class="posts">
{chr(10).join(cards)}
    </div>
    <footer>
      <a href="../index.html">← Torna al perfil</a> · Basat en <a href="https://cerdadomenech.blog/bloc/" target="_blank" rel="noopener">cerdadomenech.blog</a>
    </footer>
  </div>
  {HAMBURGER_SCRIPT}
</body>
</html>
"""


def render_post(p):
    source_html = ""
    if p.get("source_url"):
        source_html = f"""<p class="source-note">{html.escape(p.get('source_note',''))} —
      <a href="{p['source_url']}" target="_blank" rel="noopener">llegeix l'original a cerdadomenech.blog</a></p>"""
    return f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(p['title'])} · Marc Cerdà i Domènech</title>
{favicon_tags(2)}
{HEAD_LINKS.format(prefix='../../')}
<style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#main">Salta al contingut</a>
  <div class="wrap" id="main">
    {topbar(2)}
    <p class="crumbs"><a href="../index.html">← Tots els articles</a></p>
    <h1 class="page-title">{html.escape(p['title'])}</h1>
    <p class="article-meta">{p['date_display']}</p>
    <img class="article-hero" src="../../{p['image']}" alt="{html.escape(p['image_alt'])}" decoding="async" />
    <div class="article-body">
{p['body_html']}
    </div>
    {source_html}
    <footer>
      <a href="../../index.html">← Torna al perfil</a> · Basat en <a href="https://cerdadomenech.blog/" target="_blank" rel="noopener">cerdadomenech.blog</a>
    </footer>
  </div>
  {HAMBURGER_SCRIPT}
</body>
</html>
"""


# ---- Bloc d'articles de la portada (CA i EN) ----
# La portada mostrava el darrer article escrit a mà, i calia recordar-se
# d'actualitzar-lo a cada article nou. Ara es genera des dels Markdown,
# entre els marcadors <!-- @blog-highlights:start|end -->.
HOME_PAGES = [("index.html", "ca", ""), ("en/index.html", "en", "../")]
MONTHS_EN = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
MONTHS_CA = ["Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
             "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"]
HIGHLIGHT_STRINGS = {
    "ca": {"heading": "Últim article del bloc", "read": "Llegeix l'article →",
           "tag": lambda p: f'{MONTHS_CA[p["date"].month - 1]} {p["date"].year}'},
    "en": {"heading": "Latest blog post", "read": "Read the post (Catalan) →",
           "tag": lambda p: f'{MONTHS_EN[p["date"].month - 1]} {p["date"].year} · in Catalan'},
}
HIGHLIGHT_EXTRA = 0  # articles compactes sota el destacat (0 = només el darrer)


def field(post, key, lang):
    """Valor del camp en la llengua demanada; si no hi ha variant _en, el català.

    Els articles s'escriuen en català; title_en/excerpt_en al frontmatter són
    opcionals i serveixen perquè la portada anglesa expliqui de què va l'article.
    """
    if lang == "en" and post.get(key + "_en"):
        return post[key + "_en"]
    return post[key]


def esc(text):
    """Escapa per a text (no per a atributs): manté els apòstrofs tal qual."""
    return html.escape(str(text), quote=False)


def render_home_highlights(posts, lang, prefix):
    t = HIGHLIGHT_STRINGS[lang]
    if not posts:
        return ""
    first, rest = posts[0], posts[1:1 + HIGHLIGHT_EXTRA]
    out = [f'    <h2 class="section reveal">{t["heading"]}</h2>',
           '    <div class="posts">',
           f'      <a class="featured-post reveal" href="{prefix}blog/{first["slug"]}/index.html">',
           f'        <p class="tag">{esc(t["tag"](first))}</p>',
           f'        <h3>{esc(field(first, "title", lang))}</h3>',
           f'        <p>{esc(field(first, "excerpt", lang))}</p>',
           f'        <span class="read-more">{t["read"]}</span>',
           '      </a>']
    if rest:
        out.append('      <ul class="post-more reveal">')
        for p in rest:
            out.append(f'        <li><a href="{prefix}blog/{p["slug"]}/index.html">'
                       f'<span class="pm-title">{esc(field(p, "title", lang))}</span>'
                       f'<span class="pm-date">{esc(t["tag"](p))}</span></a></li>')
        out.append('      </ul>')
    out.append('    </div>')
    return "\n".join(out) + "\n"


def update_home_highlights(posts):
    """Regenera el bloc d'articles destacats de les dues portades."""
    for rel, lang, prefix in HOME_PAGES:
        path = ROOT / rel
        if not path.exists():
            continue
        page = path.read_text(encoding="utf-8")
        block = render_home_highlights(posts, lang, prefix)
        new, n = re.subn(
            r"(<!-- @blog-highlights:start -->\n).*?(    <!-- @blog-highlights:end -->)",
            lambda m: m.group(1) + block + m.group(2),
            page, count=1, flags=re.S)
        if n != 1:
            print(f"  AVÍS: no hi ha marcadors @blog-highlights a {rel}", file=sys.stderr)
            continue
        if new != page:
            path.write_text(new, encoding="utf-8")
        print(f"  portada actualitzada: {rel}")


def main():
    posts = sorted(
        (parse_post(f) for f in POSTS_DIR.glob("*.md")),
        key=lambda p: p["date"],
        reverse=True,
    )

    BLOG_DIR.mkdir(exist_ok=True)
    (BLOG_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")

    for p in posts:
        post_dir = BLOG_DIR / p["slug"]
        post_dir.mkdir(exist_ok=True)
        (post_dir / "index.html").write_text(render_post(p), encoding="utf-8")

    update_home_highlights(posts)

    print(f"Generats {len(posts)} articles a {BLOG_DIR}")
    for p in posts:
        print(f"  - blog/{p['slug']}/index.html  ({p['date_display']})")


if __name__ == "__main__":
    main()
