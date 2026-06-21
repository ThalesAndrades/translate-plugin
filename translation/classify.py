import json, re
runs=json.load(open("translation/runs.json"))
def trivial(t):
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
with open("translation/need.tsv","w") as f:
    for i,t in need: f.write(f"{i}\t{t}\n")
import os
print("need.tsv bytes:",os.path.getsize("translation/need.tsv"))
