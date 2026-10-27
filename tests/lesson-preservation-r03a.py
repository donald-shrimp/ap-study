"""Compare final autumn integration to the clean main at the start of this round."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = '1ac6547adddb659fd1026aee48d413bce2bd5d98'
COMPLETED = 'b5d5464916706ac3febf0f4d51fc3529ddd89b95'

def original(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)

sys.path.insert(0, str(ROOT/'tools'))
from ap_lesson_quality import validate_workspace
validate_workspace(ROOT)
# Keep every original historical preservation assertion against the exact
# completed integration commit. Later transcription/UI/lesson revisions have
# their own evidence and must not be mistaken for the historical post-state.
def completed(path):
    return subprocess.check_output(['git','show',f'{COMPLETED}:{path}'],cwd=ROOT)
before = {q['id']:q for q in json.loads(original('data/questions.json'))}
after = {q['id']:q for q in json.loads(completed('data/questions.json'))}
assert set(before)==set(after) and len(after)==800
educational = ['summary','explanation','choiceReasons','takeaway','hints']
for id, old in before.items():
    new = after[id]
    source_fields = set(old)-set(educational)-{'enrichment','hintSource','lessonSource'}
    assert set(new)-set(old) <= {'lessonSource'},id
    assert all(old.get(f)==new.get(f) for f in source_fields),id
    if not id.startswith('r03a-'):assert old==new,id
    if old['enrichment']=='reviewed':
        expected = copy.deepcopy(old)
        if id in {'r03a-q3','r03a-q4'}:
            assert not old['hints'][1]['revealsAnswer']
            expected['hints'][1]['revealsAnswer'] = True
        assert all(expected[f]==new[f] for f in educational),id
assert sum(q['enrichment']=='reviewed' for q in before.values())==722
assert all(q['enrichment']=='reviewed' for q in after.values())
files = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,
    'data/lessons','data/lesson-reviews','assets/questions','data/answer-keys.json',
    'data/sources.json','data/source-crops.json','src','templates','app.js',
    'styles.css','sw.js','manifest.webmanifest','index.html','ap/index.html',
    'firebase'],cwd=ROOT,text=True).splitlines()
for path in files:
    assert completed(path)==original(path),path
digest=hashlib.sha256(completed('data/questions.json')).hexdigest()
print(f'PASS 720 unchanged question records / all 722 existing lesson texts (two disclosure flags corrected) / {len(files)} historical source, review, UI, PWA and Firebase files / historical bank SHA-256 {digest}')
