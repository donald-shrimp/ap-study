"""Generated download inventories preserve banks and include every required image."""
import json,hashlib,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for q in ['ap','ab730']:
 root=ROOT/'data/qualifications'/q;m=json.loads((root/'manifest.json').read_text());raw=(root/m['offline']['url']).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['offline']['sha256'];o=json.loads(raw);assert len(o['groups'])==m['offline']['count'];files=o['assets'];groups=o['groups'];seen=set();fallback=[]
 for k,a in files.items():
  raw=(ROOT/k).read_bytes();assert a['bytes']==len(raw) and a['sha256']==hashlib.sha256(raw).hexdigest(),k
 for p in m['packs']:
  qs=json.loads((root/p['url']).read_text())
  for question in qs:
   g=next(g for g in groups if question['id'] in g['itemIds'] and g['unit']=='questions');seen.add(question['id']);needed=set()
   if not question.get('stem'):needed.update(question['sourceImages']);fallback.append(question['id'])
   if question.get('image'):needed.add(question['image'])
   if question.get('choicePresentation')!='codes':needed.update(c['image'] for c in question['choices'] if c.get('image'))
   assert needed<=set(g['files']),question['id']
   if question.get('stem'):assert not set(question['sourceImages'])&set(g['files']),question['id']
 assert len(seen)==m['count']
 if q=='ap':
  assert len(fallback)==2
  cases=json.loads((root/m['cases']['url']).read_text())['cases'];assert sum(g['count'] for g in groups if g['unit']=='cases')==len(cases)==88
  for c in cases:
   g=next(g for g in groups if c['id'] in g['itemIds']);assert {f['image'] for f in c.get('bodyFigures',[])}<=set(g['files']);assert not set(c['sourceImages'])&set(g['files'])
 print('PASS',q,len(seen),'questions / full SHA and sizes / required choice images / optional originals excluded / source-only',fallback)

# Two sessions without optional sourceRefs still download separately. The case
# catalog, rather than a qualification-specific ID pattern, defines the split.
from fp2_fixtures import prepare,builder,write
with tempfile.TemporaryDirectory(prefix='offline-case-sessions-') as d:
 root=Path(d);cfg,normal,cases=prepare(root);base=root/'content/fp2'
 cases[1]['examPartId']=cases[0]['examPartId']
 reviews=json.loads((base/'practical-reviews.json').read_text())
 reviews[1]['canonicalCaseSHA256']=builder.diagnostic_digest(cases[1])
 write(base/'practical-cases.json',cases);write(base/'practical-reviews.json',reviews)
 catalog=json.loads((base/'case-catalog.json').read_text())
 for n,e in enumerate(catalog['entries']):e.update(packId='session-'+str(n),packLabel='試験回'+str(n),number=1)
 write(base/'case-catalog.json',catalog);builder.build(root)
 folder=root/'data/qualifications/fp2';m=json.loads((folder/'manifest.json').read_text());o=json.loads((folder/m['offline']['url']).read_text())
 groups=[g for g in o['groups'] if g['unit']=='cases']
 assert [g['label'] for g in groups]==['試験回0','試験回1']
 assert [g['itemIds'] for g in groups]==[[c['id']] for c in cases]
 assert all(g['count']==1 for g in groups)
 assert cases[0]['bodyFigures'][0]['image'] in groups[0]['files'] and cases[0]['bodyFigures'][0]['image'] not in groups[1]['files']
print('PASS separate case-session downloads with empty sourceRefs / labels / counts / required images')
