"""One-shot metadata review of a known snapshot, after actual body review."""
import json,hashlib,copy,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/workspace/ap-study-ab730-content');P=ROOT/'content/ab730/authoring/reviewer'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
AUTHOR=ROOT/'content/ab730/authoring/author-drafts.json';CFG=ROOT/'content/ab730/qualification.json'
assert sha(AUTHOR)=='b4c41f2d0ca8895cf9e9678c0f614d38dc6eb9512d86ece4e46afc1404f8d54f'
assert sha(CFG)=='e0403ac6ca67530329156b26fdff30ece67c0d05fff1552658b86c971e095c81'
oldq=read(P/'body-approved-snapshot.json');qs=read(AUTHOR);reviews=read(P/'final-reviews.json');config=read(CFG);status=read(P/'final-review-status.json');stamp=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
oldr={r['questionId']:r for r in reviews};new=[];changes=[];unchanged=[]
assert len(qs)==len(oldq)==187
for n,(before,after) in enumerate(zip(oldq,qs),1):
 assert before['id']==after['id'];fields=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]
 assert not fields or fields==['sourceRefs'],(n,fields)
 if fields:changes.append({'intakeId':f'Q{n:03}','questionId':after['id'],'changedFields':fields,'before':before['sourceRefs'],'after':after['sourceRefs']})
 r=oldr.get(after['id'])
 if not r:
  assert not fields,'Held draft metadata changed unexpectedly';continue
 # Config additions must not change the previous normalized question except new sourceRefs.
 assert b.diagnostic_digest(b.normalize(before,config,n))==r['normalizedSha256'],('config normalized content unexpectedly changed',n)
 expected=list(dict.fromkeys(e['url'] for e in r['evidence']))
 assert after['sourceRefs']==expected,(n,after['sourceRefs'],expected)
 assert all(u.startswith(('https://learn.microsoft.com/','https://support.microsoft.com/')) for u in expected)
 for e in r['evidence']:
  path=ROOT/e['archivedPath'];assert path.exists();assert sha(path)==e['contentSha256'];assert e['excerpt'] in path.read_text();assert e.get('reviewedContent',True)
 nr=copy.deepcopy(r);rawhash=b.diagnostic_digest(after);normhash=b.diagnostic_digest(b.normalize(after,config,n))
 if fields:
  nr['sha256']=rawhash;nr['normalizedSha256']=normhash;nr['checkedAt']=stamp
  nr['notes']+=' 出典メタデータの最終確認: sourceRefsだけが、実際に読んだreview.evidenceのMicrosoft公式URL一覧へ変更されたことを旧承認スナップショットと全フィールド比較で確認。問題文・選択肢・正答・解説・各候補理由は不変。最終資格設定によるnormalizeと両SHAを再計算。'
  nr['metadataReview']={'checkedAt':stamp,'reviewer':'/root/ab730_reviewer','changedFields':['sourceRefs'],'previousSha256':r['sha256'],'previousNormalizedSha256':r['normalizedSha256'],'bodyUnchanged':True,'sourceRefsMatchReadEvidence':True}
 else:
  assert nr['sha256']==rawhash and nr['normalizedSha256']==normhash;unchanged.append(after['id'])
 new.append(nr)
assert len(changes)==161 and len(new)==177 and len(unchanged)==16
approved=[q for q in qs if q['id'] in oldr];normalized=[b.normalize(q,config,n) for n,q in enumerate(qs,1) if q['id'] in oldr];b.validate_reviews(approved,new,normalized)
# Preserve the actual body-review record set before metadata hash refresh.
write(P/'body-final-reviews-snapshot.json',reviews);write(P/'final-reviews.json',new)
byid={r['questionId']:r for r in new}
for x in status['records']:
 q=next(q for q in qs if q['id']==x['questionId']);x['sha256']=b.diagnostic_digest(q)
 if x['status']=='approved':x['normalizedSha256']=byid[q['id']]['normalizedSha256']
status.update(checkedAt=stamp,authorFileSha256=sha(AUTHOR),qualificationFileSha256=sha(CFG),stage='final-approved-after-sourceRefs-cleanup',approved=177,held=10,requiresCorrection=0)
write(P/'final-review-status.json',status);write(P/'final-approved-snapshot.json',qs)
receipt={'checkedAt':stamp,'author':'/root','reviewer':'/root/ab730_reviewer','authorFileSha256':sha(AUTHOR),'qualificationFileSha256':sha(CFG),'approved':177,'held':10,'requiresCorrection':0,'sourceRefsOnlyChanged':161,'retainedExactReviews':16,'all187BodiesUnchanged':True,'sourcesMatchActualReadOfficialEvidence':True,'configAddsNoNormalizedQuestionChanges':True,'builderReviewGatePassed':True,'changes':changes,'unchangedApprovedQuestionIds':unchanged}
write(P/'metadata-review-receipt.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k not in ['changes','unchangedApprovedQuestionIds']},ensure_ascii=False))
