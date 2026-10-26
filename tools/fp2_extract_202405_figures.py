#!/usr/bin/env python3
"""Crop official PDF pages; preserve original pixels and verify PDF SHA256."""
import hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen
import fitz
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"work/fp2/historical/202405"
KEYS=json.loads((DATA/"source-files.json").read_text())
def original(fn):
    loc=ROOT/"sources/fp2"/fn
    if loc.is_file(): b=loc.read_bytes()
    else:
        req=Request("https://www.jafp.or.jp/exam/mohan/files/"+fn,headers={"User-Agent":"Mozilla/5.0"})
        with urlopen(req,timeout=80) as fd: b=fd.read()
    actual=hashlib.sha256(b).hexdigest()
    expected=KEYS["sources/fp2/"+fn]
    if actual!=expected:raise ValueError("Original SHA256 mismatch: "+fn+" "+actual+" != "+expected)
    print("SHA verified",fn,len(b),actual,flush=True)
    return fitz.open(stream=b,filetype="pdf")
def png(doc,page,rect,out):
    p=doc[page]; r=fitz.Rect(rect)
    if not p.rect.contains(r):raise ValueError("Bad PDF crop box "+out)
    if len(p.get_text("text",clip=r).strip())<20:raise ValueError("Blank or mistaken crop: "+out)
    pix=p.get_pixmap(matrix=fitz.Matrix(2.4,2.4),clip=r,alpha=False)
    target=ROOT/out;target.parent.mkdir(parents=True,exist_ok=True);pix.save(target)
    print("Extracted",out,pix.width,pix.height,flush=True)
    return dict(width=pix.width,height=pix.height)
# name, PDF page zero-based, crop coordinates in PDF points, target practical cases
S=[
("q03-source.png",2,(54,196,384,317),[3]),
("q04-source.png",3,(54,177,543,397),[4]),
("q07-land-diagram.png",5,(54,196,542,494),[7]),
("q09-register.png",7,(54,161,542,396),[9]),
("q10-contract.png",8,(54,182,542,514),[10]),
("q20-tax-tables.png",18,(54,177,542,535),[20]),
("q21-land-diagram.png",19,(54,143,542,563),[21]),
("q22-family-diagram.png",20,(54,132,542,552),[22]),
("q23-cashflow.png",21,(54,110,542,651),[23,24]),
("q24-tuition.png",22,(54,253,542,443),[24]),
("q25-loan-terms.png",22,(54,576,542,676),[25]),
("q26-coefficients.png",23,(54,113,542,458),[26,27,28]),
("q29-amortization.png",27,(54,195,542,544),[29]),
("q30-deposits.png",28,(54,179,542,403),[30]),
("q31-insurance-terms.png",29,(54,141,542,452),[31]),
("q35-family-assets.png",33,(54,110,542,697),[35]),
("q35-family-insurance.png",34,(54,63,542,464),[35]),
("q36-withholding-slip.png",35,(54,228,542,540),[36]),
("q38-brokerage.png",37,(54,197,542,543),[38]),
("q40-leave-calendar.png",38,(54,179,542,551),[40])]
def run():
 p=original("j2_202405_q.pdf");o=original("g2_202405_q.pdf")
 cases=json.loads((DATA/"practical-cases.json").read_text())
 questions=json.loads((DATA/"questions.json").read_text())
 if len(cases)!=40 or len(questions)!=60:raise ValueError("Unexpected number of questions")
 refs={}
 for name,page,rect,nums in S:
  asset="assets/written/fp2/202405/"+name
  png(p,page,rect,asset)
  for n in nums:
   anchor=f"【公式原本切り出し・実技問{n}・{name}】"
   refs.setdefault(n,[]).append(dict(image=asset,anchor=anchor,alt=f"日本FP協会2024年5月実技問{n}の公式PDFから直接切り出した図表",caption=f"出典：2024年5月26日日本FP協会FP2級実技試験・印刷{page+1}頁"))
 asset="assets/fp2/202405/q53-family-tree.png"
 sz=png(o,21,(54,157,542,318),asset)
 q=questions[52]
 if q["id"]!="fp2-202405-objective-q53":raise ValueError("Q53 changed")
 prefix=q["stem"].split("\n\n＜親族関係図")[0]
 if len(prefix)<30:raise ValueError("Q53 stem mismatch")
 q["stem"]=prefix;q["sourceImages"]=[asset];q["imageSizes"]=[sz];q["version"]+=1
 # For spatial questions, never replace the source diagram with a narrated geometry.
 cases[6]["body"]="建築基準法に従い、下記＜資料＞の土地に建築物を建てる場合の延べ面積（床面積の合計）の最高限度を計算しなさい。なお、記載のない事項は一切考慮しないものとする。また、解答に当たっては、解答用紙に記載されている単位に従うこと。"
 for n,imgs in refs.items():
  q=cases[n-1]
  if q["id"]!=f"fp2-202405-jafp-q{n:02d}" or q.get("bodyFigures"):raise ValueError(f"Unexpected case state {n}")
  for pic in imgs:q["body"]+="\n\n"+pic["anchor"]
  q["bodyFigures"]=imgs;q["version"]+=1
 for name,data in [("practical-cases.json",cases),("questions.json",questions)]:
  (DATA/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
 print("DONE:",len(S),"source crops; attached",sum(map(len,refs.values())),"practical references across",len(refs),"cases + objective Q53",flush=True)
if __name__=="__main__":run()
