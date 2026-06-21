"""Stage 3 of the translation pipeline: classify runs needing translation.

Reads ``translation/runs.json`` and writes ``translation/need.tsv`` listing the
``index<TAB>text`` pairs of runs that contain genuine translatable text (i.e.
not pure numbers, punctuation, URLs or short codes), which a human then
translates into the ``tr_*.tsv`` files.
"""
import json, re, csv, os
with open("translation/runs.json", encoding="utf-8") as fh:
    runs=json.load(fh)
def trivial(t):
    """Return True if run text ``t`` needs no translation (numbers/codes/URLs)."""
    s=t.strip()
    if s=="" : return True
    if re.fullmatch(r'[\d\W_]+', s): return True           # only digits/punct/space
    if s.startswith("http://") or s.startswith("https://") or s.startswith("www."): return True
    if re.fullmatch(r'[•▪◦·\-–—.…\s]+', s): return True
    # short codes / acronyms
    if s in {"ECUS","UNIGE","ECTS","CMS","HES-SO","DEFLE","EPF","CUSO","NSC","KCSE","NB","CH","UE","EU"}: return True
    if re.fullmatch(r'[A-Z]{1,6}', s): return True
    if re.fullmatch(r'\d+\s*[/.]\s*\d+.*', s) and len(s)<14: return True   # grades like 12/20
    return False
need=[(i,t) for i,t in enumerate(runs) if not trivial(t)]
print("total runs:",len(runs),"need-translation:",len(need),
      "chars-to-translate:",sum(len(t) for _,t in need))
with open("translation/need.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.writer(f, delimiter="\t", lineterminator="\n")
    for i,t in need:
        w.writerow([i,t])
print("need.tsv bytes:",os.path.getsize("translation/need.tsv"))
