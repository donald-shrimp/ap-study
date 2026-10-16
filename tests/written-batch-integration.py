"""Synthetic fixtures: annual publishing must fail closed without changing files."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile
REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('written_batch',REPO/'tools/integrate-written-cases.py');batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False))
with tempfile.TemporaryDirectory(prefix='hitomon-synthetic-batch-') as tmp:
 root=Path(tmp);base=root/'content/ap/written-drafts/2021-2023';batch.ROOT=root;batch.BASE=base
 write(root/'content/ap/qualification.json',{'topics':[{'id':'hardware'}]})
 old=[{'id':f'published-{i}','body':'existing synthetic material','items':[]} for i in range(44)];oldreviews=[{'caseId':c['id'],'evidence':'existing synthetic review'} for c in old]
 casefile=root/'content/ap/written-cases.json';reviewfile=root/'content/ap/written-reviews.json';progressfile=base/'progress.json'
 write(casefile,old);write(reviewfile,oldreviews);write(progressfile,{'integratedYears':[]})
 write(base/'preserved-2024-2025.json',{'cases':{c['id']:batch.seal(c) for c in old},'reviews':{r['caseId']:batch.seal(r) for r in oldreviews}})
 for era,season in [('a','autumn'),('h','spring')]:
  sources={}
  for kind in ['qs','ans','cmnt']:
   path=f'synthetic-sources/2023r05{era}_ap_pm_{kind}.pdf';p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'SYNTHETIC TEST SOURCE, NOT AN OFFICIAL PDF');sources[path]=hashlib.sha256(p.read_bytes()).hexdigest()
  for n in range(1,12):
   cid=f'ap-r05{era}-pm{n}';draft={'id':cid,'topicId':'hardware','version':1,'author':'synthetic-author','status':'draft','authoringStatus':'draft','qualificationId':'ap','examPartId':'written','sourceKind':'official','sourceRefs':['https://www.ipa.go.jp/synthetic/'+Path(p).name for p in sources],'sourceImages':[],'bodyFigures':[],'items':[]}
   c={**draft,'status':'reviewed','authoringStatus':'independently-reviewed'};r={'caseId':cid,'version':1,'author':draft['author'],'reviewer':'different-synthetic-reviewer','status':'approved','canonicalCaseSHA256':batch.seal(c),'sourceHashes':sources,'assetHashes':{}}
   write(base/f'author-2023-{season}'/f'{cid}.json',draft);write(base/f'reviewer-2023-{season}'/f'approved-case-{cid}.json',c);write(base/f'reviewer-2023-{season}'/f'review-{cid}.json',r)
 tracked=[casefile,reviewfile,progressfile];before=[p.read_bytes() for p in tracked]
 cs,rs,progress=batch.prepare(2023);assert len(cs)==len(rs)==66 and progress['integratedYears']==[2023];assert cs[:44]==old and rs[:44]==oldreviews
 def rejected(action):
  try:action()
  except (AssertionError,FileNotFoundError):pass
  else:raise AssertionError('unsafe batch admitted')
  assert [p.read_bytes() for p in tracked]==before,'validation mutated published data'
 rejected(lambda:batch.prepare(2021))
 case=base/'reviewer-2023-autumn/approved-case-ap-r05a-pm1.json';review=base/'reviewer-2023-autumn/review-ap-r05a-pm1.json';rawcase=case.read_bytes();rawreview=review.read_bytes();c=json.loads(rawcase);c['topicId']='unknown-topic';write(case,c);r=json.loads(rawreview);r['canonicalCaseSHA256']=batch.seal(c);write(review,r);rejected(lambda:batch.prepare(2023));case.write_bytes(rawcase);review.write_bytes(rawreview)
 p=base/'reviewer-2023-autumn/review-ap-r05a-pm1.json';original=p.read_bytes();r=json.loads(original)
 for patch in [{'reviewer':'synthetic-author'},{'canonicalCaseSHA256':'0'*64},{'status':'pending'}]:
  write(p,{**r,**patch});rejected(lambda:batch.prepare(2023));p.write_bytes(original)
 p.unlink();rejected(lambda:batch.prepare(2023));p.write_bytes(original)
 source=root/'synthetic-sources/2023r05a_ap_pm_qs.pdf';raw=source.read_bytes();source.write_bytes(b'tampered source');rejected(lambda:batch.prepare(2023));source.write_bytes(raw)
 p=base/'author-2023-autumn/ap-r05a-pm1.json';raw=p.read_bytes();d=json.loads(raw);d['title']='changed after approval';write(p,d);rejected(lambda:batch.prepare(2023));p.write_bytes(raw)
 write(casefile,[{**old[0],'body':'tampered published case'},*old[1:]]);before=[p.read_bytes() for p in tracked];rejected(lambda:batch.prepare(2023))
print('PASS complete annual batch preserves44; unknown topic / missing approval / same author / invalid seal / pending review / wrong order / changed source / changed draft / changed existing material rejected without mutation')
