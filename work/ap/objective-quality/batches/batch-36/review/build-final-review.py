import json,hashlib,datetime,copy
from pathlib import Path
root=Path('/workspace/ap-study-batch36-review');p=root/'work/ap/objective-quality/batches/batch-36'
def sha(b):return hashlib.sha256(b).hexdigest()
def h(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
def read(path):return json.loads(path.read_text())
def write(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
initial=read(p/'review/independent-review.json');before=read(p/'review/initial-drafts.json');drafts=read(p/'drafts.json');inv={x['id']:x for x in read(root/'work/ap/objective-quality/inventory.json')};now=datetime.datetime.now(datetime.timezone.utc).isoformat();reviewer=initial['reviewer']
assert sha((p/'review/independent-review.json').read_bytes())=='72fff73bfd9b877fb2a86ba16e62637983d06fe74743230b379ff2e2e2f071ff'
assert sha((p/'review/initial-drafts.json').read_bytes())=='bfeb2946fd27b66cf22a2d0ae092d753a2cc59827b0c37dfbcda6ae051e14277'
resolutions={
'B36-01':'H2 false/design同期を承認。五圧力の仕組みを教え、名称との対応を残す。',
'B36-02':'H2 false/design同期を承認。詳細調査の性質を教えるが名称を渡さず全誤答も除外しない。',
'B36-03':'H2 false/design同期を承認。融合の仕組みを補い固有構想名との対応を残す。',
'B36-04':'keep→revise。H1で単価低下と共同費用低下の定義を補い、比較対象を教える。初学者の判断基準不足を解消。',
'B36-05':'H1定義追加後もH2を未計算の単価4式/共同費用2比較とし、計算・大小比較・効果判定を残す。累積false、H3 trueを承認。単価75/82.5円、50/55円、共同差100/200万円を再検算。',
'B36-06':'H1 false/design同期を承認。完成/遂行の定義から工程へ適用する判断が残る。',
'B36-07':'第二版・本問の範囲を明記。外部設計/システムテストは両型と補い、イの不適切理由を要件定義/導入支援を含むことへ訂正。r07h-q66の原本表も再実表示し整合。',
'B36-08':'H1 true/design同期を承認。SLを部下側の状況と対応させウの内容を実質渡している。'}
changed=[];unchanged=[];reviews=[];questions=[]
for old,e,first in zip(before,drafts,initial['questions']):
 assert old['id']==e['id']==first['id'];q=e['id'];i=inv[q];change=h(old)!=h(e);(changed if change else unchanged).append(q)
 assert h(old)==first['beforeEnvelopeSHA256'];assert h(old['lesson'])==first['beforeLessonSHA256']
 if not change:assert h(e)==first['beforeEnvelopeSHA256'] and h(e['lesson'])==first['beforeLessonSHA256']
 for path,digest in first['sourceHashes'].items():assert sha((root/path).read_bytes())==digest==i['sourceHashes'][path]
 assert sha(Path(first['officialAnswerPDF']['path']).read_bytes())==first['officialAnswerPDF']['sha256']
 hints=copy.deepcopy(first['hintReview'])
 if q=='r03a-q68':
  hints[0]['rationale']='二効果の定義と比較箇所を補い、単価計算と共同費用比較は残す。'
  hints[1]['rationale']='単価4式と共同費用の未計算比較を提示。前段の定義と合わせても数値計算・大小比較・二効果判定が残る。'
 for j,(hint,design) in enumerate(zip(e['lesson']['hints'],e['design']['stages'])):
  assert hint['revealsAnswer']==hints[j]['independentlyAssessedRevealsAnswer']==design['revealsAnswer'];assert hint['text']==design['newInformation'];hints[j]['currentRevealsAnswer']=hint['revealsAnswer']
 checks={k:True for k in ['source','answer','choices','hints','explanation','revealFlags']};checks['calculation']=first['checks']['calculation']
 finalnotes=('修正6問の該当原本をview_imageで再表示し、全4肢・全lesson・累積3ヒント/designを再読。'+' '.join(resolutions[x] for x in first['issues'])) if change else '初回承認対象のenvelope/lesson実canonical SHAと完全一致。原本/公式PDFの実SHAを再照合し初回の独立承認を継承。'
 reviews.append(dict(id=q,author=e['author'],reviewer=reviewer,status='approved',checkedAt=now,baseLessonSHA256=i['baselineLessonSHA256'],reviewedLessonSHA256=h(e['lesson']),questionSHA256=i['baselineQuestionSHA256'],sourceHashes=first['sourceHashes'],checks=checks,notes=first['independentResult']+' '+finalnotes,officialAnswer=first['officialAnswer'],independentResult=first['independentResult'],issues=[]))
 questions.append(dict(id=q,status='approved',reviewer=reviewer,checkedAt=now,beforeSnapshotEnvelopeSHA256=h(old),beforeSnapshotLessonSHA256=h(old['lesson']),finalEnvelopeSHA256=h(e),finalLessonSHA256=h(e['lesson']),sourceImageActuallyOpened=first['sourceImageActuallyOpened'],sourceImageSHA256=first['sourceImageSHA256'],sourceImageVerificationPhase='初回実表示・最終再実表示および実SHA照合' if change or q=='r07h-q66' else '初回実表示・最終実SHA照合',sourceHashes=first['sourceHashes'],officialAnswerPDF=first['officialAnswerPDF'],officialAnswer=first['officialAnswer'],independentResult=first['independentResult'],finalReview=finalnotes,finalHintRevealFlags=[x['revealsAnswer'] for x in e['lesson']['hints']],hintReview=hints,checks={**checks,'design':True},issues=[]))
assert len(changed)==6 and len(unchanged)==14
write(p/'reviews.json',reviews)
report=dict(kind='batch-correction-independent-review',status='approved',reviewer=reviewer,checkedAt=now,materialCorrector='Codex /root',primaryAuthor=drafts[0]['author'],initialAuthorHead=initial['initialAuthorHead'],counts=dict(questionsApproved=20,correctionsIndependentlyReviewed=6,resolvedInitialIssues=8,unchangedInitialEnvelopes=14,originalImagesActuallyOpenedInInitialReview=20,originalImagesActuallyReopenedInFinalReview=7,officialAnswerPDFsIndependentlyReadFromCacheInInitialReview=8,finalDomainHintDepthCasesActuallyExecutedByThisReviewer=0),frozenInitialReview=dict(path=str((p/'review/independent-review.json').relative_to(root)),sha256=sha((p/'review/independent-review.json').read_bytes())),frozenBeforeSnapshot=initial['frozenBeforeSnapshot'],finalDraftsFileSHA256=sha((p/'drafts.json').read_bytes()),finalReviewsFileSHA256=sha((p/'reviews.json').read_bytes()),resolvedIssues=[dict(id=x['id'],questionId=x['questionId'],status='resolved',materialCorrector='Codex /root',independentReviewer=reviewer,resolution=resolutions[x['id']]) for x in initial['issues']],changedQuestionIds=changed,unchangedQuestionIds=unchanged,limitations='初学者試用とアプリ採点実行は本確認者は未実施。採点はroot担当。本報告は内容独立確認と実ハッシュ照合の承認。',questions=questions)
write(p/'review/correction-independent-review.json',report)
# final consistency: every approval is tied to the actual final lesson and inventory sources
for e,r,q in zip(read(p/'drafts.json'),read(p/'reviews.json'),read(p/'review/correction-independent-review.json')['questions']):
 assert h(e['lesson'])==r['reviewedLessonSHA256']==q['finalLessonSHA256'];assert h(e)==q['finalEnvelopeSHA256'];assert r['status']==q['status']=='approved';assert r['sourceHashes']==q['sourceHashes']==inv[e['id']]['sourceHashes'];assert not r['issues'] and not q['issues']
for filename in ['drafts.json','reviews.json','review/independent-review.json','review/initial-drafts.json','review/correction-independent-review.json']:print(filename,sha((p/filename).read_bytes()))
