import json, re, glob
runs=json.load(open("translation/runs.json"))
tr={}
for fn in sorted(glob.glob("translation/tr_*.tsv")):
    for line in open(fn):
        line=line.rstrip("\n")
        if not line or "\t" not in line: continue
        rid,pt=line.split("\t",1)
        try: rid=int(rid)
        except: continue
        tr[rid]=pt
DOT=re.compile(r'(\s*\.{3,}[\s.]*\d+\s*)$')
def lead_ws(s):  return s[:len(s)-len(s.lstrip())]
def trail_ws(s): return s[len(s.rstrip()):]
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
json.dump(out, open("translation/trans.json","w"), ensure_ascii=False)
print("runs:",len(runs),"translated:",len(tr))
