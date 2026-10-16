"""Published full sessions, preserved previous cases and complete independent-review seals."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_text())
canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
cases=read('content/ap/written-cases.json');reviews=read('content/ap/written-reviews.json');by_id={r['caseId']:r for r in reviews}
progress=read('content/ap/written-drafts/2021-2023/progress.json');years=[6,7]+[y-2018 for y in progress['integratedYears']]
assert progress['integratedYears'] in [[],[2023],[2023,2022],[2023,2022,2021]]
expected={f'ap-r0{year}{s}-pm{n}' for year in years for s in ['a','h'] for n in range(1,12)}
COUNT=len(expected)
assert len(cases)==COUNT and {c['id'] for c in cases}==expected
assert set(by_id)==expected and len(reviews)==COUNT
preserved=read('content/ap/written-drafts/2021-2023/preserved-2024-2025.json')
assert len(preserved['cases'])==44 and len(preserved['reviews'])==44
assert set(preserved['cases'])<=expected and set(preserved['reviews'])<=expected
for c in cases:
 if c['id'] in preserved['cases']:assert hashlib.sha256(canonical(c)).hexdigest()==preserved['cases'][c['id']],c['id']
for r in reviews:
 if r['caseId'] in preserved['reviews']:assert hashlib.sha256(canonical(r)).hexdigest()==preserved['reviews'][r['caseId']],r['caseId']
pilot=next(c for c in cases if c['id']=='ap-r07h-pm1')
assert hashlib.sha256(canonical(pilot)).hexdigest()=='5de9a5445337d04da197d262105611c1b1f996af7ee48dab5be1e4667f55dcfb','existing pilot must remain unchanged'
config=read('content/ap/qualification.json');topics={t['id'] for t in config['topics']};total=0
for c in cases:
 r=by_id[c['id']];assert c['status']=='reviewed' and r['status']=='approved' and r['author']!=r['reviewer']
 assert r['canonicalCaseSHA256']==hashlib.sha256(canonical(c)).hexdigest(),c['id']
 assert c['topicId'] in topics and c['qualificationId']=='ap' and c['examPartId']=='written'
 assert c['sourceKind']=='official' and c['sourceRefs'] and any(u.endswith('_qs.pdf') for u in c['sourceRefs']) and any(u.endswith('_ans.pdf') for u in c['sourceRefs']) and any(u.endswith('_cmnt.pdf') for u in c['sourceRefs'])
 assert len(c['sourcePages'])==len(c['sourceImages']) and c['body'] and c['items']
 for kind in ['qs','ans','cmnt']:
  assert any(p.endswith('_'+kind+'.pdf') for p in r['sourceHashes']),c['id']
 for p,h in {**r['sourceHashes'],**r['assetHashes']}.items():
  assert not Path(p).is_absolute() and '..' not in Path(p).parts,(c['id'],'nonportable evidence path',p)
  assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,(c['id'],p)
 cursor=0
 for figure in c.get('bodyFigures',[]):
  anchor=figure['anchor'];assert c['body'].count(anchor)==1,(c['id'],'nonunique figure anchor',figure['id']);pos=c['body'].find(anchor,cursor);assert pos>=0,(c['id'],'figure order/anchor',figure['id']);cursor=pos+len(anchor)
  assert figure['image'] in r['assetHashes'] and figure['alt'] and figure['caption']
 for path in c['sourceImages']:assert path in r['assetHashes'] and path in c['imageSizes']
 known=c.get('bodyRefs',{})
 for item in c['items']:
  assert item['prompt'] and item['fields']
  for ref in item.get('bodyRefs',[]):assert ref in known,(c['id'],item['id'],ref)
  for field in item['fields']:
   assert field['explanation'] and field['rubric'] and field['referenceAnswers'];total+=1
   if field['type']!='singleChoice':assert all(len(a)<=field['maxLength'] for a in field['referenceAnswers']),(c['id'],item['id'],field['id'])
   assert field['type']!='freeText' or field['grading']['method']=='self'
manifest=read('data/qualifications/ap/manifest.json');public=read('data/qualifications/ap/'+manifest['cases']['url'])
assert public['cases']==cases and manifest['cases']['fields']==total and manifest['cases']['count']==COUNT
assert manifest['count']==800
print(f'PASS {len(years)*2} official sessions / {COUNT} independently reviewed cases / {total} fields / original pilot unchanged / source+asset+case hashes / figure insertion order / all field constraints / generated bank equality / AP800 retained')
