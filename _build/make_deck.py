#!/usr/bin/env python3
"""Turn one downloaded Slides deck into a hosted deck page on the site.

Usage (run from the repository root):
  python3 _build/make_deck.py <deck_folder> <deck_url>

<deck_folder> holds project/deck.json and project/slides/<id>.html for every id in deck.json "order".
<deck_url> is the deck's claude.ai address, as listed in _build/catalog.json.
The script writes science-starter-pack/slides/grade-<g>/<slug>/index.html, points the grade page's
"Slide deck" button at it, adds it to sitemap.xml, and records it in _build/decks-hosted.json.
"""
import json, os, re, sys, html, datetime

DOMAIN = "https://confluenceeducation.ca"
root = os.getcwd()
deck_dir, deck_url = sys.argv[1], sys.argv[2].rstrip("/")
cat = json.load(open(os.path.join(root, "_build/catalog.json")))
entries = [l for l in cat["labs"] if any(r.get("type") == "slides" and r["url"].rstrip("/") == deck_url for r in l.get("resources", []))]
if not entries:
    sys.exit(f"deck url not in catalog: {deck_url}")
lab = entries[0]
g = lab["grade"]
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
lab_path = f"/science-starter-pack/labs/grade-{g}/{slug(lab['title'])}/"

deck = json.load(open(os.path.join(deck_dir, "project/deck.json")))
title = deck.get("title") or lab["title"].rsplit(" Lab", 1)[0] + " Slides"
path = f"/science-starter-pack/slides/grade-{g}/{slug(title)}/"
missing, sections = [], []
for sid in deck["order"]:
    fp = os.path.join(deck_dir, "project/slides", sid + ".html")
    if not os.path.exists(fp):
        missing.append(sid); continue
    s = open(fp).read().strip()
    s = s.replace("Riverbend School · ", "").replace("Riverbend School Science · ", "")
    sections.append(s)
if missing:
    sys.exit(f"missing slide files: {missing}")
if not sections:
    sys.exit("no slides")

fonts = "".join(f'<link rel="stylesheet" href="{html.escape(f["href"])}">' for f in deck.get("faces", {}).values() if f.get("href", "").startswith("https://fonts.googleapis.com/"))
e = html.escape
codes = ", ".join(l["code"] for l in entries)
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · Science {g} · Confluence Curriculum &amp; PD</title>
<meta name="description" content="{e(lab['understanding'])}">
<link rel="canonical" href="{DOMAIN}{path}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<link rel="stylesheet" href="/assets/deck.css">
</head>
<body class="deck">
<header class="dk-bar">
<span class="dk-title">{e(title)}</span>
<span>Science {g} · {e(codes)}</span>
<a href="{lab_path}">Open the lab</a>
<a class="dk-dl" href="{path}{slug(title)}.pptx" download>Download for PowerPoint or Google Slides</a>
<a href="/use/#google-slides">How to open in Google Slides</a>
<a href="/science-starter-pack/science-{g}/">All Science {g}</a>
</header>
<main class="dk-stage-wrap"><div class="dk-stage" aria-roledescription="slide deck" aria-label="{e(title)}"><div class="dk-scaler">
{chr(10).join(sections)}
</div></div></main>
<nav class="dk-ctrl" aria-label="Slide controls">
<button type="button" class="dk-prev">Previous</button>
<span class="dk-count" aria-live="polite"></span>
<button type="button" class="dk-next">Next</button>
<button type="button" class="dk-notes-btn" aria-pressed="false">Teacher notes</button>
</nav>
<section class="dk-notes" hidden><h2>Teacher notes</h2><div class="dk-notes-body"></div></section>
<script src="/assets/deck.js"></script>
</body>
</html>
"""
out = os.path.join(root, path.strip("/"), "index.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w").write(page)

# editable PowerPoint copy (also opens in Google Slides)
import subprocess, tempfile, threading, http.server, functools, socketserver
pptx_name = slug(title) + ".pptx"
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=root))
threading.Thread(target=srv.serve_forever, daemon=True).start()
tmp = tempfile.mkdtemp()
try:
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(["node", os.path.join(here, "export_pptx.js"), f"http://127.0.0.1:{srv.server_address[1]}{path}", os.path.join(tmp, "s.json"), os.path.join(tmp, "img")], check=True, timeout=600)
    subprocess.run([sys.executable, os.path.join(here, "pptx_from_json.py"), os.path.join(tmp, "s.json"), os.path.join(os.path.dirname(out), pptx_name), title], check=True, timeout=300)
finally:
    srv.shutdown()

# point the grade page's deck button at the hosted copy
gp = os.path.join(root, f"science-starter-pack/science-{g}/index.html")
s = open(gp).read()
old = f'href="{e(deck_url)}" target="_blank" rel="noopener">Slide deck<span class="sr"> (opens in a new tab)</span>'
n = s.count(old)
s = s.replace(old, f'href="{path}">Slide deck')
open(gp, "w").write(s)

# sitemap
sm_p = os.path.join(root, "sitemap.xml")
sm = open(sm_p).read()
loc = f"<loc>{DOMAIN}{path}</loc>"
if loc not in sm:
    sm = sm.replace("</urlset>", f"<url>{loc}<lastmod>{datetime.date.today().isoformat()}</lastmod></url>\n</urlset>")
    open(sm_p, "w").write(sm)

# manifest
mp = os.path.join(root, "_build/decks-hosted.json")
man = json.load(open(mp)) if os.path.exists(mp) else {}
man[deck_url] = {"path": path, "slides": len(sections), "date": datetime.date.today().isoformat()}
json.dump(man, open(mp, "w"), indent=1)
print(f"ok {path} slides={len(sections)} grade_links_updated={n}")
