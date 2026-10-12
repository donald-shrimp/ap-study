"""Apply only independently checked, exact-hash transcription records.

Question identity, answer, lesson and source assets remain unchanged. Drafts are
never an input. Existing text outside this batch is left alone.
"""
import hashlib
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def refresh_context_reviews(root,before_bank,after_bank,records,before_context,after_context):
    """Journal representation-only edits; do not pretend old audits reviewed text."""
    if not after_context or before_context==after_context:
        return
    before={q['id']:q for q in before_bank};after={q['id']:q for q in after_bank}
    record_map={r['id']:r for r in records}
    old_context={r['questionId']:r for r in before_context['items']}
    new_context={r['questionId']:r for r in after_context['items']}
    changes=[]
    for id,q in after.items():
        if q==before[id]:continue
        changed={k for k in q if q[k]!=before[id].get(k)}
        if id not in record_map or not changed<={'stem','choices','image','imageAlt','version','choicePresentation'}:
            raise ValueError(f'Non-transcription source edit: {id}')
        if {k:v for k,v in old_context[id].items() if k!='sourceHash'}!={k:v for k,v in new_context[id].items() if k!='sourceHash'}:
            raise ValueError(f'Classification changed: {id}')
        changes.append({'id':id,'beforeQuestion':before[id],'afterQuestionSHA256':digest(q),
                        'beforeContextItem':old_context[id],'afterContextItem':new_context[id],
                        'transcriptionSHA256':digest(record_map[id])})
    directory=root/'content/ap/study-context-reviews';root_path=directory/'root.json'
    if not root_path.is_file():return
    review=json.loads(root_path.read_text())
    journal={'kind':'reviewed-transcription-representation','reviewer':'/root','beforeContextSHA256':digest(before_context),
             'afterContextSHA256':digest(after_context),'beforeRootReview':copy.deepcopy(review),'items':changes}
    filename=f'data/transcription-context-revisions/{digest(changes)[:16]}.json'
    path=root/filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(journal,ensure_ascii=False,indent=2)+'\n')
    review['sourceMetadataRevisions'].append({'runId':'transcription-integration-'+digest(changes)[:16],
       'revisionRecord':filename,'note':'確認済み文字起こしの表現・版だけを反映。紙ペン分類と理由は保持。変更前の問題と監査を台帳に保存。文字内容の確認者は各transcription-reviewを参照。'})
    review['combinedContextSha256']=digest(after_context)
    review['preservedR07hItemsSha256']=digest(sorted((i for i in after_context['items'] if i['questionId'].startswith('r07h-q')),key=lambda i:int(i['questionId'].split('-q')[1])))
    review['preservedContentSha256']['data/questions.json']=hashlib.sha256((root/'data/questions.json').read_bytes()).hexdigest()
    root_path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    for exam in {item['id'].split('-q')[0] for item in changes}:
        path=directory/f'{exam}.json'
        if not path.is_file():continue
        review=json.loads(path.read_text());review['publishedItemsSha256']=digest(sorted((i for i in after_context['items'] if i['questionId'].startswith(exam+'-q')),key=lambda i:int(i['questionId'].split('-q')[1])))
        review.setdefault('sourceMetadataRevisions',[]).append({'revisionRecord':filename,'note':'分類と理由は不変。原本文字起こし後の教材参照ハッシュに更新。'})
        path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')


def checked_records(root=ROOT):
    bank=json.loads((root/'data/questions.json').read_text())
    by_id={q['id']:q for q in bank}
    records=[]
    seen=set()
    for source in sorted((root/'data/transcriptions').glob('*.json')):
        review_file=root/'data/transcription-reviews'/source.name
        if not review_file.is_file():
            raise ValueError(f'Missing transcription reviews: {source.name}')
        reviews=json.loads(review_file.read_text())
        if len({r['id'] for r in reviews})!=len(reviews):
            raise ValueError(f'Duplicate review: {source.name}')
        reviews={r['id']:r for r in reviews}
        entries=json.loads(source.read_text())
        if set(reviews)!={r['id'] for r in entries}:
            raise ValueError(f'Review coverage differs: {source.name}')
        for record in entries:
            id=record['id'];q=by_id.get(id);review=reviews[id]
            if not q or id in seen:
                raise ValueError(f'Unknown/duplicate transcription: {id}')
            seen.add(id)
            if record['format']!='hitomon-markdown-math-v1' or not record['stem'].strip():
                raise ValueError(f'Invalid format/body: {id}')
            if record.get('choicePresentation','inline') not in ['inline','codes'] or record.get('choicePresentation')=='codes' and not record.get('image'):
                raise ValueError(f'Invalid grouped choice presentation: {id}')
            if len(record['choices'])!=len(q['choices']) or [c['label'] for c in record['choices']]!=[c['label'] for c in q['choices']]:
                raise ValueError(f'Choice count/order differs: {id}')
            if any(not isinstance(c.get('text'),str) or not(c['text'].strip() or c.get('image')) or set(c)-{'label','text','image'} for c in record['choices']):
                raise ValueError(f'Incomplete/invalid choice: {id}')
            if review['status']!='confirmed' or not review['reviewer'] or review['reviewer']==record['author']:
                raise ValueError(f'Independent review missing: {id}')
            if review['reviewedTranscriptionSHA256']!=digest(record) or not review['evidence']:
                raise ValueError(f'Review hash/evidence mismatch: {id}')
            if not all(review['checks'].get(k) is True for k in ['wording','math','tables','figures','choices','source']):
                raise ValueError(f'Incomplete review: {id}')
            hashes=[hashlib.sha256((root/path).read_bytes()).hexdigest() for path in q['sourceImages']]
            if hashes!=record['sourceImageSHA256']:
                raise ValueError(f'Source changed: {id}')
            source_evidence={}
            for proof in record.get('sourceEvidence',[]):
                path=proof['path']
                if not path.startswith('assets/transcription-sources/') or not (root/path).resolve().is_relative_to(root.resolve()) or not (root/path).is_file():
                    raise ValueError(f'Invalid supplemental source: {id}')
                sha=hashlib.sha256((root/path).read_bytes()).hexdigest()
                if sha!=proof['sha256'] or not proof.get('pdfSHA256') or not proof.get('reason'):
                    raise ValueError(f'Supplemental source changed: {id}')
                source_evidence[path]=sha
            if source_evidence!=review.get('sourceEvidenceSHA256',{}):
                raise ValueError(f'Supplemental source review mismatch: {id}')
            figure_hashes={}
            for image in [record.get('image'),*[c.get('image') for c in record['choices']]]:
                if image and (not image.startswith('assets/transcriptions/') or not (root/image).resolve().is_relative_to(root.resolve()) or not (root/image).is_file()):
                    raise ValueError(f'Missing/invalid figure: {id}')
                if image:
                    figure_hashes[image]=hashlib.sha256((root/image).read_bytes()).hexdigest()
            if figure_hashes!=review.get('figureSHA256'):
                raise ValueError(f'Reviewed figure changed: {id}')
            records.append(record)
    return bank, records


def checked_retentions(root=ROOT, bank=None, records=None):
    """An independently checked decision to keep the unchanged original image."""
    if bank is None or records is None:
        bank, records = checked_records(root)
    path = root/'data/transcription-image-retentions.json'
    entries = json.loads(path.read_text()) if path.is_file() else []
    by_id = {q['id']: q for q in bank}
    seen = {r['id'] for r in records}
    for entry in entries:
        id = entry['id']; q = by_id.get(id)
        if not q or id in seen:
            raise ValueError(f'Unknown/duplicate image retention: {id}')
        seen.add(id)
        if entry.get('status') != 'image-retained' or not entry.get('reason') or not entry.get('evidence'):
            raise ValueError(f'Incomplete image retention: {id}')
        if not entry.get('assessor') or not entry.get('reviewer') or entry['assessor'] == entry['reviewer']:
            raise ValueError(f'Independent retention review missing: {id}')
        decision = {k:v for k,v in entry.items() if k != 'reviewedDecisionSHA256'}
        if entry.get('reviewedDecisionSHA256') != digest(decision):
            raise ValueError(f'Retention review hash mismatch: {id}')
        hashes = [hashlib.sha256((root/p).read_bytes()).hexdigest() for p in q['sourceImages']]
        if hashes != entry.get('sourceImageSHA256') or q.get('stem'):
            raise ValueError(f'Retained image source/representation changed: {id}')
        if entry.get('priorReview'):
            previous_path=(root/entry['priorReview']).resolve()
            if not previous_path.is_relative_to(root.resolve()):
                raise ValueError(f'Invalid retention evidence path: {id}')
            previous=next((r for r in json.loads(previous_path.read_text()) if r['id']==id),None)
            if not previous or digest(previous)!=entry.get('priorReviewSHA256'):
                raise ValueError(f'Retention evidence hash mismatch: {id}')
    return entries


def draft_question_ids(root):
    """Local external drafts count as pending too; review histories do not."""
    ids=set()
    folder=root/'data/transcription-drafts'
    for pattern in ['transcribe_*.json','chatgpt_*.json']:
        for file in folder.glob(pattern):
            ids.update(r['id'] for r in json.loads(file.read_text()))
    return ids


def apply(root=ROOT):
    bank,records=checked_records(root)
    retentions=checked_retentions(root,bank,records)
    context_path=root/'content/ap/study-context.json'
    context=json.loads(context_path.read_text()) if context_path.is_file() else None
    before_context=copy.deepcopy(context)
    before_bank=copy.deepcopy(bank)
    classifications={r['questionId']:r for r in context['items']} if context else {}
    # KaTeX must be able to render every formula before changing the bank.
    if root==ROOT:
        subprocess.run(['node', str(ROOT/'tools/check-question-text.mjs')],check=True)
    by_id={q['id']:q for q in bank}
    for record in records:
        q=by_id[record['id']]
        classification=classifications.get(q['id'])
        if classification and classification['sourceHash']!=digest(q):
            raise ValueError(f'Classification source changed before transcription: {q["id"]}')
        replacement={key:record[key] for key in ['stem','choices','image','imageAlt']}
        if 'choicePresentation' in record or 'choicePresentation' in q:
            replacement['choicePresentation']=record.get('choicePresentation','inline')
        if any(q.get(key)!=value for key,value in replacement.items()):
            q.update(replacement)
            q['version']+=1
        # Text-only representation changes do not change the verified paper/pen
        # classification. Keep its exact-source link current, without relabeling.
        if classification:
            classification['sourceHash']=digest(q)
    (root/'data/questions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n')
    if context:
        context_path.write_text(json.dumps(context,ensure_ascii=False,indent=2)+'\n')
        refresh_context_reviews(root,before_bank,bank,records,before_context,context)
    ids={r['id'] for r in records}
    retained_ids={r['id'] for r in retentions}
    covered=ids|retained_ids
    packs=[]
    for pack in sorted({id.split('-q')[0] for id in ids}):
        chosen=sorted((id for id in ids if id.startswith(pack+'-q')),key=lambda id:int(id.split('-q')[1]))
        packs.append({'id':pack,'count':len(chosen),'ids':chosen})
    draft_ids=draft_question_ids(root)
    text_count=sum(bool(q['stem']) and all(c.get('text') or c.get('image') for c in q['choices']) for q in bank)
    candidates=[p['id'] for p in packs]+sorted({q['id'].split('-q')[0] for q in bank}-{p['id'] for p in packs})
    next_batch=None
    for pack in candidates:
        numbers=sorted(q['number'] for q in bank if q['id'].startswith(pack+'-q') and q['id'] not in covered)
        if numbers:
            next_batch={'packId':pack,'numbers':numbers[:10]};break
    progress={'format':'hitomon-transcription-progress','version':1,'total':len(bank),'reviewed':len(records),
        'imageRetained':len(retentions),'processed':len(covered),'imageRetainedIds':sorted(retained_ids),
        'remainingReview':len(bank)-len(covered),'displayText':text_count,'preservedExistingText':text_count-len(records),
        'pendingDrafts':len(draft_ids-covered),'packs':packs,'nextBatch':next_batch}
    (root/'data/transcription-progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
    print(f'Independently reviewed transcriptions: {len(records)}/{len(bank)}')
    print(f'Original images retained: {len(retentions)}; coverage: {len(covered)}/{len(bank)}')
    if root==ROOT:
        subprocess.run([sys.executable,str(ROOT/'tools/build-content.py')],check=True)


if __name__=='__main__':
    apply()
