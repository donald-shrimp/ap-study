"""Acceptance of empty unpublished FP scaffolding, drafts, evidence and case-only catalogs."""
import copy,importlib.util,json,subprocess,tempfile
from pathlib import Path
from fp2_fixtures import prepare,builder,write,ROOT
from material_contracts import decimal_value,validate_numeric,validate_legal
spec=importlib.util.spec_from_file_location('delivery_check',ROOT/'tools/check-fp2-delivery.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
assert 'fp2' not in json.loads((ROOT/'content/qualifications.json').read_text())['qualifications']
assert 'fp2' not in {q['id'] for q in json.loads((ROOT/'data/qualifications/catalog.json').read_text())['qualifications']}
assert delivery.check(ROOT)=={'questions':0,'cases':0,'fields':0,'mode':'draft structure only; not approved'}
for text,expected in [('１，４９０，０００','1490000'),('0.4350','0.435'),('1,49',None),('149万円',None),('1e6',None),('①',None)]:assert decimal_value(text)==expected
with tempfile.TemporaryDirectory(prefix='fp2-content-') as d:
 root=Path(d);cfg,normal,cases=prepare(root);base=root/'content/fp2'
 result=delivery.check(root,True);assert (result['questions'],result['cases'],result['fields'])==(1,2,7)
 m=json.loads((root/'data/qualifications/fp2/manifest.json').read_text());assert [t['examPartId'] for t in m['studyTargets']]==['objective','jafp-practical','kinzai-personal'];assert m['studyTargets'][1]['count']==1 and m['studyTargets'][1]['countLabel']=='問';assert len(m['studyTargets'])==3;assert sum(p['practiceAvailable'] for p in m['examParts'])==3
 for change in [lambda c:c['items'][0]['fields'][-1]['numeric'].update(decimalPlaces=-1),lambda c:c['items'][0]['fields'][-1]['grading'].update(method='self'),lambda c:c['sourceRecord'].update(legalAsOf='2026-02-30'),lambda c:c['legalReview'].update(status='current',sourceRefs=[])]:
  broken=copy.deepcopy(cases);change(broken[0]);write(base/'practical-cases.json',broken)
  try:delivery.check(root,True)
  except (ValueError,AssertionError,subprocess.CalledProcessError):pass
  else:raise AssertionError('Bad numeric/legal material accepted')
 write(base/'practical-cases.json',cases)
 broken=copy.deepcopy(normal);broken['sourceRecord']['questionSha256']='f'*64;write(base/'questions.json',[broken])
 try:delivery.check(root,True)
 except (ValueError,AssertionError):pass
 else:raise AssertionError('Source hash mismatch accepted')
with tempfile.TemporaryDirectory(prefix='fp2-drafts-') as d:
 root=Path(d);cfg,normal,cases=prepare(root,draft=True);before=(root/'content/fp2/practical-cases.json').read_bytes();assert delivery.check(root)['cases']==2;assert (root/'content/fp2/practical-cases.json').read_bytes()==before
 try:delivery.check(root,True)
 except (ValueError,AssertionError):pass
 else:raise AssertionError('Unreviewed draft accepted as reviewed')
with tempfile.TemporaryDirectory(prefix='fp2-case-only-') as d:
 root=Path(d);prepare(root,cases_only=True);m=json.loads((root/'data/qualifications/fp2/manifest.json').read_text());assert m['count']==0 and len(m['studyTargets'])==2;assert all(t['unit']=='cases' for t in m['studyTargets'])
print('PASS unpublished FP scaffolding / draft is read-only and never approved / reviewed source hashes / legal and numeric validation / three scoped targets / case-only catalog')
