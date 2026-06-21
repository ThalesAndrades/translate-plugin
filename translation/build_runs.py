import json, statistics
blocks=json.load(open("translation/blocks.json"))

def skey(r): return (r["size"],r["color"],r["bold"],r["italic"],r["fam"],r["link"],r["linkpage"])
def unionbb(a,b): return [min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]

run_texts={}; run_list=[]
def run_id(t):
    if t not in run_texts:
        run_texts[t]=len(run_list); run_list.append(t)
    return run_texts[t]

out=[]
for b in blocks:
    x0,y0,x1,y1=b["bbox"]; bw=x1-x0
    # per-line merged runs + blank flag + fill
    L=[]
    for line in b["lines"]:
        runs=[]; cur=None
        for r in line:
            if r["text"]=="": continue
            if cur and skey(cur)==skey(r):
                cur["text"]+=r["text"]; cur["bbox"]=unionbb(cur["bbox"],r["bbox"])
            else:
                if cur: runs.append(cur)
                cur=dict(r)
        if cur: runs.append(cur)
        # small-caps merge: single uppercase letter + following smaller uppercase run
        i=0; merged=[]
        while i < len(runs):
            r=runs[i]
            if (i+1<len(runs) and len(r["text"].strip())==1 and r["text"].strip().isalpha()
                and r["text"].strip().isupper() and runs[i+1]["text"][:1].isupper()
                and runs[i+1]["size"]<r["size"]-0.3 and runs[i+1]["color"]==r["color"]):
                nr=dict(r); nr["text"]=r["text"]+runs[i+1]["text"]
                nr["bbox"]=unionbb(r["bbox"],runs[i+1]["bbox"]); nr["smallcaps"]=True
                merged.append(nr); i+=2
            else:
                merged.append(r); i+=1
        runs=merged
        txt="".join(x["text"] for x in runs)
        blank = txt.strip()==""
        fill = ((max(x["bbox"][2] for x in runs)-min(x["bbox"][0] for x in runs))/bw) if (runs and bw>1) else 0
        L.append({"runs":runs,"blank":blank,"fill":fill})
    nonblank=[l for l in L if not l["blank"]]
    def is_bullet(txt):
        t=txt.lstrip()
        return t[:1] in ("•","◦","▪","‣","-","–") or (len(t)>=2 and t[0].isdigit() and t[1] in ".)")
    has_bullet=any(is_bullet("".join(x["text"] for x in l["runs"])) for l in nonblank)
    flow = (bw>200 and len(nonblank)>=2 and not has_bullet
            and sum(1 for l in nonblank if l["fill"]>0.85) >= max(1,len(nonblank)//2))

    items=[]   # tokens
    spanrects=[ [round(v,1) for v in s["bbox"]] for line in b["lines"] for s in line if s["text"].strip()]

    def emit_run(r):
        st={"size":r["size"],"color":r["color"],"bold":r["bold"],"italic":r["italic"],
            "fam":r["fam"],"link":r["link"],"linkpage":r["linkpage"],"sc":r.get("smallcaps",False)}
        items.append({"t":"run","rid":run_id(r["text"]),"st":st})

    if flow:
        prev=None
        started=False
        for l in L:
            if l["blank"]:
                if started: items.append({"t":"para"})
                prev=None
                continue
            for r in l["runs"]:
                if prev is not None and skey(prev)==skey(r):
                    # merge across soft wrap (de-hyphenate)
                    pt=prev["text"]
                    if pt.rstrip().endswith("-") and len(pt.rstrip())>=2 and pt.rstrip()[-2].isalpha() and r["text"][:1].islower():
                        newtext=pt.rstrip()[:-1]+r["text"]
                    else:
                        newtext=(pt if pt.endswith(" ") else pt+" ")+r["text"]
                    # update last emitted run text
                    prev["text"]=newtext; prev["bbox"]=unionbb(prev["bbox"],r["bbox"])
                    items[-1]["rid"]=run_id(newtext)
                else:
                    emit_run(r); prev=dict(r)
            started=True
    else:
        # build effective lines, merging a lone bullet marker into the following line
        eff=[]; pending=None
        for l in L:
            if l["blank"]:
                eff.append(None); continue
            runs=l["runs"]
            txt="".join(r["text"] for r in runs).strip()
            if txt in ("•","◦","▪","‣","-","–","o","*") and len(runs)<=2:
                pending=[dict(runs[0])]; pending[0]["text"]=runs[0]["text"].rstrip()+"  "
                continue
            if pending:
                runs=pending+runs; pending=None
            eff.append(runs)
        if pending: eff.append(pending)
        first=True
        for el in eff:
            if not first: items.append({"t":"br"})
            first=False
            if el is None: continue
            for r in el: emit_run(r)
    b["items"]=items; b["flow"]=flow; b["spanrects"]=spanrects
    # cleanup big fields
    for k in ("lines",): b.pop(k,None)
    out.append(b)

json.dump(out, open("translation/blocks2.json","w"), ensure_ascii=False)
json.dump(run_list, open("translation/runs.json","w"), ensure_ascii=False, indent=0)
print("blocks:",len(out),"unique runs:",len(run_list),
      "run chars:",sum(len(t) for t in run_list))
