#!/usr/bin/env python3
"""Usage: python3 _build/pptx_from_json.py <slides.json> <out.pptx> <title>"""
import json, sys, os
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn

data = json.load(open(sys.argv[1])); out = sys.argv[2]; title = sys.argv[3]
PX = 6350  # EMU per CSS px: 1920 px = 13.333 in
prs = Presentation(); prs.slide_width = Emu(1920 * PX); prs.slide_height = Emu(1080 * PX)
prs.core_properties.title = title; prs.core_properties.author = "Dr. Lance Pedersen"
blank = prs.slide_layouts[6]
E = lambda v: Emu(int(round(v * PX)))
rgb = lambda c: RGBColor(int(c["r"]), int(c["g"]), int(c["b"]))
def alpha(shape_fill_el, a):
    if a is None or a >= 0.999: return
    srgb = shape_fill_el.find(qn("a:srgbClr"))
    if srgb is not None:
        el = srgb.makeelement(qn("a:alpha"), {"val": str(int(a * 100000))}); srgb.append(el)
KIND = {"rect": MSO_SHAPE.RECTANGLE, "arrow-right": MSO_SHAPE.RIGHT_ARROW, "arrow-left": MSO_SHAPE.LEFT_ARROW,
        "arrow-up": MSO_SHAPE.UP_ARROW, "arrow-down": MSO_SHAPE.DOWN_ARROW, "circle": MSO_SHAPE.OVAL, "ellipse": MSO_SHAPE.OVAL,
        "triangle": MSO_SHAPE.ISOSCELES_TRIANGLE, "diamond": MSO_SHAPE.DIAMOND}
ALIGN = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT, "end": PP_ALIGN.RIGHT, "justify": PP_ALIGN.JUSTIFY}
for sd in data["slides"]:
    s = prs.slides.add_slide(blank)
    if sd.get("bg"):
        f = s.background.fill; f.solid(); f.fore_color.rgb = rgb(sd["bg"])
    for sh in sd["shapes"]:
        if sh["kind"] == "line":
            ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(sh["x1"]), E(sh["y1"]), E(sh["x2"]), E(sh["y2"]))
            ln.line.color.rgb = rgb(sh["c"]); ln.line.width = Pt(max(sh["w"] * 0.5, 0.25)); continue
        if sh["w"] < 1 or sh["h"] < 1: continue
        kind = KIND.get(sh["kind"], MSO_SHAPE.RECTANGLE)
        if kind == MSO_SHAPE.RECTANGLE and sh.get("rad", 0) > 0: kind = MSO_SHAPE.ROUNDED_RECTANGLE
        shp = s.shapes.add_shape(kind, E(sh["x"]), E(sh["y"]), E(sh["w"]), E(sh["h"]))
        shp.shadow.inherit = False
        if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
            shp.adjustments[0] = min(0.5, sh["rad"] / max(1, min(sh["w"], sh["h"])))
        if sh.get("fill"):
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(sh["fill"])
            alpha(shp.fill._xPr.find(qn("a:solidFill")), sh["fill"].get("a"))
        else: shp.fill.background()
        if sh.get("line"):
            shp.line.color.rgb = rgb(sh["line"]["c"]); shp.line.width = Pt(max(sh["line"]["w"] * 0.5, 0.25))
        else: shp.line.fill.background()
        shp.text_frame.text = ""
    for pc in sd.get("pics", []):
        if pc.get("file") and os.path.exists(pc["file"]):
            s.shapes.add_picture(pc["file"], E(pc["x"]), E(pc["y"]), E(pc["w"]), E(pc["h"]))
    for t in sd["texts"]:
        if not t["runs"] or t["w"] < 2: continue
        w = t["w"] * 1.08 + 6
        x = t["x"] - (w - t["w"]) / 2 if t["align"] == "center" else (t["x"] - (w - t["w"]) if t["align"] in ("right", "end") else t["x"])
        tb = s.shapes.add_textbox(E(x), E(t["y"]), E(w), E(max(t["h"], 10)))
        tf = tb.text_frame; tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.TOP
        para = tf.paragraphs[0]; first = True
        def setp(pp):
            pp.alignment = ALIGN.get(t["align"], PP_ALIGN.LEFT)
            if t.get("lh"): pp.line_spacing = round(min(max(t["lh"], 0.8), 3) * 0.95, 2)
        setp(para)
        for r in t["runs"]:
            parts = r["t"].split("\n")
            for i, piece in enumerate(parts):
                if i > 0:
                    para = tf.add_paragraph(); setp(para)
                if not piece: continue
                run = para.add_run(); run.text = piece
                fo = run.font; fo.size = Pt(round(r["size"] * 0.5, 1)); fo.bold = r.get("bold"); fo.italic = r.get("italic")
                if r.get("font"): fo.name = r["font"]
                if r.get("color"): fo.color.rgb = rgb(r["color"])
                if t.get("ls"):
                    run._r.get_or_add_rPr().set("spc", str(int(t["ls"] * 0.5 * 100)))
                if r.get("sup") or r.get("sub"):
                    run._r.get_or_add_rPr().set("baseline", "30000" if r.get("sup") else "-25000")
    if sd.get("notes"):
        s.notes_slide.notes_text_frame.text = sd["notes"]
prs.save(out)
print("saved", out, len(data["slides"]), "slides")
