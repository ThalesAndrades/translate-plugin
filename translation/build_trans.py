"""Stage 4 of the translation pipeline: assemble the translation map.

Loads ``translation/runs.json`` and every ``translation/tr_*.tsv`` file
(``run_id<TAB>translation``) and writes ``translation/trans.json`` mapping each
run index to its Portuguese text. Runs without a provided translation pass
through unchanged; dotted table-of-contents leaders and the source run's
leading/trailing whitespace (and elision/soft-hyphen spacing) are preserved.
"""
import json, re, glob
with open("translation/runs.json", encoding="utf-8") as fh:
    runs=json.load(fh)
tr={}
skipped=0
for fn in sorted(glob.glob("translation/tr_*.tsv")):
    with open(fn, encoding="utf-8") as fh:
        for line in fh:
            line=line.rstrip("\n")
            if not line or "\t" not in line:
                continue
            rid,pt=line.split("\t",1)
            try:
                rid=int(rid)
            except ValueError:
                skipped+=1   # malformed row id; skip but keep visibility via the count
                continue
            tr[rid]=pt
DOT=re.compile(r'(\s*\.{3,}[\s.]*\d+\s*)$')
def lead_ws(s):
    """Return the leading-whitespace prefix of ``s``."""
    return s[:len(s)-len(s.lstrip())]
def trail_ws(s):
    """Return the trailing-whitespace suffix of ``s``."""
    return s[len(s.rstrip()):]
out={}
for i,src in enumerate(runs):
    if i not in tr:
        out[str(i)]=src; continue
    core=tr[i]
    m=DOT.search(src)
    if m:
        out[str(i)]=DOT.sub('',core).rstrip()+m.group(1); continue
    lead=lead_ws(src); trail=trail_ws(src)
    if trail=="" and src.rstrip()[-1:] in ("’","'","‘","-","–","—"):
        trail=" "
    out[str(i)]=lead+core.strip()+trail
with open("translation/trans.json","w",encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False)
print("runs:",len(runs),"translated:",len(tr),"skipped malformed rows:",skipped)
