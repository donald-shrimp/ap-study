from pathlib import Path
import json,hashlib
D=Path('content/ap/written-drafts/2024/author-spring-7-11')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(c):return hashlib.sha256(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
cases=[json.load(open(D/f'ap-r06h-pm{n}.json')) for n in range(7,12)]
crops=json.loads((D/'crop-evidence-8.json').read_text())+json.loads((D/'crop-evidence-9.json').read_text())+json.loads((D/'crop-evidence-11.json').read_text())
for name,page,box in [('figure-1',41,[136,373,544,739]),('figure-2',41,[608,390,923,741]),('figure-3',44,[124,426,924,645]),('figure-4',44,[146,765,923,1153])]:
 p=f'assets/written/ap-r06h-pm7/{name}.png';crops.append(dict(caseId='ap-r06h-pm7',image=p,source=f'assets/written/ap-r06h-pm7/question-p{page:02}.png',box=box,sha256=sha(p)))
e=dict(author='/root/author_2024_spring_7_11',status='awaiting-independent-review',method='公式PDFから親担当が2倍でレンダーした原問PNGを全23頁，view_imageで実表示して全文・全設問・全図表を読み，原文どおり手動文字化。図9枚はその既存PNGから忠実クロップし，完成cropも全てview_imageで実表示した。解答PDFの4〜6頁，採点講評2〜3頁のPNGも実表示。日本語OCR出力（問8・48頁）を参考にしたが，最終確認は実画像で行った。',sourcePDFs=[s for s in json.load(open('content/ap/written-drafts/2024/sources/sources.json')) if '2024r06h' in s['path']],visuallyReadQuestionImages=[p for c in cases for p in c['sourceImages']],visuallyReadAnswerImages=[f'content/ap/written-drafts/2024/sources/2024r06h_ap_pm_ans-p{p:02}.png' for p in [4,5,6]],visuallyReadCommentaryImages=[f'content/ap/written-drafts/2024/sources/2024r06h_ap_pm_cmnt-p{p:02}.png' for p in [2,3]],visuallyReadCrops=[x['image'] for x in crops],cropEvidence=crops,sourceImageHashes={p:sha(p) for c in cases for p in c['sourceImages']},caseSHA256={c['id']:canonical(c) for c in cases},calculations=[{'caseId':'ap-r06h-pm7','itemId':'q1-2','calculation':'32 kHz × 10 ms = 32000 /s × 0.010 s = 320','checkedReloadSemantics':'0になった後，次のカウントダウンまでの間にリロードするので初期値320。319ではない。'},{'caseId':'ap-r06h-pm7','itemId':'q2-3','calculation':'最初の0の4連続はウ・エ・オ・カ→ドア閉=カ。後半はサ=1，シ=0の後，ス・セ・ソ・タが1の4連続→ドア開=タ。'}],notes=['春問11は63〜66頁で完結。67頁はメモ用紙で教材sourceImagesに含めない。','問8設問2c公式例は図記号。referenceAnswersは上向き白抜き三角形と接続実線を文字で説明した学習用表現であり，公式文章ではない。自己評価で原図の表記も確認。','問7設問3(1)と問8設問3は全て列挙のため自己評価。問9設問2(3)b/cは公式順不同なので2欄を合わせて過不足を自己評価。'],unverified=['作成者自身の確認は独立レビューではない。全5大問の別担当レビュー完了待ち。'])
(D/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
for c in cases:
 assert c['body'] and c['authoringStatus']=='awaiting-independent-review'
 fs=[f for i in c['items'] for f in i['fields']]
 assert len(fs)<=20
 for f in fs:
  assert f['referenceAnswers'] and f['explanation'] and f['rubric']
  if f['type']!='singleChoice':
   assert isinstance(f['maxLength'],int) and 1<=f['maxLength']<=2000
   assert all(len(a)<=f['maxLength'] for a in f['referenceAnswers']),(c['id'],f['id'],f['referenceAnswers'])
 for fig in c['bodyFigures']:assert c['body'].count(fig['anchor'])==1
 print(c['id'],len(fs),canonical(c))
