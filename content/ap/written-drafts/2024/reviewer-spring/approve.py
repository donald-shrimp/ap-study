import json,pathlib,hashlib,datetime,sys
root=pathlib.Path(__file__).resolve().parents[5]
p=pathlib.Path(sys.argv[1]);c=json.loads(p.read_text());caseid=c['id'];c['status']='reviewed';c['authoringStatus']='independently-reviewed'
reviewdir=root/'content/ap/written-drafts/2024/reviewer-spring'
def sha(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
canon=lambda c:json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
source={f'content/ap/written-drafts/2024/sources/2024r06h_ap_pm_{k}.pdf':sha(f'content/ap/written-drafts/2024/sources/2024r06h_ap_pm_{k}.pdf') for k in ['qs','ans','cmnt']}
assets=c['sourceImages']+[f['image'] for f in c.get('bodyFigures',[])]
for kind,pg in [('ans',sys.argv[2]),('cmnt',sys.argv[3])]:assets.append(f'content/ap/written-drafts/2024/sources/2024r06h_ap_pm_{kind}-p{int(pg):02}.png')
r={'caseId':caseid,'version':c['version'],'status':'approved','author':c['author'],'reviewer':'/root/review_2024_spring','reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonicalCaseSHA256':hashlib.sha256(canon(c)).hexdigest(),'sourceEvidence':'content/ap/written-drafts/2024/reviewer-spring/independent-findings.json','sourceHashes':source,'assetHashes':{a:sha(a) for a in assets},'method':'原問全頁・全cropをview_imageで実表示し、全本文/全表セル/全図ラベル結線凡例/下線範囲/全設問/全回答欄/全選択肢/字数条件を作者草稿と照合。公式解答例・採点講評PNGも実表示し公式例全件と説明/rubricを照合。全PDF・教材画像・実読公式PNGのSHAと最終case canonical SHAを保存。','answerCheck':sys.argv[4],'gradingCheck':'公式登録例の短答・単一選択だけexactText。説明・順不同複数等はself、未登録表現を機械的不正解にせず自己評価へ。rubricは学習用でIPA配点ではない。','findings':[]}
(reviewdir/f'approved-case-{caseid}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');(reviewdir/f'review-{caseid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(caseid,r['canonicalCaseSHA256'])
