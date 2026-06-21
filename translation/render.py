"""Stage 5 of the translation pipeline: render the translated PDF.

Redacts the original text spans in place (keeping images, graphics, table
fills and links) and re-inserts the translated text into the identical
bounding boxes using metric-compatible embedded fonts.

Usage::

    python translation/render.py TRANS_JSON OUT_PDF [PAGES] [SOURCE_PDF]

``PAGES`` is an optional comma-separated 0-based page filter (e.g. ``"0,4,14"``).
``SOURCE_PDF`` overrides the source document path.
"""
import fitz, json, sys, html as htmllib

DEFAULT_SRC = "/root/.claude/uploads/0c155b62-5bbe-5506-9bc4-6ffe9b540090/35f78d18-Conditions_dimmatriculation_20262027.pdf"
SRC = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_SRC
with open("translation/blocks2.json", encoding="utf-8") as fh:
    blocks=json.load(fh)
with open("translation/runs.json", encoding="utf-8") as fh:
    runs=json.load(fh)
if len(sys.argv)>1 and sys.argv[1]:
    with open(sys.argv[1], encoding="utf-8") as fh:
        TR=json.load(fh)
else:
    TR={}
OUT=sys.argv[2] if len(sys.argv)>2 else "translation/out.pdf"
only=(
    {int(x.strip()) for x in sys.argv[3].split(",") if x.strip()}
    if len(sys.argv)>3 and sys.argv[3].strip()
    else None
)

def tr(rid):
    """Return the translated text for run ``rid`` (falls back to the original)."""
    return TR.get(str(rid), runs[rid])

FAM={"arial":"LibSans","calibri":"Carlito","cambria":"Caladea",
     "mono":"LibMono","symbol":"LibSans"}
FONTDIR="translation/fonts"
ARCH=fitz.Archive(FONTDIR)
def face(fam,fn):
    """Unused helper kept for reference: build a 4-variant @font-face block."""
    return ("@font-face{font-family:%s;src:url(%s);font-weight:normal;font-style:normal}"
            "@font-face{font-family:%s;src:url(%s-b);font-weight:bold;font-style:normal}"
            "@font-face{font-family:%s;src:url(%s-i);font-weight:normal;font-style:italic}"
            "@font-face{font-family:%s;src:url(%s-bi);font-weight:bold;font-style:italic}")
FONTCSS="".join([
 "@font-face{font-family:LibSans;src:url(LiberationSans-Regular.ttf)}",
 "@font-face{font-family:LibSans;font-weight:bold;src:url(LiberationSans-Bold.ttf)}",
 "@font-face{font-family:LibSans;font-style:italic;src:url(LiberationSans-Italic.ttf)}",
 "@font-face{font-family:LibSans;font-weight:bold;font-style:italic;src:url(LiberationSans-BoldItalic.ttf)}",
 "@font-face{font-family:Carlito;src:url(Carlito-Regular.ttf)}",
 "@font-face{font-family:Carlito;font-weight:bold;src:url(Carlito-Bold.ttf)}",
 "@font-face{font-family:Carlito;font-style:italic;src:url(Carlito-Italic.ttf)}",
 "@font-face{font-family:Carlito;font-weight:bold;font-style:italic;src:url(Carlito-BoldItalic.ttf)}",
 "@font-face{font-family:Caladea;src:url(Caladea-Regular.ttf)}",
 "@font-face{font-family:Caladea;font-weight:bold;src:url(Caladea-Bold.ttf)}",
 "@font-face{font-family:Caladea;font-style:italic;src:url(Caladea-Italic.ttf)}",
 "@font-face{font-family:Caladea;font-weight:bold;font-style:italic;src:url(Caladea-BoldItalic.ttf)}",
 "@font-face{font-family:LibMono;src:url(LiberationMono-Regular.ttf)}",
 "@font-face{font-family:LibMono;font-weight:bold;src:url(LiberationMono-Bold.ttf)}",
 "@font-face{font-family:LibMono;font-style:italic;src:url(LiberationMono-Italic.ttf)}",
 "@font-face{font-family:LibMono;font-weight:bold;font-style:italic;src:url(LiberationMono-BoldItalic.ttf)}",
 "*{margin:0;padding:0}",
])
def hexcol(c):
    """Convert a PyMuPDF integer colour to a ``#rrggbb`` CSS string."""
    return "#%06x"%(c & 0xFFFFFF)

def style_css(st):
    """Build the inline CSS for a run's style dict (size/family/colour/etc.)."""
    s=[f"font-size:{st['size']}pt",f"font-family:{FAM[st['fam']]}",f"color:{hexcol(st['color'])}"]
    if st["bold"]: s.append("font-weight:bold")
    if st["italic"]: s.append("font-style:italic")
    if st.get("sc"): s.append("font-variant:small-caps")
    if st["link"] or st["linkpage"] is not None: s.append("text-decoration:underline")
    return ";".join(s)

def build_html(b):
    """Render one block's items into an HTML fragment for ``insert_htmlbox``."""
    align="justify" if b["flow"] else "left"
    out=[]
    for it in b["items"]:
        if it["t"]=="br": out.append("<br>")
        elif it["t"]=="para": out.append("<br><br>")
        else:
            txt=htmllib.escape(tr(it["rid"]))
            out.append(f'<span style="{style_css(it["st"])}">{txt}</span>')
    return f'<div style="text-align:{align};margin:0;padding:0;line-height:1.0">{"".join(out)}</div>'

doc=fitz.open(SRC)
errors=[]
for pno,page in enumerate(doc):
    if only and pno not in only: continue
    pb=[b for b in blocks if b["page"]==pno]
    link_rects=[fitz.Rect(l["from"]) for l in page.get_links()]
    underlines=[]
    for d in page.get_drawings():
        r=fitz.Rect(d["rect"])
        if r.height<=3.0 and r.width>=6 and any(r.intersects(lr) and r.y0>=lr.y0-1 for lr in link_rects):
            underlines.append(r)
    for b in pb:
        for rc in b["spanrects"]:
            rect=fitz.Rect(rc)
            if not rect.is_empty: page.add_redact_annot(rect, fill=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                          graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                          text=fitz.PDF_REDACT_TEXT_REMOVE)
    for r in underlines:
        page.draw_rect(fitz.Rect(r.x0-0.5,r.y0-0.5,r.x1+0.5,r.y1+1.0), color=None, fill=(1,1,1))
    for b in pb:
        x0,y0,x1,y1=b["bbox"]
        rect=fitz.Rect(x0-0.6,y0-1.0,x1+1.5,y1+1.5)
        try:
            page.insert_htmlbox(rect, build_html(b), css=FONTCSS, archive=ARCH, scale_low=0.4)
        except Exception as e:
            errors.append((pno, b.get("bbox"), str(e)))
if errors:
    for p, bbox, err in errors:
        print(f"ERR page={p} bbox={bbox} err={err}", file=sys.stderr)
    raise SystemExit(1)
doc.save(OUT, garbage=4, deflate=True)
print("saved",OUT)
