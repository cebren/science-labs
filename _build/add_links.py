#!/usr/bin/env python3
"""Idempotent site pass, run from the repository root after any change:
- adds a "Science Starter Pack" home bar to every lab page and Year Plan page
- builds the Year Plan pages from _build/plans/science-<g>.html, pointing their lab and deck
  links at this site's copies (decks only once they are hosted)
"""
import json, os, re, glob

DOMAIN = "https://confluenceeducation.ca"
cat = json.load(open("_build/catalog.json"))
hosted = json.load(open("_build/decks-hosted.json")) if os.path.exists("_build/decks-hosted.json") else {}
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

lab_map = {}
for l in cat["labs"]:
    if l.get("url"):
        lab_map[l["url"].rstrip("/")] = f"/science-starter-pack/labs/grade-{l['grade']}/{slug(l['title'])}/"
deck_map = {u.rstrip("/"): v["path"] for u, v in hosted.items()}

GC = {7: "#F0A070", 8: "#7DB0F0", 9: "#74C995"}
MARK = ('<svg viewBox="0 0 64 64" width="22" height="22" aria-hidden="true" style="flex:none">'
        '<path d="M6 10 C 20 14, 26 26, 32 36" fill="none" stroke="#5A9CCB" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M58 10 C 44 14, 38 26, 32 36" fill="none" stroke="#5CC4B8" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M32 36 C 32 44, 30 50, 32 58" fill="none" stroke="#4FAFC0" stroke-width="10" stroke-linecap="round"/></svg>')

def bar(g, label=None):
    font = "'Atkinson Hyperlegible','Segoe UI',system-ui,sans-serif"
    pill = ("display:inline-flex;align-items:center;gap:7px;min-height:34px;padding:6px 14px;border-radius:999px;"
            "text-decoration:none;font:700 14px/1.2 " + font + ";white-space:nowrap;")
    primary = pill + "background:#FFFFFF;color:#14303F;border:2px solid #FFFFFF;"
    ghost = pill + "background:transparent;color:#FFFFFF;border:2px solid rgba(255,255,255,.45);"
    btns = [f'<a href="/science-starter-pack/" style="{primary}"><span aria-hidden="true">←</span>Science Starter Pack</a>']
    if g:
        dot = f'<span aria-hidden="true" style="width:10px;height:10px;border-radius:50%;background:{GC[g]};flex:none"></span>'
        btns.append(f'<a href="/science-starter-pack/science-{g}/" style="{ghost}">{dot}Science {g} labs</a>')
        if label != "plan":
            btns.append(f'<a href="/science-starter-pack/year-plans/science-{g}/" style="{ghost}">'
                        '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" style="flex:none"><rect x="3.5" y="5" width="17" height="15" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3.5 10h17M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
                        f'Science {g} year plan</a>')
    brand = (f'<a href="/" style="display:inline-flex;align-items:center;gap:8px;margin-left:auto;color:#E6F1F5;text-decoration:none;'
             f'font:700 14px/1.2 \'Bricolage Grotesque\',{font}">{MARK}<span>Confluence Curriculum &amp; PD</span></a>')
    return ('<nav data-cf-home aria-label="Site" style="display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;'
            'padding:10px 16px;background:#14303F;border-bottom:3px solid #3A9E96;position:relative;z-index:50">'
            + "".join(btns) + brand + '</nav>'
            '<a data-cf-float href="/science-starter-pack/" aria-label="Back to the Science Starter Pack" style="position:fixed;left:12px;bottom:12px;z-index:2147483000;'
            f'display:inline-flex;align-items:center;gap:6px;background:#14303F;color:#fff;font:700 13px/1 {font};text-decoration:none;padding:10px 14px;border-radius:999px;border:2px solid #3A9E96;'
            'box-shadow:0 4px 14px rgba(0,0,0,.25);opacity:0;pointer-events:none;transition:opacity .2s">← Starter Pack</a>'
            '<script>(function(){var n=document.querySelector("[data-cf-home]"),f=document.querySelector("[data-cf-float]");'
            'if(!n||!f||!window.IntersectionObserver)return;new IntersectionObserver(function(e){var v=e[0].isIntersecting;'
            'f.style.opacity=v?"0":"1";f.style.pointerEvents=v?"none":"auto";f.tabIndex=v?-1:0;}).observe(n);})();</script>')

def inject(s, g, label=None):
    if "data-cf-home" in s:
        s = re.sub(r'<nav data-cf-home.*?</nav>(<a data-cf-float.*?</script>)?', lambda m: bar(g, label), s, count=1, flags=re.S)
        return s
    m = re.search(r"<body[^>]*>", s)
    return s[:m.end()] + bar(g, label) + s[m.end():] if m else bar(g, label) + s

# labs
n_labs = 0
for fp in glob.glob("science-starter-pack/labs/grade-*/*/index.html"):
    g = int(re.search(r"grade-(\d)", fp).group(1))
    s = open(fp).read(); s2 = inject(s, g)
    if s2 != s: open(fp, "w").write(s2); n_labs += 1

# year plans
n_plans = 0
for g in (7, 8, 9):
    src = f"_build/plans/science-{g}.html"
    if not os.path.exists(src): continue
    s = open(src).read()
    for u, p in sorted(lab_map.items(), key=lambda x: -len(x[0])):
        s = s.replace(f'"{u}"', f'"{p}"').replace(f"'{u}'", f"'{p}'")
    for u, p in sorted(deck_map.items(), key=lambda x: -len(x[0])):
        s = s.replace(f'"{u}"', f'"{p}"').replace(f"'{u}'", f"'{p}'")
    s = s.replace("https://claude.ai/artifact/9SVj66LucMGzU8g1w1Z7Ro", "/science-starter-pack/")
    s = s.replace("Riverbend School · ", "").replace("Riverbend School Science · ", "")
    path = f"/science-starter-pack/year-plans/science-{g}/"
    head = (f'<link rel="canonical" href="{DOMAIN}{path}"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            f'<meta name="description" content="Draft day by day year plan for Alberta\'s new Science {g} curriculum (2027/28), linked to the Science Starter Pack labs and slide decks.">')
    if "<head>" in s: s = s.replace("<head>", "<head>" + head, 1)
    else: s = head + s
    s = inject(s, g, "plan")
    out = path.strip("/") + "/index.html"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    old = open(out).read() if os.path.exists(out) else ""
    if old != s: open(out, "w").write(s); n_plans += 1
    # sitemap
    sm = open("sitemap.xml").read(); loc = f"<loc>{DOMAIN}{path}</loc>"
    if loc not in sm:
        open("sitemap.xml", "w").write(sm.replace("</urlset>", f"<url>{loc}</url>\n</urlset>"))
print(f"labs updated {n_labs}, plans written {n_plans}, decks linked in plans {len(deck_map)}")
