"""Draft structural and numerical self-checks. This does NOT approve publication."""
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda path:json.loads((ROOT/path).read_text())
digest=lambda q:hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
batch=read('content/ap/diagnostic-drafts/20261008-second-round.json')
checks=read('content/ap/diagnostic-drafts/20261008-second-round-author-checks.json')
progress=read('content/ap/diagnostic-progress.json')
published=read('content/ap/diagnostic-questions.json')
manifest=read('data/qualifications/ap/manifest.json')
parents={q['id']:q for q in read('data/qualifications/ap/'+manifest['index']['url'])}
assert not checks['independentReview'] and checks['author']==batch['author']
assert len(batch['questions'])==8 and len({q['topicId'] for q in batch['questions']})==8
assert len({q['parentQuestionId'] for q in batch['questions']})==8
assert not {q['parentQuestionId'] for q in batch['questions']} & {q['parentQuestionId'] for q in published}
records={item['questionId']:item for item in progress['items']}
evidence={e['questionId']:e for e in batch['sourceChecks']}
authorchecks={c['questionId']:c for c in checks['checks']}
bytopic={q['topicId']:q for q in batch['questions']}
for q in batch['questions']:
    r=records[q['id']]; pending=r['status']=='awaiting-independent-review'
    assert q['diagnosticOnly'] and q['enrichment']=='draft' and q['hints']==[]
    assert len(q['choices'])==len(q['choiceReasons'])==4
    assert len({c['text'] for c in q['choices']})==4
    assert q['correctChoiceId'] in {c['id'] for c in q['choices']}
    assert r['draftSha256']==authorchecks[q['id']]['draftSha256']==digest(q)
    assert authorchecks[q['id']]['status']=='author-self-check-only'
    assert q['topicId']==parents[q['parentQuestionId']]['topicId']
    assert evidence[q['id']]['originalAnswerLabel']==parents[q['parentQuestionId']]['choices'][parents[q['parentQuestionId']]['answer']]['label']
    for image in evidence[q['id']]['sourceImages']:
        assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest()==image['sha256']
    if pending: assert q['id'] not in {p['id'] for p in published}

def choice(q): return next(c['text'] for c in q['choices'] if c['id']==q['correctChoiceId'])
theory=bytopic['theory']
assert '20%' in theory['stem'] and '50%' in theory['stem']
waiting=lambda utilization:utilization/(1-utilization)
assert F(choice(theory))==waiting(F(50,100))/waiting(F(20,100))==4
architecture=bytopic['architecture']
assert all(str(t)+'ナノ秒' in architecture['stem'] for t in [80,20,32])
assert [c['id'] for c in architecture['choices'] if 20*F(c['text'])+80*(1-F(c['text']))==32]==[architecture['correctChoiceId']]
system=bytopic['system']
assert all(str(t)+'時間' in system['stem'] for t in [95,12,5])
assert F(choice(system))==F(95,100)
assert [round(float(F(95,112)),2),round(float(F(95,107)),2),round(float(F(95,100)),2),round(float(F(99,101)),2)]==[float(c['text']) for c in system['choices']]
interface=bytopic['interface']
assert '320×240' in interface['stem'] and '24ビット' in interface['stem'] and '30フレーム' in interface['stem']
bits=320*240*24*30
assert bits==55296000 and abs(bits-55*10**6)<10**6
assert choice(interface)=='55Mビット／秒'
print('8 drafts: source/hash/structure and numeric self-checks passed. Separate content review remains required.')
