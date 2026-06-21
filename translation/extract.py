"""Stage 1 of the translation pipeline: extract styled text runs.

Opens the source PDF and writes ``translation/blocks.json`` containing, for
every page, the text blocks as structured run records (text, bbox, font size,
colour, bold/italic, font family, hyperlink target) plus per-block alignment
and reflow heuristics.

Usage::

    python translation/extract.py [SOURCE_PDF]

The source PDF path may be passed as the first CLI argument; otherwise it falls
back to the document this pipeline was built for.
"""
import sys
import fitz, json, statistics

DEFAULT_SRC = "/root/.claude/uploads/0c155b62-5bbe-5506-9bc4-6ffe9b540090/35f78d18-Conditions_dimmatriculation_20262027.pdf"
SRC = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
doc = fitz.open(SRC)

def is_bold(s):
    """Return True if span ``s`` is bold (by render flag or font name)."""
    return bool(s["flags"] & 16) or "Bold" in s["font"] or "bold" in s["font"].lower()
def is_italic(s):
    """Return True if span ``s`` is italic/oblique (by render flag or font name)."""
    return bool(s["flags"] & 2) or "Italic" in s["font"] or "Oblique" in s["font"]
def fam(font):
    """Normalise a raw font name to a coarse family key used by the renderer."""
    f=font.lower()
    if "courier" in f: return "mono"
    if "cambria" in f: return "cambria"
    if "times" in f or "georgia" in f or "serif" in f: return "cambria"
    if "symbol" in f: return "symbol"
    if "calibri" in f: return "calibri"
    if "aptos" in f: return "calibri"
    return "arial"

blocks_out=[]
for pno,page in enumerate(doc):
    links=page.get_links()
    link_rects=[(fitz.Rect(l["from"]), l.get("uri","")) for l in links if l.get("kind")==2 or l.get("uri") or l.get("page") is not None]
    # include internal links too
    link_rects=[(fitz.Rect(l["from"]), l) for l in links]
    d=page.get_text("dict")
    for b in d["blocks"]:
        if b.get("type",0)!=0: continue
        lines=b["lines"]
        # build runs by merging adjacent same-style spans within block, tracking line breaks
        block_runs=[]
        line_fills=[]
        block_x0=b["bbox"][0]; block_x1=b["bbox"][2]
        bw=block_x1-block_x0
        line_objs=[]
        for li,l in enumerate(lines):
            spans=[s for s in l["spans"]]
            if not spans: continue
            lx0=min(s["bbox"][0] for s in spans); lx1=max(s["bbox"][2] for s in spans)
            if bw>1: line_fills.append((lx1-lx0)/bw)
            runs=[]
            for s in spans:
                if s["text"]=="" : continue
                r=fitz.Rect(s["bbox"])
                link=None
                for lr,ld in link_rects:
                    if r.intersects(lr) and (r & lr).get_area() > 0.4*r.get_area():
                        link=ld; break
                col=s["color"]
                runs.append({
                    "text":s["text"],
                    "bbox":[round(x,1) for x in s["bbox"]],
                    "size":round(s["size"],1),
                    "color":col,
                    "bold":is_bold(s),
                    "italic":is_italic(s),
                    "fam":fam(s["font"]),
                    "link": (link.get("uri") if link else None),
                    "linkpage": (link.get("page") if (link and link.get("kind")==1) else None),
                })
            line_objs.append(runs)
        if not line_objs: continue
        # alignment / reflow detection
        nonlast=line_fills[:-1] if len(line_fills)>1 else line_fills
        reflow = len(line_objs)>1 and bw>180 and (min(nonlast) if nonlast else 0) > 0.78
        # center detection
        align="left"
        # justify if reflow and fills high
        if reflow:
            align="justify"
        blocks_out.append({
            "page":pno,
            "bbox":[round(x,1) for x in b["bbox"]],
            "align":align,
            "reflow":reflow,
            "lines":line_objs,
        })

with open("translation/blocks.json", "w", encoding="utf-8") as fh:
    json.dump(blocks_out, fh, ensure_ascii=False)
print("blocks:",len(blocks_out))
