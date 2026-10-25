"""Reject broken image-reference metadata and verify its independent review."""
import copy,hashlib,json,tempfile
from pathlib import Path
from fp2_fixtures import prepare,builder,write,ROOT
read=lambda p:json.loads(p.read_text())
with tempfile.TemporaryDirectory(prefix='body-reference-contract-') as d:
 root=Path(d);cfg,normal,cases=prepare(root);base=root/'content/fp2';c=cases[0];figure=c['bodyFigures'][0]
 c['bodyRefs']={'figure':{'anchor':figure['caption'],'sourcePages':[1]},'inside':{'text':'合成画像の中の文字','sourcePages':[1]},'paragraph':{'text':'本文の文字','sourcePages':[1]},'elsewhere':{'text':'別ページの文字','sourcePages':[2]}}
 reviews=read(base/'practical-reviews.json');reviews[0]['canonicalCaseSHA256']=builder.diagnostic_digest(c);write(base/'practical-cases.json',cases);write(base/'practical-reviews.json',reviews)
 catalog=read(base/'case-catalog.json');catalog['entries'][0]['referenceTargets']={'inside':'figure'};write(base/'case-catalog.json',catalog);builder.compile_qualification(root,'fp2')
 for targets in [{'unknown':'figure'},{'inside':'unknown'},{'inside':'paragraph'},{'elsewhere':'figure'},{'inside':['figure']},{'inside':'inside'}]:
  bad=copy.deepcopy(catalog);bad['entries'][0]['referenceTargets']=targets;write(base/'case-catalog.json',bad)
  try:builder.compile_qualification(root,'fp2')
  except (ValueError,AssertionError):pass
  else:raise AssertionError('invalid reference metadata accepted: '+repr(targets))
reviews={}
for path in sorted((ROOT/'docs/audits').glob('body-reference-targets-review-*.json')):
 r=read(path);assert r['status']=='approved' and r['reviewer']!=r['metadataAuthor']
 for mapping in r['mappings']:reviews[(mapping['caseId'],mapping['referenceKey'])]=mapping
count=0
for q in ['ap','fp2']:
 cfg=read(ROOT/f'content/{q}/qualification.json');cases={c['id']:c for c in read(ROOT/cfg['caseSource'])};catalog=read(ROOT/cfg['caseCatalogSource'])
 for entry in catalog['entries']:
  c=cases[entry['caseId']]
  for source,target in entry.get('referenceTargets',{}).items():
   r=reviews[(c['id'],source)];assert r['status']=='approved' and r['targetId']==target
   assert r['reference']==c['bodyRefs'][source] and r['targetReference']==c['bodyRefs'][target]
   image=next(f['image'] for f in c['bodyFigures'] if f['caption']==(c['bodyRefs'][target].get('text') or c['bodyRefs'][target].get('anchor')))
   assert r['image']==image and r['imageSHA256']==hashlib.sha256((ROOT/image).read_bytes()).hexdigest();count+=1
print('PASS image-reference metadata contracts / unknown, non-figure, wrong page and malformed targets rejected / independently reviewed mappings:',count)
