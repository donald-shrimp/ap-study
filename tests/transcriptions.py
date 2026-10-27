"""Reviewed source/hash coverage, generated text and immutable lesson data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import shutil

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('transcriptions',ROOT/'tools/apply-transcriptions.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
bank,records=module.checked_records()
retentions=module.checked_retentions(ROOT,bank,records)
by_id={q['id']:q for q in bank}
progress=json.loads((ROOT/'data/transcription-progress.json').read_text())
assert progress['reviewed']==len(records) and progress['imageRetained']==len(retentions)
assert progress['processed']==len(records)+len(retentions)
assert progress['remainingReview']==len(bank)-progress['processed']
assert set(progress['imageRetainedIds'])=={r['id'] for r in retentions}
assert {id for p in progress['packs'] for id in p['ids']}=={r['id'] for r in records}
assert progress['pendingDrafts']==len(module.draft_question_ids(ROOT)-{r['id'] for r in records}-{r['id'] for r in retentions})
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);folder=root/'data/transcription-drafts';folder.mkdir(parents=True)
    (folder/'chatgpt_external.json').write_text(json.dumps([{'id':'r05a-q61'},{'id':'r05a-q62'}]))
    (folder/'transcribe_local.json').write_text(json.dumps([{'id':'r05a-q62'},{'id':'r05a-q63'}]))
    (folder/'review_history.json').write_text(json.dumps([{'id':'r05a-q64'}]))
    assert module.draft_question_ids(root)=={'r05a-q61','r05a-q62','r05a-q63'}
journals=[json.loads(path.read_text()) for path in (ROOT/'data/transcription-context-revisions').glob('*.json')]
historical={module.digest(item['beforeQuestion']):item['beforeQuestion'] for journal in journals for item in journal['items']}
# Lesson-only revisions retain the real terminal transcription version in the
# immutable archive. The current bank must still match independent registrations.
quality_root=ROOT/'work/ap/objective-quality'
if (quality_root/'manifest.json').is_file():
 import sys
 sys.path.insert(0,str(ROOT/'tools'))
 from ap_lesson_quality import validate_workspace
 validate_workspace(ROOT)
 historical.update({module.digest(q):q for q in json.loads((quality_root/'baseline/questions.json').read_text())})

for journal in journals:
    assert journal['kind']=='reviewed-transcription-representation'
    for item in journal['items']:
        current=by_id[item['id']]
        q=current if module.digest(current)==item['afterQuestionSHA256'] else historical[item['afterQuestionSHA256']]
        before=item['beforeQuestion']
        assert {k for k in q if q[k]!=before.get(k)}<={'stem','choices','image','imageAlt','version','choicePresentation'}
        assert module.digest(q)==item['afterQuestionSHA256']
        assert {k:v for k,v in item['beforeContextItem'].items() if k!='sourceHash'}=={k:v for k,v in item['afterContextItem'].items() if k!='sourceHash'}
for record in records:
    q=by_id[record['id']]
    assert all(q[k]==record[k] for k in ['stem','choices','image','imageAlt']),q['id']
    assert q['sourceImages'] and q['enrichment']=='reviewed' and len(q['hints'])==3
    assert q['choices'][q['answer']]['label'] in ['ア','イ','ウ','エ']
    source=json.loads((ROOT/f'data/lessons/{q["id"].split("-q")[0]}.json').read_text())
    lesson=next(l for l in source if l['id']==q['id'])
    assert all(q[k]==lesson[k] for k in ['summary','explanation','takeaway','choiceReasons','hints'])

# Reviewed source edits, author self-review and figure edits are rejected before
# rewriting the bank. Test in an isolated tree, never mutate public material.
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    for folder in ['data/transcriptions','data/transcription-reviews']:
        shutil.copytree(ROOT/folder,root/folder)
    (root/'data/questions.json').write_text(json.dumps(bank,ensure_ascii=False))
    for q in bank:
        for path in q['sourceImages']+[q.get('image')]+[c.get('image') for c in q['choices']]:
            if path:
                destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,destination)
    for record in records:
        for proof in record.get('sourceEvidence',[]):
            destination=root/proof['path'];destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/proof['path'],destination)
    first=records[0];source=root/'data/transcriptions'/f'{first["id"].split("-q")[0]}.json'
    content=json.loads(source.read_text());content[0]['stem']+='改ざん';source.write_text(json.dumps(content))
    try:module.checked_records(root);raise AssertionError('edited transcription accepted')
    except ValueError as error:assert 'hash' in str(error)
    shutil.copyfile(ROOT/source.relative_to(root),source)
    review_file=root/'data/transcription-reviews'/source.name;reviews=json.loads(review_file.read_text());reviews[0]['reviewer']=first['author'];review_file.write_text(json.dumps(reviews))
    try:module.checked_records(root);raise AssertionError('self-review accepted')
    except ValueError as error:assert 'Independent review' in str(error)
    shutil.copyfile(ROOT/review_file.relative_to(root),review_file)
    # Retention decisions also require independent exact-hash source review;
    # they must never be used to inflate the text transcription count.
    retention_file=ROOT/'data/transcription-image-retentions.json'
    if retentions:
        shutil.copyfile(retention_file,root/'data/transcription-image-retentions.json')
        for entry in retentions:
            if entry.get('priorReview'):
                destination=root/entry['priorReview'];destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/entry['priorReview'],destination)
        module.checked_retentions(root,bank,records)
        edited=json.loads(retention_file.read_text());edited[0]['reason']+='改ざん'
        (root/'data/transcription-image-retentions.json').write_text(json.dumps(edited))
        try:module.checked_retentions(root,bank,records);raise AssertionError('edited retention accepted')
        except ValueError as error:assert 'hash' in str(error)
        edited=json.loads(retention_file.read_text());edited[0]['reviewer']=edited[0]['assessor']
        edited[0]['reviewedDecisionSHA256']=module.digest({k:v for k,v in edited[0].items() if k!='reviewedDecisionSHA256'})
        (root/'data/transcription-image-retentions.json').write_text(json.dumps(edited))
        try:module.checked_retentions(root,bank,records);raise AssertionError('retention self-review accepted')
        except ValueError as error:assert 'Independent' in str(error)
    figure=next(r['image'] for r in records if r['image']);(root/figure).write_bytes(b'changed')
    try:module.checked_records(root);raise AssertionError('edited figure accepted')
    except ValueError as error:assert 'figure changed' in str(error)
    shutil.copyfile(ROOT/figure,root/figure)
    supplemental=next((proof['path'] for r in records for proof in r.get('sourceEvidence',[])),None)
    if supplemental:
        (root/supplemental).write_bytes(b'changed')
        try:module.checked_records(root);raise AssertionError('edited source supplement accepted')
        except ValueError as error:assert 'Supplemental source changed' in str(error)

subprocess.run(['node','tools/check-question-text.mjs'],cwd=ROOT,check=True)
print(f'PASS {len(records)} independently reviewed transcriptions / source and figure hashes / immutable lessons / tamper rejection')
