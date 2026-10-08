"""Save completed author batches as pending drafts; never approve publication.

This staging helper is independent from the review/promotion step. It only
copies already-authored JSON/assets and recomputes the factual progress ledger.
"""
import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda path:json.loads(path.read_text())
write=lambda path,value:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
digest=lambda q:hashlib.sha256(json.dumps(q,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('workspace',type=Path)
parser.add_argument('--refresh-pending',action='store_true',help='Archive and replace pending drafts only; never replace a published question.')
args=parser.parse_args()
progress_path=ROOT/'content/ap/diagnostic-progress.json'
progress=read(progress_path)
sets=read(ROOT/'content/ap/mock-sets.json')
slots={slot['questionId']:slot for s in sets['sets'] for slot in s['slots']}
records={item['questionId']:item for item in progress['items']}
added=0
for side in ['a','b']:
    directory=args.workspace/f'author-{side}'
    for source in sorted(directory.glob('batch-*.json')):
        batch=read(source)
        assert batch['format']=='hitomon-diagnostic-drafts' and batch['status']=='awaiting-independent-review'
        target=ROOT/f'content/ap/diagnostic-drafts/{batch["batchId"]}.json'
        if target.exists() and read(target)!=batch:
            assert args.refresh_pending, 'An imported batch was changed; explicit pending refresh required.'
            assert all(records[q['id']]['status']=='awaiting-independent-review' for q in batch['questions'])
            archive=target.parent/'archive';archive.mkdir(exist_ok=True)
            old_hash=hashlib.sha256(target.read_bytes()).hexdigest()[:16]
            shutil.copy(target,archive/(target.stem+'-'+old_hash+'.json'))
        for q in batch['questions']:
            assert q['id'] in slots and q['parentQuestionId']==slots[q['id']]['parentQuestionId']
            assert q['topicId']==slots[q['id']]['topicId'] and q['enrichment']=='draft' and q['diagnosticOnly']
            if q['id'] in records:
                item=records[q['id']]
                if item['draftSha256']!=digest(q):
                    assert args.refresh_pending and item['status']=='awaiting-independent-review', 'An imported draft was changed: '+q['id']
                    item.update(draftSha256=digest(q),draftVersion=q['version'])
                if args.refresh_pending and item['status']=='awaiting-independent-review':
                    item['authorRun']=batch['author']
            else:
                item={'questionId':q['id'],'topicId':q['topicId'],'parentQuestionId':q['parentQuestionId'],'status':'awaiting-independent-review','draftVersion':q['version'],'draftSha256':digest(q),'authorRun':batch['author'],'draftBatchPath':str(target.relative_to(ROOT))}
                progress['items'].append(item);records[q['id']]=item;added+=1
            assets=[q.get('image'),*q.get('sourceImages',[]),*(choice.get('image') for choice in q['choices'])]
            for asset in filter(None,assets):
                public=ROOT/asset
                assert public.resolve().is_relative_to((ROOT/'assets/questions/diagnostic').resolve())
                local=directory/'assets'/Path(asset).name
                assert local.is_file(), 'Missing draft figure: '+asset
                if public.exists():assert public.read_bytes()==local.read_bytes(), 'Figure name collision: '+asset
                else:public.parent.mkdir(parents=True,exist_ok=True);shutil.copy(local,public)
        write(target,batch)
        relative=str(target.relative_to(ROOT))
        if relative not in progress['batchPaths']:progress['batchPaths'].append(relative)
        checks=directory/source.name.replace('batch-','author-checks-')
        assert checks.is_file()
        check_target=target.with_name(target.stem+'-author-checks.json')
        if check_target.exists() and read(check_target)!=read(checks):
            assert args.refresh_pending
            archive=target.parent/'archive';archive.mkdir(exist_ok=True)
            old_hash=hashlib.sha256(check_target.read_bytes()).hexdigest()[:16]
            shutil.copy(check_target,archive/(check_target.stem+'-'+old_hash+'.json'))
        shutil.copy(checks,check_target)
published=read(ROOT/'content/ap/diagnostic-questions.json')
pending=[item for item in progress['items'] if item['status']=='awaiting-independent-review']
progress.update(updatedAt=datetime.now(timezone.utc).isoformat(),publishedCount=len(published),pendingReviewCount=len(pending),draftCount=len(pending),archivedDraftCount=sum('draftSha256' in i and i['status']=='reviewed' for i in progress['items']))
progress['parentExamCounts']=dict(sorted(Counter(q['parentQuestionId'].split('-')[0] for q in published).items()))
progress['draftParentExamCounts']=dict(sorted(Counter(q['parentQuestionId'].split('-')[0] for q in pending).items()))
for topic,counts in progress['topicCounts'].items():
    counts.update(published=sum(q['topicId']==topic for q in published),awaitingReview=sum(q['topicId']==topic for q in pending))
published_ids={q['id'] for q in published};pending_ids={i['questionId'] for i in pending}
progress['mockProgress']={}
for s in sets['sets']:
    ids={slot['questionId'] for slot in s['slots']}
    completed=len(ids & published_ids);awaiting=len(ids & pending_ids)
    progress['mockProgress'][s['id']]={'target':s['size'],'reviewed':completed,'awaitingReview':awaiting,'notCreated':s['size']-completed-awaiting}
    s['status']='ready' if completed==s['size'] else 'in_progress'
write(ROOT/'content/ap/mock-sets.json',sets);write(progress_path,progress)
print(json.dumps({'newDrafts':added,'published':len(published),'pending':len(pending),'sets':progress['mockProgress']},ensure_ascii=False))
