#!/usr/bin/env python3
"""Integrate one completely approved annual batch, preserving published cases."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'content/ap/written-drafts/2021-2023'
def read(path):return json.loads(path.read_text())
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def seal(value):return hashlib.sha256(canonical(value)).hexdigest()
def checked_path(path):
 p=Path(path)
 assert not p.is_absolute() and '..' not in p.parts,('invalid evidence path',path)
 return ROOT/p

def prepare(year):
 progress=read(BASE/'progress.json');integrated=progress['integratedYears']
 assert integrated in [[],[2023],[2023,2022]],'All annual batches already integrated or invalid order'
 assert year==[2023,2022,2021][len(integrated)],'Integrate newest remaining year first'
 cases=read(ROOT/'content/ap/written-cases.json');reviews=read(ROOT/'content/ap/written-reviews.json')
 topics={t['id'] for t in read(ROOT/'content/ap/qualification.json')['topics']}
 assert len(cases)==len(reviews)==44+22*len(integrated)
 assert len({c['id'] for c in cases})==len(cases) and len({r['caseId'] for r in reviews})==len(reviews)
 fixed=read(BASE/'preserved-2024-2025.json')
 assert len(fixed['cases'])==len(fixed['reviews'])==44
 for key,rows,idkey in [('cases',cases,'id'),('reviews',reviews,'caseId')]:
  by_id={v[idkey]:v for v in rows}
  for cid,digest in fixed[key].items():assert cid in by_id and seal(by_id[cid])==digest,('published material changed',cid)
 pending=[]
 for season,era in [('autumn','a'),('spring','h')]:
  folder=BASE/f'reviewer-{year}-{season}'
  for n in range(1,12):
   cid=f'ap-r{year-2018:02}{era}-pm{n}';c=read(folder/f'approved-case-{cid}.json');r=read(folder/f'review-{cid}.json')
   assert c['id']==r['caseId']==cid and c['version']==r['version']
   assert c['status']=='reviewed' and r['status']=='approved' and c['author']==r['author']!=r['reviewer']
   assert r['canonicalCaseSHA256']==seal(c),(cid,'review seal mismatch')
   assert c['topicId'] in topics,(cid,'unknown topic',c['topicId'])
   assert c['qualificationId']=='ap' and c['examPartId']=='written' and c['sourceKind']=='official'
   for kind in ['qs','ans','cmnt']:
    filename=f'{year}r{year-2018:02}{era}_ap_pm_{kind}.pdf'
    assert any(Path(p).name==filename for p in r['sourceHashes']),(cid,'missing matching official PDF',kind)
    assert any(u.startswith('https://www.ipa.go.jp/') and u.endswith('/'+filename) for u in c['sourceRefs']),(cid,'incorrect source URL',kind)
   assert set(c['sourceImages']+[f['image'] for f in c.get('bodyFigures',[])])<=set(r['assetHashes'])
   for path,digest in {**r['sourceHashes'],**r['assetHashes']}.items():assert hashlib.sha256(checked_path(path).read_bytes()).hexdigest()==digest,(cid,path)
   draft=read(BASE/f'author-{year}-{season}'/f'{cid}.json');normalized=dict(c);normalized['status']=draft['status'];normalized['authoringStatus']=draft['authoringStatus']
   assert normalized==draft,(cid,'approved content differs from latest author draft')
   pending.append((c,r))
 assert not {c['id'] for c,_ in pending}&{c['id'] for c in cases}
 cases.extend(c for c,_ in pending);reviews.extend(r for _,r in pending)
 progress.update(updatedAt=datetime.now(timezone.utc).isoformat(),integratedYears=integrated+[year],status='integrated_under_verification',totalCases=len(cases),totalItems=sum(len(c['items']) for c in cases),totalFields=sum(len(i['fields']) for c in cases for i in c['items']),totalFigures=sum(len(c.get('bodyFigures',[])) for c in cases))
 return cases,reviews,progress

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--year',type=int,required=True,choices=[2023,2022,2021]);parser.add_argument('--register',action='store_true');args=parser.parse_args()
 cases,reviews,progress=prepare(args.year)
 if args.register:
  for path,value in [(ROOT/'content/ap/written-cases.json',cases),(ROOT/'content/ap/written-reviews.json',reviews),(BASE/'progress.json',progress)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 print(('Registered' if args.register else 'Validated; use --register to write'),args.year,'=>',len(cases),'cases /',progress['totalFields'],'fields; all approved seals and existing44 preserved')
if __name__=='__main__':main()
