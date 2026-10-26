"""Published FP120/80 corpus plus isolated draft/evidence/case-only contracts."""
import copy,hashlib,importlib.util,json,subprocess,tempfile,jsonschema
from referencing import Registry,Resource
from pathlib import Path
from fp2_fixtures import prepare,builder,write,ROOT
from material_contracts import decimal_value,validate_numeric,validate_legal
spec=importlib.util.spec_from_file_location('delivery_check',ROOT/'tools/check-fp2-delivery.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
assert 'fp2' in json.loads((ROOT/'content/qualifications.json').read_text())['qualifications']
catalog=json.loads((ROOT/'data/qualifications/catalog.json').read_text())['qualifications']
published=next(q for q in catalog if q['id']=='fp2');assert published['count']==120
assert published['studyTargets']==[{'examPartId':'objective','label':'学科','unit':'questionAttempts','count':120},{'examPartId':'jafp-practical','label':'実技（日本FP協会）','unit':'cases','count':80,'caseLabel':'問題','countLabel':'問'}]
assert delivery.check(ROOT,True)=={'questions':120,'cases':80,'fields':136,'mode':'reviewed evidence'}
practical=ROOT/'deliveries/fp2-jafp-202605-samples'
accepted=json.loads((practical/'content/fp2/practical-cases.json').read_text())
all_registered=json.loads((ROOT/'content/fp2/practical-cases.json').read_text())
registered=[c for c in all_registered if c['id'].startswith('fp2-202605-')]
evidence={r['caseId']:r for r in json.loads((practical/'review/pr36-review-evidence.json').read_text())['cases']}
assert len(accepted)==len(registered)==len(evidence)==40
for c,d in zip(registered,accepted):
 assert c=={**d,'status':'reviewed'} and builder.diagnostic_digest(d)==evidence[c['id']]['acceptedDraftSHA256']
 for path,digest in evidence[c['id']]['assetHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
assert sum(len(i['fields']) for c in registered for i in c['items'])==68
assert sum(f['type']=='numeric' for c in registered for i in c['items'] for f in i['fields'])==22
all_raw=json.loads((ROOT/'content/fp2/questions.json').read_text());raw=[q for q in all_raw if q['packId']=='202605'];draft=json.loads((ROOT/'delivery/content/fp2/questions.json').read_text())
assert len(raw)==len(draft)==60
revision=ROOT/'work/fp2/revisions/202605-objective-v2'
revised=json.loads((revision/'questions.json').read_text())
question_schema=json.loads((ROOT/'schemas/question-format.v1.json').read_text());legal_schema=json.loads((ROOT/'schemas/legal-context.v1.json').read_text())
registry=Registry().with_resource(legal_schema['$id'],Resource.from_contents(legal_schema))
validator=jsonschema.Draft202012Validator(question_schema,registry=registry)
for q in revised+all_raw:validator.validate(q)
review=json.loads((revision/'review/independent-review.json').read_text())
revised_evidence={r['questionId']:r for r in review['questions']}
previous=json.loads((revision/'review/previous-publication-reviews.json').read_text())
historical=[{**d,'enrichment':'reviewed'} for d in draft]
cfg=json.loads((ROOT/'content/fp2/qualification.json').read_text())
builder.validate_reviews(historical,previous,[builder.normalize(q,cfg,n+1) for n,q in enumerate(historical)],ROOT)
assert review['status']=='approved-after-independent-review' and len(revised_evidence)==len(revised)==60
assert review['officialSource']['pagesInspected']==list(range(1,35))
allowed={'version','enrichment','summary','explanation','takeaway','choiceReasons'}
explanation_reviewed=[{**d,'enrichment':'reviewed'} for d in revised]
for q,d,old in zip(explanation_reviewed,revised,historical):
 assert q=={**d,'enrichment':'reviewed'} and q['version']==old['version']+1
 assert {k:v for k,v in q.items() if k not in allowed}=={k:v for k,v in old.items() if k not in allowed}
 item=revised_evidence[q['id']]
 assert item['acceptedDraftSHA256']==builder.diagnostic_digest(d) and item['author']!=item['reviewer'] and item['status']=='approved'
 assert item['officialAnswerLabel']==next(c['label'] for c in q['choices'] if c['id']==q['correctChoiceId'])
# The hint revision is a separate independently sealed layer over the preserved
# explanation revision. Old reviews never certify the new hints by themselves.
hint_root=ROOT/'work/fp2/revisions/202605-objective-hints-v3'
read=lambda p:json.loads(p.read_text())
assert read(hint_root/'review/previous-publication-questions.json')==explanation_reviewed
old_hint_reviews=read(hint_root/'review/previous-publication-reviews.json')
builder.validate_reviews(explanation_reviewed,old_hint_reviews,[builder.normalize(q,cfg,n+1) for n,q in enumerate(explanation_reviewed)],ROOT)
hint_drafts=[q for p in sorted((hint_root/'drafts').glob('q*.json')) for q in read(p)]
assert len(hint_drafts)==len(raw)==60
hint_reviews=[read(p) for p in sorted((hint_root/'review').glob('independent-q*.json'))]
assert len(hint_reviews)==6 and all(r['status']=='approved' and r['author']!=r['reviewer'] for r in hint_reviews)
hint_evidence={r['questionId']:r for batch in hint_reviews for r in batch['questions']}
assert len(hint_evidence)==60
allowed_hint_keys={'version','enrichment','hintStatus','hints'}
for q,d,old in zip(raw,hint_drafts,explanation_reviewed):
 assert q=={**d,'enrichment':'reviewed'} and q['version']==old['version']+1
 assert {k:v for k,v in q.items() if k not in allowed_hint_keys}=={k:v for k,v in old.items() if k not in allowed_hint_keys}
 assert d['enrichment']=='draft' and q['hintStatus']=='individual' and len(q['hints'])==2
 assert all(h['title'].strip() and h['text'].strip() and type(h['revealsAnswer']) is bool for h in q['hints'])
 item=hint_evidence[q['id']]
 assert item['status']=='approved' and item['officialCorrectChoiceId']==q['correctChoiceId']
 assert item['acceptedSHA256']==builder.diagnostic_digest(q) and item['draftSHA256']==builder.diagnostic_digest(d)
 assert item['hintFlags']==[h['revealsAnswer'] for h in q['hints']]
ledger={r['questionId']:r for r in json.loads((ROOT/'content/fp2/question-reviews.json').read_text())}
assert len(ledger)==120
builder.validate_reviews(all_raw,list(ledger.values()),[builder.normalize(q,cfg,n+1) for n,q in enumerate(all_raw)],ROOT)

for q in all_raw:
 for asset,digest in ledger[q['id']]['assetHashes'].items():
  import hashlib
  assert hashlib.sha256((ROOT/asset).read_bytes()).hexdigest()==digest
manifest=json.loads((ROOT/'data/qualifications/fp2/manifest.json').read_text())
assert manifest['reviewed']==120 and sum(p['practiceAvailable'] for p in manifest['examParts'])==2
assert manifest['cases']['count']==80 and manifest['cases']['fields']==136
offline=json.loads((ROOT/'data/qualifications/fp2'/manifest['offline']['url']).read_text())
assert 'assets/fp2/202605/q55-family-chart.png' in offline['assets']
practical_groups=[g for g in offline['groups'] if g['examPartId']=='jafp-practical']
assert len(practical_groups)==2 and all(g['count']==40 and g['unit']=='cases' for g in practical_groups)
assert {f['image'] for c in all_registered for f in c['bodyFigures']}<=set().union(*(set(g['files']) for g in practical_groups))
assert not any(p.endswith('.pdf') for p in offline['assets'])
# January publication must exactly equal the independently approved projection.
jan=ROOT/'work/fp2/historical/202501'
jan_questions=json.loads((jan/'questions.json').read_text())
jan_cases=json.loads((jan/'practical-cases.json').read_text())
assert [q for q in all_raw if q['packId']=='202501']==[{**q,'enrichment':'reviewed'} for q in jan_questions]
assert [c for c in all_registered if c['id'].startswith('fp2-202501-')]==[{**c,'status':'reviewed'} for c in jan_cases]
jan_obj=json.loads((jan/'review/objective-final-review.json').read_text())
jan_pr=json.loads((jan/'review/practical-final-review.json').read_text())
assert builder.diagnostic_digest(jan_questions)==jan_obj['questionSetDraftSha256']
assert builder.diagnostic_digest(jan_cases)==jan_pr['draftSetCanonicalSha256']
assert len(jan_obj['questions'])==60 and len(jan_pr['questions'])==40
assert {r['questionId']:r for r in json.loads((jan/'review/objective-publication-reviews.json').read_text())}=={k:v for k,v in ledger.items() if k.startswith('fp2-202501-')}
case_ledger={r['caseId']:r for r in json.loads((ROOT/'content/fp2/practical-reviews.json').read_text())}
assert {r['caseId']:r for r in json.loads((jan/'review/practical-publication-reviews.json').read_text())}=={k:v for k,v in case_ledger.items() if k.startswith('fp2-202501-')}
jan_images={f['image'] for c in jan_cases for f in c['bodyFigures']}
assert len(jan_images)==8 and jan_images<=set(offline['assets'])
assert not ({p for c in jan_cases for p in c['sourceImages']} & set(offline['assets']))

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
print('PASS FP120+80 / 136 fields reviewed corpus / accepted draft contents preserved / figure hash and offline inventory / separated subject counts / isolated draft, legal, numeric and case-only contracts')
