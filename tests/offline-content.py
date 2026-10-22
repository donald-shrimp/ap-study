"""Generated download inventories preserve banks and include every required image."""
import json,hashlib
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
