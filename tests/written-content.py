"""Published full sessions, independent-review seals, complete field/figure references."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_text())
canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
cases=read('content/ap/written-cases.json');reviews=read('content/ap/written-reviews.json');by_id={r['caseId']:r for r in reviews}
expected={f'ap-r07{s}-pm{n}' for s in ['a','h'] for n in range(1,12)}
assert len(cases)==22 and {c['id'] for c in cases}==expected
assert set(by_id)==expected and len(reviews)==22
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
 for p,h in {**r['sourceHashes'],**r['assetHashes']}.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,(c['id'],p)
 cursor=0
 for figure in c.get('bodyFigures',[]):
  anchor=figure['anchor'];pos=c['body'].find(anchor,cursor);assert pos>=0,(c['id'],'figure order/anchor',figure['id']);cursor=pos+len(anchor)
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
assert public['cases']==cases and manifest['cases']['fields']==total and manifest['cases']['count']==22
assert manifest['count']==800
print(f'PASS two official sessions / 22 independently reviewed cases / {total} fields / original pilot unchanged / source+asset+case hashes / figure insertion order / all field constraints / generated bank equality / AP800 retained')
