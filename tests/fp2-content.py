"""Published FP240/160 corpus plus isolated draft/evidence/case-only contracts."""
import copy,hashlib,importlib.util,json,subprocess,tempfile,jsonschema
from referencing import Registry,Resource
from pathlib import Path
from fp2_fixtures import prepare,builder,write,ROOT
from material_contracts import decimal_value,validate_numeric,validate_legal
spec=importlib.util.spec_from_file_location('delivery_check',ROOT/'tools/check-fp2-delivery.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
assert 'fp2' in json.loads((ROOT/'content/qualifications.json').read_text())['qualifications']
catalog=json.loads((ROOT/'data/qualifications/catalog.json').read_text())['qualifications']
published=next(q for q in catalog if q['id']=='fp2');assert published['count']==240
assert published['studyTargets']==[{'examPartId':'objective','label':'学科','unit':'questionAttempts','count':240},{'examPartId':'jafp-practical','label':'実技（日本FP協会）','unit':'cases','count':160,'caseLabel':'問題','countLabel':'問'}]
assert delivery.check(ROOT,True)=={'questions':240,'cases':160,'fields':274,'mode':'reviewed evidence'}
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
assert len(ledger)==240
builder.validate_reviews(all_raw,list(ledger.values()),[builder.normalize(q,cfg,n+1) for n,q in enumerate(all_raw)],ROOT)

for q in all_raw:
 for asset,digest in ledger[q['id']]['assetHashes'].items():
  import hashlib
  assert hashlib.sha256((ROOT/asset).read_bytes()).hexdigest()==digest
manifest=json.loads((ROOT/'data/qualifications/fp2/manifest.json').read_text())
assert manifest['reviewed']==240 and sum(p['practiceAvailable'] for p in manifest['examParts'])==2
assert manifest['cases']['count']==160 and manifest['cases']['fields']==274
offline=json.loads((ROOT/'data/qualifications/fp2'/manifest['offline']['url']).read_text())
assert 'assets/fp2/202605/q55-family-chart.png' in offline['assets']
practical_groups=[g for g in offline['groups'] if g['examPartId']=='jafp-practical']
assert len(practical_groups)==4 and all(g['count']==40 and g['unit']=='cases' for g in practical_groups)
assert {f['image'] for c in all_registered for f in c['bodyFigures']}<=set().union(*(set(g['files']) for g in practical_groups))
assert not any(p.endswith('.pdf') for p in offline['assets'])
# January publication must exactly equal the independently approved projection.
jan=ROOT/'work/fp2/historical/202501'
jan_questions=json.loads((jan/'questions.json').read_text())
jan_cases=json.loads((jan/'practical-cases.json').read_text())
assert [q for q in all_raw if q['packId']=='202501']==[{**q,'enrichment':'reviewed'} for q in jan_questions]
jan_law=ROOT/'work/fp2/revisions/202501-practical-q17-law'
old_q17=read(jan_law/'previous-publication-case.json');new_q17=read(jan_law/'case.json')
assert old_q17==next({**c,'status':'reviewed'} for c in jan_cases if c['id']==old_q17['id'])
assert new_q17['version']==old_q17['version']+1 and new_q17['status']=='draft'
assert {k:v for k,v in new_q17.items() if k not in {'version','status','legalReview'}}=={k:v for k,v in old_q17.items() if k not in {'version','status','legalReview'}}
assert new_q17['legalReview']['status']=='outdated' and new_q17['legalReview']['checkedAt']=='2026-10-26'
expected_jan=[{**(new_q17 if c['id']==old_q17['id'] else c),'status':'reviewed'} for c in jan_cases]
assert [c for c in all_registered if c['id'].startswith('fp2-202501-')]==expected_jan
assert read(jan_law/'review/independent-review.json')['status']=='approved'
jan_obj=json.loads((jan/'review/objective-final-review.json').read_text())
jan_pr=json.loads((jan/'review/practical-final-review.json').read_text())
assert builder.diagnostic_digest(jan_questions)==jan_obj['questionSetDraftSha256']
assert builder.diagnostic_digest(jan_cases)==jan_pr['draftSetCanonicalSha256']
assert len(jan_obj['questions'])==60 and len(jan_pr['questions'])==40
assert {r['questionId']:r for r in json.loads((jan/'review/objective-publication-reviews.json').read_text())}=={k:v for k,v in ledger.items() if k.startswith('fp2-202501-')}
case_ledger={r['caseId']:r for r in json.loads((ROOT/'content/fp2/practical-reviews.json').read_text())}
old_jan_reviews={r['caseId']:r for r in read(jan/'review/practical-publication-reviews.json')}
assert old_jan_reviews[old_q17['id']]==read(jan_law/'review/previous-publication-review.json')
new_q17_review=read(jan_law/'review/publication-review.json')
assert new_q17_review['canonicalCaseSHA256']==builder.diagnostic_digest({**new_q17,'status':'reviewed'})
expected_jan_reviews={**old_jan_reviews,old_q17['id']:new_q17_review}
assert expected_jan_reviews=={k:v for k,v in case_ledger.items() if k.startswith('fp2-202501-')}
jan_images={f['image'] for c in jan_cases for f in c['bodyFigures']}
assert len(jan_images)==8 and jan_images<=set(offline['assets'])
assert not ({p for c in jan_cases for p in c['sourceImages']} & set(offline['assets']))

# May 2025 publication is the exact independently reviewed delivery projection.
may=ROOT/'deliveries/fp2-jafp-202505'
may_questions=read(may/'content/fp2/questions.json');may_cases=read(may/'content/fp2/practical-cases.json')
assert [q for q in all_raw if q['packId']=='202505']==[{**q,'enrichment':'reviewed'} for q in may_questions]
assert [c for c in all_registered if c['id'].startswith('fp2-202505-')]==[{**c,'status':'reviewed'} for c in may_cases]
assert {r['questionId']:r for r in read(may/'review/objective-publication-reviews.json')}=={k:v for k,v in ledger.items() if k.startswith('fp2-202505-')}
assert {r['caseId']:r for r in read(may/'review/practical-publication-reviews.json')}=={k:v for k,v in case_ledger.items() if k.startswith('fp2-202505-')}
may_images={f['image'] for c in may_cases for f in c['bodyFigures']}
assert len(may_images)==5 and may_images<=set(offline['assets'])
assert not ({p for c in may_cases for p in c['sourceImages']} & set(offline['assets']))
obj_first=read(may/'review/objective-final-01-30.json')
assert obj_first['allInitialFindingsResolved'] and not obj_first['remainingFindings'] and len(obj_first['records'])==30
assert all(r['verdict']=='accepted_content_final' and r['draftCanonicalSHA256']==builder.diagnostic_digest(may_questions[n]) for n,r in enumerate(obj_first['records']))
obj_second=read(may/'review/objective-final-31-60.json')
assert not obj_second['remainingFindings'] and len(obj_second['checks'])==30
assert all(r['status']=='accepted' and r['draftCanonicalSHA256']==builder.diagnostic_digest(may_questions[n+30]) for n,r in enumerate(obj_second['checks']))
for suffix in ['01-20','21-40']:
 final=read(may/f'review/practical-final-{suffix}.json')
 assert final['status']=='approved' and len(final['questions'])==20
for q in may_questions:assert '別担当' not in q['explanation'] and 'レビューで必要' not in q['explanation']
assert '800百万円' in may_questions[9]['stem'] and '| 科目 | 金額 |' in may_questions[9]['stem']
assert all('/review-v3/' in f['image'] for c in may_cases for f in c['bodyFigures'])

# September projection, law flags, all review seals and immutable earlier corpus.
sep=ROOT/'work/fp2/historical/202409'
sep_questions=read(sep/'questions.json');sep_cases=read(sep/'practical-cases.json')
assert len(sep_questions)==60 and len(sep_cases)==40
assert [q for q in all_raw if q['packId']=='202409']==[{**q,'enrichment':'reviewed'} for q in sep_questions]
assert [c for c in all_registered if c['id'].startswith('fp2-202409-')]==[{**c,'status':'reviewed'} for c in sep_cases]
for name,key,published_ledger in [('objective-publication-reviews.json','questionId',ledger),('practical-publication-reviews.json','caseId',case_ledger)]:
 reviews=read(sep/'review'/name)
 assert {r[key]:r for r in reviews}=={k:v for k,v in published_ledger.items() if k.startswith('fp2-202409-')}
 for item in reviews:assert item['author']!=item['reviewer'] and (ROOT/item['reviewEvidence']['record']).is_file()
for name,count in [('objective-final-01-30.json',30),('objective-final-31-60.json',30),('practical-final-01-20.json',20),('practical-final-21-40.json',20)]:
 final=read(sep/'review'/name);assert final['status']=='approved'
 records=final.get('questions',final.get('records',final.get('checks',[])));assert len(records)==count
assert sum(len(q['hints']) for q in sep_questions)==120
for n in [25,27,33]:assert '| --- |' in sep_questions[n-1]['stem']
for n in [46,48,50]:assert sep_questions[n-1]['hints'][0]['revealsAnswer'] is True
assert sep_cases[4]['items'][0]['fields'][0]['numeric']['rounding']=='floor'
for n in [24,25]:assert '| ライフイベント |  | 綾乃中学校入学 | 自動車購入 | 英夫中学校入学 | 綾乃高校入学 |  |' in sep_cases[n-1]['body']
flags={'fp2-202409-objective-q07','fp2-202409-objective-q35','fp2-202409-jafp-q31','fp2-202409-jafp-q35','fp2-202409-jafp-q40'}
assert {c['id'] for c in sep_questions+sep_cases if c['legalReview']['status']=='outdated'}==flags
for c in sep_questions+sep_cases:
 validate_legal(c)
 if c['id'] in flags:assert c['legalReview']['checkedAt']=='2026-10-26' and c['legalReview']['sourceRefs'] and c['sourceRecord']['legalAsOf']=='2024-04-01'
 else:assert c['legalReview']['status']=='unverified'
sep_images={f['image'] for c in sep_cases for f in c['bodyFigures']}
assert len(sep_images)==6 and sep_images<=set(offline['assets'])
assert not ({p for c in sep_cases for p in c['sourceImages']} & set(offline['assets']))
preserved=read(sep/'review/preservation.json')
for path in ['content/fp2/questions.json','content/fp2/question-reviews.json','content/fp2/practical-cases.json','content/fp2/practical-reviews.json']:
 proof=preserved[path];previous=copy.deepcopy(read(ROOT/path)[:proof['count']])
 if path.endswith('practical-cases.json'):previous=[old_q17 if c['id']==old_q17['id'] else c for c in previous]
 if path.endswith('practical-reviews.json'):previous=[read(jan_law/'review/previous-publication-review.json') if c['caseId']==old_q17['id'] else c for c in previous]
 assert builder.diagnostic_digest(previous)==proof['canonicalSHA256'],path
catalog_before=read(ROOT/'content/fp2/case-catalog.json');catalog_before['entries']=catalog_before['entries'][:120]
assert builder.diagnostic_digest(catalog_before)==preserved['content/fp2/case-catalog.json']['canonicalSHA256']
for path in ['data/qualifications/ap/manifest.json','data/qualifications/ab730/manifest.json']:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==preserved[path]['fileSHA256']

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
print('PASS FP240+160 / 274 fields reviewed corpus / accepted draft contents preserved / figure hash and offline inventory / separated subject counts / isolated draft, legal, numeric and case-only contracts')
