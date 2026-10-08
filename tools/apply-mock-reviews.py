"""Promote explicitly approved mock materials and their actual review evidence.

This does not generate approvals or review check flags. A different reviewer must
provide completed questions, decisions, solutions and source evidence first.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: json.loads(path.read_text())
write = lambda path, value: path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
digest = lambda q: hashlib.sha256(json.dumps(q, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('review_directory', type=Path)
parser.add_argument('--set', required=True, choices=['a', 'b'])
args = parser.parse_args()
directory = args.review_directory.resolve()
questions = read(directory/'corrected-questions.json')
reviews = read(directory/'reviews.json')
solutions = read(directory/'solutions.json')
findings = read(directory/'findings.json')
assert isinstance(questions, list) and isinstance(reviews, list) and questions
review_by_id = {r['questionId']: r for r in reviews}
assert len(review_by_id) == len(reviews) == len(questions)
assert set(review_by_id) == {q['id'] for q in questions}
first_pass={s['questionId']:s for s in solutions['solutions']}
decisions={f['questionId']:f for f in findings}
assert set(review_by_id)==set(first_pass)==set(decisions)
assert all(f['status']=='approved' and f['rationale'].strip() for f in findings)
assert all(s['reason'].strip() for s in first_pass.values())
sets = read(ROOT/'content/ap/mock-sets.json')
slots = {s['questionId']: s for pack in sets['sets'] if pack['id']==f'ap-mock-{args.set}' for s in pack['slots']}
progress_path = ROOT/'content/ap/diagnostic-progress.json'
progress = read(progress_path)
items = {i['questionId']: i for i in progress['items']}
published_path = ROOT/'content/ap/diagnostic-questions.json'
reviews_path = ROOT/'content/ap/diagnostic-reviews.json'
published = read(published_path)
old_reviews = read(reviews_path)
published_by_id = {q['id']: q for q in published}
evidence = ROOT/f'content/ap/diagnostic-evidence/mock-{args.set}'

# Validate all supplied completed objects before modifying the shared corpus.
for q in questions:
    assert q['id'] in slots and q['id'].startswith(f'ap-mock-{args.set}-q')
    slot, item, review = slots[q['id']], items[q['id']], review_by_id[q['id']]
    assert q['parentQuestionId']==slot['parentQuestionId'] and q['topicId']==slot['topicId']
    assert q['diagnosticOnly'] is True and q['enrichment']=='reviewed' and q['hints']==[]
    assert len(q['choices'])==len(q['choiceReasons'])==4 and all(q['choiceReasons'])
    assert q['correctChoiceId'] in {c['id'] for c in q['choices']}
    assert review['sha256']==digest(q) and review['version']==q['version']
    assert review['author']==item['authorRun'] and review['reviewer']!=review['author']
    assert all(review['checks'].get(k) is True for k in ['source','answer','calculation','choices','wording'])
    assert review['notes'].strip() and review['method']['separateAgent'] is True
    assert review['method']['separateExecution'] is True and review['method']['answerBlindFirstPass'] is True
    assert review['sourceEvidence']['parentQuestionId']==q['parentQuestionId']
    assert review['sourceEvidence']['originalViewedInReviewRun'] is True
    assert review['sourceEvidence']['officialAnswer']==review['sourceEvidence']['independentOriginalAnswer']
    for image in review['sourceEvidence']['sourceImages']:
        original=ROOT/image['path']
        assert original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()==image['sha256']
    if q['id'] in published_by_id:
        assert published_by_id[q['id']]==q, 'Already-published object differs; use the revision workflow.'
    else:
        assert item['status']=='awaiting-independent-review'
    assets=list(filter(None,[q.get('image'),*q.get('sourceImages',[]),*(c.get('image') for c in q['choices'])]))
    image_hashes={image['path']:image['sha256'] for image in review.get('derivedImages',[])}
    assert set(assets)==set(image_hashes), 'Missing completed diagram hash evidence.'
    for asset in assets:
        target=ROOT/asset
        assert target.resolve().is_relative_to((ROOT/'assets/questions/diagnostic').resolve())
        local=directory/'assets'/Path(asset).name
        assert local.is_file() or target.is_file(), 'Missing reviewed figure: '+asset
        assert hashlib.sha256((local if local.is_file() else target).read_bytes()).hexdigest()==image_hashes[asset]
        if local.is_file() and target.is_file():
            assert local.read_bytes()==target.read_bytes(), 'Use a new filename for a revised figure.'

evidence.mkdir(parents=True, exist_ok=True)
for filename in ['solutions.json','findings.json','independent-checks.py','independent-checks.json','calculation-inputs.json','calculation-image-hashes.json','asset-hashes.json','official-answer-extracted.txt','browser-render-records.json','ui-display-checks.json']:
    source=directory/filename
    if source.is_file(): shutil.copy(source,evidence/filename)
for source in directory.glob('solutions-*.json'):
    shutil.copy(source,evidence/source.name)
for q in questions:
    for asset in filter(None,[q.get('image'),*q.get('sourceImages',[]),*(c.get('image') for c in q['choices'])]):
        target=ROOT/asset;local=directory/'assets'/Path(asset).name
        if local.is_file() and not target.exists(): shutil.copy(local,target)
    review=review_by_id[q['id']]
    review['method']['firstPassSolutions']=str((evidence/'solutions.json').relative_to(ROOT))
    review['method']['findings']=str((evidence/'findings.json').relative_to(ROOT))
    if (evidence/'independent-checks.py').exists():
        review['method']['independentChecks']=str((evidence/'independent-checks.py').relative_to(ROOT))
    for field in ['batchFirstPassSolutions','browserRenderRecords']:
        if review['method'].get(field):
            name=Path(review['method'][field]).name
            assert (evidence/name).is_file()
            review['method'][field]=str((evidence/name).relative_to(ROOT))
    if (evidence/'ui-display-checks.json').exists():
        review['method']['actualUiDisplayEvidence']=str((evidence/'ui-display-checks.json').relative_to(ROOT))
    if q['id'] not in published_by_id:
        published.append(q);old_reviews.append(review)
    else:
        original=next(r for r in old_reviews if r['questionId']==q['id'])
        assert original['reviewer']==review['reviewer'] and original['sha256']==review['sha256']
        old_reviews[old_reviews.index(original)]=review
    items[q['id']].update(status='reviewed',publishedVersion=q['version'],publishedSha256=digest(q),reviewRun=review['reviewer'])
progress['latestReviewRun']=reviews[-1]['reviewer']
progress['editorialPolicy'].update(updatedAt=datetime.now(timezone.utc).isoformat(),alignedQuestionIds=[q['id'] for q in published])
write(published_path,published);write(reviews_path,old_reviews);write(progress_path,progress)
print(json.dumps({'approved':len(questions),'published':len(published),'reviewer':reviews[-1]['reviewer']},ensure_ascii=False))
