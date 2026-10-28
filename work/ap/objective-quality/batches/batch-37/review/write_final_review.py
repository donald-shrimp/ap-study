import json,hashlib,datetime,copy
from pathlib import Path
p=Path('work/ap/objective-quality/batches/batch-37')
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
before=json.loads((p/'review/initial-drafts.json').read_text()); final=json.loads((p/'drafts.json').read_text()); initial=json.loads((p/'review/independent-review.json').read_text()); inv={x['id']:x for x in json.load(open('work/ap/objective-quality/inventory.json'))}; src=json.load(open('data/sources.json')); now=datetime.datetime.now(datetime.timezone.utc).isoformat(); reviewer='Codex /root/ap_batch37_review'; changed={'r05a-q76','r04h-q77'}
assert sha((p/'review/independent-review.json').read_bytes())=='6a79e664b6c46f317fa0bbe213a176988e2893a299f73b909d5bb70df2b7acd3'
assert sha((p/'review/initial-drafts.json').read_bytes())=='f978108ae108b9e7f8cf6a72ae93e7d04d24913c38cb54afe9ba1a81737935b1'
rows=[]; questions=[]
for b,f,q in zip(before,final,initial['questions']):
 assert b['id']==f['id']==q['id']; id=f['id']; v=inv[id]
 assert canon(b)==q['beforeEnvelopeSHA256']; assert canon(b['lesson'])==q['beforeLessonSHA256']
 if id not in changed:assert b==f
 else:
  old=copy.deepcopy(b['lesson']); old['hints'][1]['revealsAnswer']=False; assert old==f['lesson']
  assert f['design']['stages'][1]['revealsAnswer']==False
  assert all(f['lesson']['hints'][i]['revealsAnswer']==f['design']['stages'][i]['revealsAnswer'] for i in range(3))
 assert q['sourceHashes']==v['sourceHashes']
 for file,h in q['sourceHashes'].items():assert sha(Path(file).read_bytes())==h
 pdf=q['officialAnswerPDF']; assert sha(Path(pdf['path']).read_bytes())==pdf['sha256'];assert next(s for s in src if s['url']==pdf['url'])['sha256']==pdf['sha256']
 flags=[h['revealsAnswer'] for h in f['lesson']['hints']]; assert flags==[h['independentlyAssessedRevealsAnswer'] for h in q['hintReview']]
 checks=q['checks'].copy();checks['revealFlags']=True
 notes=q['independentResult']+' '+('修正後の原本を再表示し全肢・教材・累積3ヒント・designを再確認。H2は判断を残すfalse、H3は正答明示のtrueで整合。' if id in changed else '初回全教材確認に対応するenvelope/lessonが最終もexact hash不変。')
 rows.append({'id':id,'author':f['author'],'reviewer':reviewer,'status':'approved','checkedAt':now,'baseLessonSHA256':v['baselineLessonSHA256'],'reviewedLessonSHA256':canon(f['lesson']),'questionSHA256':v['baselineQuestionSHA256'],'sourceHashes':q['sourceHashes'],'checks':{k:value for k,value in checks.items() if k!='design'},'notes':notes,'officialAnswer':q['officialAnswer'],'independentResult':q['independentResult'],'issues':[]})
 questions.append({'id':id,'status':'approved','reviewer':reviewer,'checkedAt':now,'beforeSnapshotEnvelopeSHA256':canon(b),'beforeSnapshotLessonSHA256':canon(b['lesson']),'finalEnvelopeSHA256':canon(f),'finalLessonSHA256':canon(f['lesson']),'sourceImageActuallyOpened':q['sourceImageActuallyOpened'],'sourceImageSHA256':q['sourceImageSHA256'],'sourceImageVerificationPhase':'初回実表示済み。最終でも修正2問は原本をview_imageで再表示し、残18問は実画像SHAと初回確認hashの不変を照合。','sourceHashes':q['sourceHashes'],'officialAnswerPDF':pdf,'officialAnswer':q['officialAnswer'],'independentResult':q['independentResult'],'finalReview':notes,'finalHintRevealFlags':flags,'hintReview':[dict(h,currentRevealsAnswer=flags[j]) for j,h in enumerate(q['hintReview'])],'checks':checks,'issues':[]})
(p/'reviews.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
report={'kind':'correction-independent-content-review','status':'approved','reviewer':reviewer,'checkedAt':now,'materialCorrector':'Codex /root','primaryAuthor':final[0]['author'],'initialAuthorHead':initial['initialAuthorHead'],'counts':{'questions':20,'approved':20,'changedQuestionsRechecked':2,'unchangedQuestionsExactEnvelopeAndLessonHashMatched':18,'initialOriginalImagesActuallyOpened':20,'finalOriginalImagesReopened':2,'choiceReasonsInitiallyRead':80,'cumulativeHintsInitiallyRead':60,'officialAnswerPDFsVerified':9,'resolvedIssues':2,'unresolvedIssues':0},'frozenInitialReview':{'path':str(p/'review/independent-review.json'),'sha256':sha((p/'review/independent-review.json').read_bytes())},'frozenBeforeSnapshot':initial['frozenBeforeSnapshot'],'finalDraftsFileSHA256':sha((p/'drafts.json').read_bytes()),'finalReviewsFileSHA256':sha((p/'reviews.json').read_bytes()),'resolvedIssues':[dict(i,resolution='rootがH2をfalseへ変更しdesignのremainingWork/reason/sourceNotesを同期。最終独立確認で本文不変と条件適用・名称対応の残存、H3の開示trueを再確認。',status='resolved') for i in initial['issues']],'limitations':'初学者試用・アプリ採点・構造試験は実施していない。採点等の統合検証はroot担当。教材は確認者自身で修正していない。','questions':questions}
(p/'review/correction-independent-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for name in ['drafts.json','reviews.json','review/initial-drafts.json','review/independent-review.json','review/correction-independent-review.json']:print(name,sha((p/name).read_bytes()))
assert len(rows)==len(questions)==20;assert all(q['status']=='approved' and not q['issues'] for q in questions)
