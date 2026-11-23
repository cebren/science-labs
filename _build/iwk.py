#!/usr/bin/env python3
"""Add an "Indigenous ways of knowing, doing and being" panel to a lab and a slide to its deck.

Usage (from the repository root):  python3 _build/iwk.py <catalog key>     e.g. g7-sl1
Reads _build/iwk/<key>.json. Idempotent: re-running replaces the earlier panel and slide.
Writes: the lab page (panel before the credit line), the deck page (slide before the last slide),
the deck's .pptx (rebuilt), and refreshes the site bar (adds a "Ways of knowing" button).
"""
import json, os, re, sys, html, subprocess, tempfile, threading, http.server, functools, socketserver

root = os.getcwd(); here = os.path.dirname(os.path.abspath(__file__))
key = sys.argv[1]
d = json.load(open(os.path.join(here, "iwk", key + ".json")))
cat = json.load(open(os.path.join(here, "catalog.json")))
hosted = json.load(open(os.path.join(here, "decks-hosted.json")))
lab = next(l for l in cat["labs"] if l["key"] == key)
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
e = lambda s: html.escape(s or "", quote=True)
g = lab["grade"]
lab_fp = f"science-starter-pack/labs/grade-{g}/{slug(lab['title'])}/index.html"
deck_url = next((r["url"] for r in lab.get("resources", []) if r.get("type") == "slides"), None)
deck_path = hosted.get(deck_url, {}).get("path") if deck_url else None

ACK = ("This resource was made in Edmonton, in Treaty 6 territory. We acknowledge the nêhiyaw (Cree), Dene, "
       "Anishinaabe (Saulteaux), Nakota Isga (Nakota Sioux) and Niitsitapi (Blackfoot) peoples, the Métis, whose homeland this is, "
       "and the Inuit, one of whose largest communities south of the 60th parallel lives in Edmonton. We also honour all First Nations, "
       "Métis and Inuit peoples whose knowledge shapes these lands.")
PROTOCOL = ("Indigenous knowledge belongs to the nations and communities that hold it. These notes point to public, cited sources "
            "and do not speak for any nation. For deeper learning, invite an Elder or Knowledge Keeper through your school "
            "division's Indigenous education team, and follow local protocol.")

def panel():
    conns = ""
    for c in d["connections"]:
        src = " · ".join(f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])}</a>' for s in c.get("sources", []))
        peoples = ", ".join(c.get("peoples", []))
        conns += (f'<article class="cfk-card"><p class="cfk-tag">{e(c.get("scale",""))}{" · " + e(peoples) if peoples else ""}</p>'
                  f'<h3>{e(c["title"])}</h3><p>{e(c["text"])}</p>'
                  + (f'<p class="cfk-src">Source: {src}</p>' if src else "") + '</article>')
    tries = "".join(f"<li>{e(t)}</li>" for t in d.get("try", []))
    return f'''<section id="ways-of-knowing" data-cf-iwk="{e(key)}" class="cfk" aria-labelledby="cfk-h">
<style>
.cfk{{--k-bg:#F4EFE6;--k-card:#FFFFFF;--k-ink:#1B2328;--k-muted:#56616A;--k-line:#D9D1C4;--k-a:#1F5E8C;--k-b:#3A9E96;
 margin:32px auto;max-width:1120px;padding:24px;border-radius:16px;background:var(--k-bg);color:var(--k-ink);border:1px solid var(--k-line);
 font:16px/1.6 'Atkinson Hyperlegible','Segoe UI',system-ui,sans-serif;box-sizing:border-box}}
@media (prefers-color-scheme:dark){{.cfk{{--k-bg:#172129;--k-card:#1C2831;--k-ink:#E9EEF1;--k-muted:#A2AEB7;--k-line:#2C3A45;--k-a:#7DB8E4;--k-b:#5CC4B8}}}}
.cfk *{{box-sizing:border-box}}
.cfk h2{{font:800 clamp(1.4rem,3vw,1.9rem)/1.15 'Bricolage Grotesque','Segoe UI',sans-serif;margin:0 0 .4em;color:var(--k-ink)}}
.cfk h3{{font:700 1.12rem/1.25 'Bricolage Grotesque','Segoe UI',sans-serif;margin:0 0 .35em;color:var(--k-ink)}}
.cfk p{{margin:0 0 .8em}}
.cfk-eyebrow,.cfk-tag{{font:600 .74rem/1.4 'JetBrains Mono',ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--k-b);margin:0 0 .6em}}
.cfk-ack{{border-left:4px solid var(--k-b);padding:6px 0 6px 14px;color:var(--k-muted);font-size:.95rem}}
.cfk-grid{{display:grid;gap:12px;margin:14px 0}}
@media (min-width:760px){{.cfk-grid{{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}}}}
.cfk-card{{background:var(--k-card);border:1px solid var(--k-line);border-radius:12px;padding:16px}}
.cfk-src{{font-size:.85rem;color:var(--k-muted)}}
.cfk a{{color:var(--k-a)}}
.cfk ul{{margin:.2em 0 1em;padding-left:1.2em}}
.cfk-note{{font-size:.88rem;color:var(--k-muted);border-top:1px dashed var(--k-line);padding-top:10px;margin-top:6px}}
</style>
<p class="cfk-eyebrow">Indigenous ways of knowing, doing and being</p>
<h2 id="cfk-h">{e(d["heading"])}</h2>
<p class="cfk-ack">{e(ACK)}</p>
<p>{e(d["intro"])}</p>
<div class="cfk-grid">{conns}</div>
{f'<h3>Talk and think</h3><ul>{tries}</ul>' if tries else ''}
<p class="cfk-note">{e(PROTOCOL)}</p>
</section>'''

# lab page
s = open(lab_fp).read()
s = re.sub(r'<section id="ways-of-knowing" data-cf-iwk=.*?</section>', '', s, flags=re.S)
i = s.find('<p class="credit"')
if i < 0: sys.exit("credit line not found in " + lab_fp)
s = s[:i] + panel() + s[i:]
open(lab_fp, "w").write(s)

# deck slide
if deck_path:
    sd = d["slide"]
    pts = "".join(f'<div style="display:flex;gap:20px;align-items:flex-start"><span style="flex:none;width:14px;height:14px;margin-top:18px;border-radius:50%;background:#5CC4B8"></span><p style="font-size:34px;line-height:1.4">{e(p)}</p></div>' for p in sd["points"])
    slide = (f'<section id="ways-of-knowing" data-cf-iwk="{e(key)}" style="background:#14303F;color:#EEF3F5;font-family:\'Atkinson Hyperlegible\', Arial, sans-serif;padding:112px 128px 150px;display:flex;flex-direction:column;gap:36px">'
             f'<p style="font-family:\'JetBrains Mono\', \'Courier New\', monospace;font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#5CC4B8">Indigenous ways of knowing, doing and being</p>'
             f'<h2 style="font-family:\'Bricolage Grotesque\', Arial, sans-serif;font-size:72px;font-weight:800;line-height:1.08">{e(sd["title"])}</h2>'
             f'<div style="display:flex;flex-direction:column;gap:18px">{pts}</div>'
             f'<p style="position:absolute;left:128px;bottom:56px;width:1664px;font-size:22px;color:#A9C6D3">Treaty 6 territory · nêhiyaw, Dene, Anishinaabe (Saulteaux), Nakota Isga, Niitsitapi, Métis and Inuit</p>'
             f'<aside>{e(sd.get("notes",""))} {e(PROTOCOL)}</aside></section>')
    dfp = os.path.join(deck_path.strip("/"), "index.html")
    t = open(dfp).read()
    t = re.sub(r'<section id="ways-of-knowing" data-cf-iwk=.*?</section>\n?', '', t, flags=re.S)
    m = re.search(r'<div class="dk-scaler">(.*)</div></div></main>', t, re.S)
    body = m.group(1)
    last = body.rfind("<section")
    body = body[:last] + slide + "\n" + body[last:]
    t = t[:m.start(1)] + body + t[m.end(1):]
    open(dfp, "w").write(t)
    # rebuild pptx
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    tmp = tempfile.mkdtemp()
    try:
        title = re.search(r'<span class="dk-title">(.*?)</span>', t).group(1)
        pptx = os.path.join(os.path.dirname(dfp), slug(html.unescape(title)) + ".pptx")
        subprocess.run(["node", os.path.join(here, "export_pptx.js"), f"http://127.0.0.1:{srv.server_address[1]}{deck_path}", os.path.join(tmp, "s.json"), os.path.join(tmp, "img")], check=True, timeout=600)
        subprocess.run([sys.executable, os.path.join(here, "pptx_from_json.py"), os.path.join(tmp, "s.json"), pptx, html.unescape(title)], check=True, timeout=300)
    finally:
        srv.shutdown()
subprocess.run([sys.executable, os.path.join(here, "add_links.py")], check=True)
print("ok", key, lab_fp, deck_path or "(no hosted deck)")
