import json, re, glob, sys
runs=json.load(open("translation/runs.json"))
# load all translation batches: lines "rid<TAB>pt"
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
out={}
missing=[]
for i,src in enumerate(runs):
    m=DOT.search(src)
    if i in tr:
        val=tr[i]
        if m:
            val=DOT.sub('', val).rstrip()+m.group(1)
        out[str(i)]=val
    else:
        # passthrough (trivial / untranslated). keep source as-is.
        out[str(i)]=src
        # record genuinely-untranslated non-trivial for reporting
json.dump(out, open("translation/trans.json","w"), ensure_ascii=False)
print("runs:",len(runs),"translated entries:",len(tr))
