"""Verify actual mock families, subject balance, review evidence and draft isolation."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--complete',action='store_true',help='Require all 160 materials to be reviewed and published, not just a valid plan.')
args=parser.parse_args()
read=lambda path:json.loads((ROOT/path).read_text())
digest=lambda q:hashlib.sha256(json.dumps(q,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
sets=read('content/ap/mock-sets.json')
qualification=read('content/ap/qualification.json')
manifest=read('data/qualifications/ap/manifest.json')
originals={q['id']:q for q in read('data/qualifications/ap/'+manifest['index']['url'])}
published={q['id']:q for q in read('content/ap/diagnostic-questions.json')}
reviews={r['questionId']:r for r in read('content/ap/diagnostic-reviews.json')}
progress=read('content/ap/diagnostic-progress.json')
assert sets['format']=='hitomon-mock-sets' and sets['version']==1 and sets['qualificationId']=='ap' and sets['materialOnly']
assert len(sets['sets'])==2 and len({s['id'] for s in sets['sets']})==2
all_ids=set();all_parents=set()
for s in sets['sets']:
    assert s['size']==len(s['slots'])==80
    assert [slot['number'] for slot in s['slots']]==list(range(1,81))
    assert s['status'] in ['in_progress','ready']
    subjects=Counter();topics=Counter();set_ids=set()
    for slot in s['slots']:
        parent=originals[slot['parentQuestionId']]
        assert slot['topicId']==parent['topicId']
        assert slot['questionId'] not in all_ids and slot['parentQuestionId'] not in all_parents
        all_ids.add(slot['questionId']);all_parents.add(slot['parentQuestionId']);set_ids.add(slot['questionId'])
        topics[parent['topicId']]+=1
        subjects['technology' if parent['number']<=50 else 'management' if parent['number']<=60 else 'strategy']+=1
        if slot['questionId'] in published:
            q=published[slot['questionId']];review=reviews[q['id']]
            assert q['diagnosticOnly'] and q['enrichment']=='reviewed' and q['hints']==[]
            assert q['parentQuestionId']==parent['id'] and q['topicId']==parent['topicId']
            assert len(q['choices'])==len(q['choiceReasons'])==4
            assert review['sha256']==digest(q) and review['author']!=review['reviewer']
            assert review['method']['separateAgent'] is True and all(review['checks'][key] for key in ['source','answer','calculation','choices','wording'])
            if q['id'].startswith('ap-mock-'):
                assert not (q.get('stem') and q.get('sourceImages')), 'Text stems use image/imageAlt for figures in the diagnostic renderer.'
                assets=set(filter(None,[q.get('image'),*q.get('sourceImages',[]),*(c.get('image') for c in q['choices'])]))
                hashes={image['path']:image['sha256'] for image in review.get('derivedImages',[])}
                assert assets==set(hashes)
                assert all(hashlib.sha256((ROOT/asset).read_bytes()).hexdigest()==hashes[asset] for asset in assets)
    assert subjects==s['distribution']=={'technology':50,'management':10,'strategy':20}
    assert set(topics)=={topic['id'] for topic in qualification['topics']}
    complete=len(set_ids & published.keys())
    assert (s['status']=='ready')==(complete==80)
    if s['status']=='ready':assert all(id in published for id in set_ids)
assert len(all_ids)==len(all_parents)==160
if args.complete:
    assert all(s['status']=='ready' for s in sets['sets']) and all(id in published for id in all_ids)
    assert progress['pendingReviewCount']==0
assert not qualification['diagnosticBlueprint']['variantLimits'], 'Do not silently change the 30-question allocation.'
assert len(originals)==800 and not any(q.get('diagnosticOnly') for q in originals.values())
for item in progress['items']:
    if item['status']=='awaiting-independent-review':assert item['questionId'] not in published
print('PASS '+('160 reviewed materials / ' if args.complete else 'planned materials / ')+'two 80-slot sets / 160 distinct source families / all17 fields / 50+10+20 per set / actual review hashes / unaided and ordinary-corpus isolation')
