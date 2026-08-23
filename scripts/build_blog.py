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
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
BLOG_DIR = ROOT / "blog"

CYAN = "#39ffb0"

FAVICON = ("<link rel=\"icon\" type=\"image/svg+xml\" href=\"data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
           "%3Crect width='40' height='40' rx='8' fill='%23000705'/%3E"
           "%3Ccircle cx='20' cy='20' r='17' fill='none' stroke='%2339ffb0' stroke-width='1.3' opacity='0.6'/%3E"
           "%3Cpath d='M12,27 L12,13 Q16,20 20,23 Q24,20 28,13 L28,27' fill='none' stroke='%2339ffb0' "
           "stroke-width='3.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\" />")

CSS = """
:root{
  --bg-deep:#000705; --bg-mid:#04140f;
  --panel:rgba(255,255,255,0.045); --panel-border:rgba(255,255,255,0.09);
  --text:#eaf2f4; --muted:#8fa5ac; --cyan:#39ffb0; --cyan-rgb:57,255,176;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{
  background:
    radial-gradient(ellipse 900px 500px at 50% -10%, rgba(var(--cyan-rgb),0.10), transparent 60%),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 34px),
    linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-mid) 55%, var(--bg-deep) 100%);
  background-attachment:fixed;
  color:var(--text);
  font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  min-height:100vh;
}
.wrap{ max-width:648px; margin:0 auto; padding:0 24px 90px; }
.topbar{
  display:flex; align-items:center; justify-content:center; gap:12px;
  padding:18px 0; border-bottom:1px solid var(--panel-border); margin-bottom:44px;
  position:sticky; top:0; z-index:5;
  background:
    radial-gradient(ellipse 900px 500px at 50% -10%, rgba(var(--cyan-rgb),0.10), transparent 60%),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 34px),
    linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-mid) 55%, var(--bg-deep) 100%);
  background-attachment:fixed;
}
.topbar .mark{ width:34px; height:34px; color:var(--cyan); flex:0 0 auto; }
.topbar a.brand{ text-decoration:none; display:flex; align-items:center; gap:12px; }
.topbar span{
  font-family:Georgia,'Iowan Old Style',serif; font-style:italic; letter-spacing:0.12em;
  text-transform:uppercase; font-size:0.76rem; color:var(--muted);
}
.topbar strong{ color:var(--text); font-style:normal; }
.crumbs{ text-align:center; margin-bottom:8px; }
.crumbs a{ color:var(--cyan); text-decoration:none; font-size:0.85rem; }
h1.page-title{
  font-family:Georgia,serif; font-weight:700; font-size:2rem; text-align:center;
  margin:8px 0 6px;
}
p.page-sub{ text-align:center; color:var(--muted); font-size:0.92rem; margin:0 0 40px; }
.posts{ display:flex; flex-direction:column; gap:16px; }
.post-card{
  display:flex; gap:18px; text-decoration:none; color:inherit;
  background:var(--panel); border:1px solid var(--panel-border); border-left:3px solid var(--cyan);
  border-radius:10px; padding:18px; transition:transform .15s ease, box-shadow .15s ease;
}
.post-card:hover{ transform:translateY(-2px); box-shadow:0 10px 26px -10px var(--cyan); }
.post-card img{ width:110px; height:110px; object-fit:cover; border-radius:8px; flex:0 0 auto; }
.post-card .meta{ text-transform:uppercase; letter-spacing:0.08em; font-size:0.66rem; color:var(--cyan); font-weight:700; margin:0 0 6px; }
.post-card h2{ font-family:Georgia,serif; font-size:1.1rem; margin:0 0 6px; color:#fff; }
.post-card p.excerpt{ margin:0; color:var(--muted); font-size:0.85rem; line-height:1.5; }
.article-hero{ width:100%; max-height:340px; object-fit:cover; border-radius:12px; margin-bottom:26px; }
.article-meta{ text-align:center; color:var(--muted); font-size:0.8rem; margin:0 0 34px; text-transform:uppercase; letter-spacing:0.06em; }
.article-body p{ font-size:1.02rem; line-height:1.75; color:#dbe6e8; margin:0 0 22px; }
.article-body blockquote{
  margin:32px 0; padding:4px 0 4px 22px; border-left:3px solid var(--cyan);
  font-family:Georgia,serif; font-style:italic; font-size:1.2rem; color:#fff;
}
.source-note{
  margin-top:40px; padding-top:20px; border-top:1px solid var(--panel-border);
  color:var(--muted); font-size:0.82rem; text-align:center;
}
.source-note a{ color:var(--cyan); text-decoration:none; }
footer{ margin-top:56px; text-align:center; color:var(--muted); font-size:0.76rem; }
footer a{ color:var(--cyan); text-decoration:none; }
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
    home = "../" * depth + "index.html"
    return f"""<div class="topbar">
  <a class="brand" href="{home}">
    {LOGO_SVG}
    <span><strong>Marc Cerdà i Domènech</strong> · Geociències Marines</span>
  </a>
</div>"""


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
        <img src="../{p['image']}" alt="{html.escape(p['image_alt'])}" />
        <span>
          <p class="meta">{p['date_display']}</p>
          <h2>{html.escape(p['title'])}</h2>
          <p class="excerpt">{html.escape(p['excerpt'])}</p>
        </span>
      </a>""")
    return f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Bloc · Marc Cerdà i Domènech</title>
{FAVICON}
<style>{CSS}</style>
</head>
<body>
  <div class="wrap">
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
{FAVICON}
<style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    {topbar(2)}
    <p class="crumbs"><a href="../index.html">← Tots els articles</a></p>
    <h1 class="page-title">{html.escape(p['title'])}</h1>
    <p class="article-meta">{p['date_display']}</p>
    <img class="article-hero" src="../../{p['image']}" alt="{html.escape(p['image_alt'])}" />
    <div class="article-body">
{p['body_html']}
    </div>
    {source_html}
    <footer>
      <a href="../../index.html">← Torna al perfil</a> · Basat en <a href="https://cerdadomenech.blog/" target="_blank" rel="noopener">cerdadomenech.blog</a>
    </footer>
  </div>
</body>
</html>
"""


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

    print(f"Generats {len(posts)} articles a {BLOG_DIR}")
    for p in posts:
        print(f"  - blog/{p['slug']}/index.html  ({p['date_display']})")


if __name__ == "__main__":
    main()
