"""Real AB-730 publication provenance; not a replacement for human/agent review."""
import json,hashlib,importlib.util,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
read=lambda p:json.loads((ROOT/p).read_text())
cfg=read('content/ab730/qualification.json');raw=read(cfg['questionSource']);reviews=read(cfg['questionReviewSource']);drafts=read('content/ab730/authoring/author-drafts.json');exclusions=read('content/ab730/authoring/publication-exclusions.json');progress=read('content/ab730/progress.json')
assert len(raw)==progress['published']==174
assert len(drafts)==progress['sourceCount']==187
assert len(reviews)==len(raw)
assert collections.Counter(q['type'] for q in raw)=={'singleChoice':157,'multipleChoice':17}
assert {q['id'] for q in raw}=={q['id'] for q in drafts}-{e['questionId'] for e in exclusions}
assert sum(e['status']=='held' for e in exclusions)==10
assert sum(bool(e.get('canonicalQuestionId')) for e in exclusions)==3
assert all(q==next(d for d in drafts if d['id']==q['id']) for q in raw)
normalized=[b.normalize(q,cfg,i+1) for i,q in enumerate(raw)];b.validate_reviews(raw,reviews,normalized);b.validate_questions(normalized,cfg,ROOT)
for q,r in zip(raw,reviews):
 assert r['questionId']==q['id'] and r['status']=='approved' and r['author']=='/root' and r['reviewer']=='/root/ab730_reviewer'
 assert q['sourceRefs']==list(dict.fromkeys(e['url'] for e in r['evidence']))
 assert len(q['choiceReasons'])==len(q['choices']) and all(reason.strip() for reason in q['choiceReasons'])
 assert q['hints']==[] and q['sourceKind']=='authored' and q['uses']==['practice','diagnostic']
 for e in r['evidence']:
  p=(ROOT/e['archivedPath']).resolve();assert p.is_relative_to(ROOT) and p.is_file()
  assert e['reviewedContent'] and hashlib.sha256(p.read_bytes()).hexdigest()==e['contentSha256']
  assert e['excerpt'] in p.read_text()
assert hashlib.sha256((ROOT/'content/ab730/intake/original.html.txt').read_bytes()).hexdigest()==progress['sourceSha256']
manifest=read('data/qualifications/ab730/manifest.json');actual=[]
for pack in manifest['packs']:
 p=ROOT/'data/qualifications/ab730'/pack['url'];assert hashlib.sha256(p.read_bytes()).hexdigest()==pack['sha256'];actual+=json.loads(p.read_text())
assert actual==normalized
index_path=ROOT/'data/qualifications/ab730'/manifest['index']['url'];assert hashlib.sha256(index_path.read_bytes()).hexdigest()==manifest['index']['sha256'];index=json.loads(index_path.read_text());assert [q['id'] for q in index]==[q['id'] for q in normalized]
for entry,q in zip(index,normalized):
 assert all(v==q[k] for k,v in entry.items() if k not in ['choices','hintCount'])
 assert entry['choices']==[{k:v for k,v in c.items() if k!='text'} for c in q['choices']]
 assert entry['hintCount']==0 and 'hints' not in entry and 'choiceReasons' not in entry

assert manifest['count']==manifest['reviewed']==174 and manifest['diagnosticBlueprint']['size']==30
assert not any(k in manifest for k in ['studyContext','flashcards','mockSets','assessment'])
assert {q['id'] for q in actual}.isdisjoint(q['id'] for q in read('data/questions.json'))
assert 'effectiveFrom' not in cfg['syllabuses'][0]
assert {q['id'] for q in read('data/qualifications/catalog.json')['qualifications']}==set(read('content/qualifications.json')['qualifications'])
print('PASS AB-730 actual187 source -> independent177 / held10 / duplicates3 / public174; exact raw+normalized review hashes; read official evidence+excerpt hashes; full choice reasons; stable IDs and original archive; generated174; optional features and AP separation')
