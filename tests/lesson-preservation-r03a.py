"""Compare final autumn integration to the clean main at the start of this round."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '1ac6547adddb659fd1026aee48d413bce2bd5d98'

def original(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)

before = {q['id']:q for q in json.loads(original('data/questions.json'))}
after = {q['id']:q for q in json.loads((ROOT/'data/questions.json').read_bytes())}
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
    assert (ROOT/path).read_bytes()==original(path),path
digest=hashlib.sha256((ROOT/'data/questions.json').read_bytes()).hexdigest()
print(f'PASS 720 unchanged question records / all 722 existing lesson texts (two disclosure flags corrected) / {len(files)} existing source, review, UI, PWA and Firebase files / bank SHA-256 {digest}')
