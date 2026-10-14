import json,hashlib,importlib.util,copy
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/workspace/ap-study-ab730-content');P=ROOT/'content/ab730/authoring/reviewer'
# One-shot record reconciliation for the bodies already actually read by this reviewer.
# This is not an automatic content reviewer; unseen future drafts must never pass.
EXPECTED_READ_AUTHOR_SHA='a52b46f5f78a824e6ed92c0fc19167bae7321196fe27ca5a4c847a9d50bb74da'
assert hashlib.sha256((ROOT/'content/ab730/authoring/author-drafts.json').read_bytes()).hexdigest()==EXPECTED_READ_AUTHOR_SHA, 'Unreviewed author snapshot: actual review required.'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
qs=read(ROOT/'content/ab730/authoring/author-drafts.json');config=read(ROOT/'content/ab730/qualification.json');old=read(P/'final-reviews.json');blind=read(P/'blind-solutions.json');findings=read(P/'final-findings.json');stamp=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
held={7,16,35,76,121,123,128,138,158,164}
prev={r['questionId']:r for r in old};issues={x['questionId']:x for x in findings};catalog={Path(e.get('archivedPath',e['path'])).stem:copy.deepcopy(e) for r in blind+old for e in r['evidence']}
index=read(Path('/workspace/research/ab730-complete/index.json'));extras=read(P/'evidence/extra-index.json')
def proof(key,start,end):
 path=P/'evidence'/f'{key}.txt';lines=path.read_text().splitlines()
 if key in catalog:e=copy.deepcopy(catalog[key])
 else:
  x=next(x for x in extras if x.get('path')==str(path));e={'url':x.get('finalURL',x['url']),'path':str(path),'fetchedAt':x['fetchedAt'],'reviewedContent':True}
 e['contentSha256']=hashlib.sha256(path.read_bytes()).hexdigest();e['archivedPath']=str(path.relative_to(ROOT));e['excerpt']='\n'.join(lines[start-1:end]);e['excerptLine']=start
 return e
# Supporting passages actually read; these replace/add precise support where blind-stage snippets were broad.
extra_word=proof('0b32a13c5836f41f',29,39)
extra_teams=proof('f8b585bfdb043b4f',1,12)
schedule=proof('66',7,21);privacy=proof('16',20,34);retention=proof('42',42,51);roles=proof('30',24,46);sandbox=proof('32',35,36)
replacements={14:['69','34'],48:['56','79'],55:['60'],58:['60'],95:['36','77','9'],131:['71'],154:['16','42'],160:['53','69'],161:['36','60','31','66'],165:['53','69'],177:['4'],183:['34','11','4']}
additions={3:[schedule],4:[schedule],6:[retention],14:[],22:[retention],28:[schedule],30:[schedule],47:[proof('11f06b4bb93b5336',1,34)],48:[catalog['79']],50:[privacy],55:[extra_teams],58:[extra_teams],62:[schedule],70:[extra_word],81:[extra_word],98:[catalog['38']],117:[privacy],120:[privacy],131:[roles],154:[privacy],161:[schedule],162:[retention],177:[sandbox]}
new=[];statuses=[];retained=0;updated=0
for n,(q,b) in enumerate(zip(qs,blind),1):
 rawhash=builder.diagnostic_digest(q);normalized=builder.normalize(q,config,n);normhash=builder.diagnostic_digest(normalized)
 if n in held:
  x=issues.get(q['id'],{});statuses.append({'intakeId':f'Q{n:03}','questionId':q['id'],'status':'held','sha256':rawhash,'reason':x.get('issue',b.get('notes','Insufficient official evidence for a unique answer.')),'author':'/root','reviewer':'/root/ab730_reviewer'});continue
 r=prev.get(q['id'])
 if r and r['sha256']==rawhash and r['normalizedSha256']==normhash:
  r=copy.deepcopy(r);retained+=1
 else:
  evidence=[copy.deepcopy(catalog[k]) for k in replacements[n]] if n in replacements else copy.deepcopy(b['evidence'])
  evidence+=copy.deepcopy(additions.get(n,[]));unique=[]
  for e in evidence:
   if not any(z['url']==e['url'] and z['excerpt']==e['excerpt'] for z in unique):unique.append(e)
  assert len(q['choiceReasons'])==len(q['choices'])
  ids=[c['id'] for c in q['choices']]
  if q['type']=='multipleChoice':
   answers=q['correctChoiceIds'];assert len(set(answers))==len(answers) and set(answers)<=set(ids)
   assert q['selection']['mode']=='all' or q['selection']['count']==len(answers)
   answer_note='複数選択の正答集合を全候補と比較し、exact/all条件・指定数・採点対象IDを照合。'
  else:
   assert q['correctChoiceId'] in ids;answer_note='全候補を比較し単一正答の一意性を確認。'
  issue=issues.get(q['id'],{}).get('issue','')
  notes='提供正答・著者草稿を見る前にblind187を独立解答済み。著者の最終草稿の問題文・全選択肢・正答・解説・各選択肢理由を実際に読み、公式本文と再照合。'+answer_note+'日本語試験の新版適用日は未確認。資料の2026-10-14確認日を試験適用日とは扱わない。'
  if issue:notes+=' 初回指摘: '+issue+' 修正後の文と全候補理由を再読し解消を確認。'
  if n in [160,165]:notes+=' 引用されたエラーから原因を断定せず、示されたファイル状態を最初に確認する診断行動として審査。公式資料にこの文面と原因の一対一対応があるとは認定しない。'
  if n==129:notes+=' Analystの資料で直接確認したのはデータ統合・分析・可視化。特定のセンチメント分析の正確性や個別機能の保証は認定しない。'
  if n==131:notes+=' Researcherの対話/処理時設定と、Agent Builderの所有者が編集する永続的な指示・ナレッジ構成を区別。'
  if n in [177,183]:notes+=' Foundry資料は攻撃/防御概念の証拠であり、Foundry設定画面がMicrosoft365 Copilot UIに存在するとは扱わない。'
  r={'questionId':q['id'],'version':q['version'],'sha256':rawhash,'normalizedSha256':normhash,'author':'/root','reviewer':'/root/ab730_reviewer','checkedAt':stamp,'checks':{'source':True,'answer':True,'choices':True,'wording':True,'calculation':True if n==28 else 'not-applicable'},'notes':notes,'evidence':unique,'status':'approved'};updated+=1
 new.append(r);statuses.append({'intakeId':f'Q{n:03}','questionId':q['id'],'status':'approved','sha256':rawhash,'normalizedSha256':normhash,'author':'/root','reviewer':'/root/ab730_reviewer'})
 assert r['sha256']==rawhash and r['normalizedSha256']==normhash
assert len(new)==177 and len(statuses)==187
write(P/'body-approved-snapshot.json',qs);write(P/'final-reviews.json',new)
for f in findings:
 q=next(q for q in qs if q['id']==f['questionId']);n=qs.index(q)+1
 if n not in held:f['resolution']='Corrected draft reread with all choices/reasons; see current final-reviews.json exact hashes.';f['status']='resolved';f['resolvedSha256']=builder.diagnostic_digest(q);f['resolvedAt']=stamp
 else:f['status']='held'
write(P/'final-findings.json',findings)
summary={'checkedAt':stamp,'author':'/root','reviewer':'/root/ab730_reviewer','authorFileSha256':hashlib.sha256((ROOT/'content/ab730/authoring/author-drafts.json').read_bytes()).hexdigest(),'qualificationFileSha256':hashlib.sha256((ROOT/'content/ab730/qualification.json').read_bytes()).hexdigest(),'approved':177,'held':10,'requiresCorrection':0,'retainedExactReviews':retained,'newOrRevisedActualReviews':updated,'records':statuses,'stage':'body-approved-before-sourceRefs-cleanup'}
write(P/'final-review-status.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='records'},ensure_ascii=False))
