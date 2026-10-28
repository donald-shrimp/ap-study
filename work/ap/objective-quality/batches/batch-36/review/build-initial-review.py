import json,hashlib,datetime
from pathlib import Path
root=Path('/workspace/ap-study-batch36-review'); p=root/'work/ap/objective-quality/batches/batch-36'; cache=Path('/workspace/scratch/ap-a-quality-review/sources')
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
c=json.loads((p/'context.json').read_text()); d=json.loads((p/'drafts.json').read_text()); before=json.loads((p/'review/initial-drafts.json').read_text());assert d==before
inventory={x['id']:x for x in json.loads((root/'work/ap/objective-quality/inventory.json').read_text())}; sources=json.loads((root/'data/sources.json').read_text())
notes=[
'アクティビティ図は処理順序・分岐・並行・同期。クラスは構造、状態マシンは状態遷移、ユースケースは利用者と機能でア。',
'処理の制御フローと並行・同期を扱うアクティビティ図がア。構造/状態/機能関係の他三図と区別した。',
'五つの競争圧力はファイブフォースでエ。PESTはマクロ環境、VRIOは資源、バリューチェーンは活動。',
'A新規300−100=200、a新規200×3−100=500。b正味200×2+500×1−300=600個でイ。cはbの下位でも上位でもなく対象需要を変えない。',
'A200個、a500個を新規製造。b直接400+間接500−b在庫300=600個でイ。既存a100に内包されたbは再調達しない。',
'表のa=要件定義とd=運用テストは準委任、b=内部設計とc=結合は請負でイ。外部設計/システムテストは表の通り両型。第二版の設問であり契約一般への固定分類にはしない。',
'顕在化時の事前対応計画はエ。実績外注による確率低減、品質契約、通常の比較選定は発生時対応計画を述べない。',
'共通フレーム2013という原本の時点・前提で、費用を見積もる前提となる機能・性能・制約の要件定義書がエ。納品/評価/見積結果の文書とは時点・役割が異なる。',
'単価A1500/20=75円、B3300/40=82.5円、C500/10=50円、D1100/20=55円で規模利益なし。E1900<2000=A+C、F4200<4400=B+Dで共同費用削減100/200万円、シナジーありのイ。共同生産でもE1900/30からF4200/60へ平均費用は増加。',
'第二版の図で内部設計から結合までを示すエ。ア/イは導入支援まで、ウも要件定義を含む。システムテストは常に請負不可という一般則にはしない。',
'買収前に財務・法務・事業等の価値/リスクを確認するデューデリジェンスがエ。株主権行使/公開買付公告/市場分割とは異なる。',
'サイバー・フィジカル融合による超スマート社会の構想名はSociety 5.0でイ。行政サービス/利用者参加Web/多様性社会と区別。',
'PMはPerformance=目標達成とMaintenance=集団維持の二機能でイ。資質の特性理論、部下成熟度のSL、状況適合性の理論とは異なる。',
'SLは部下の成熟・自律性に合わせるのでウ。資質は特性理論、P/M二軸はPM、統制力等への適合はフィードラー理論。',
'SLは部下成熟度と教示/説得/参加/委任を対応させるイ。四窓はジョハリ、四知識過程はSECI、五欲求段階はマズロー。',
'SLの成熟度別四スタイルがイ。アの自己理解、ウの知識創造、エの欲求階層は目的が異なる。',
'既存アイデアの類似性によるグループ化は親和図法でウ。NM/ゴードン/ブレーンストーミングは発想を広げる手法。',
'親和図法が収束技法のウ。原本の引き出された後という条件で発散の三手法から区別。',
'商品の仕入支出は通常営業でイ。株式発行と借入返済は財務、固定資産売却は投資。収入/支出の符号では分類しない。',
'デルファイは専門家への匿名調査→集計共有→再回答を反復し収束させるエ。先行指標/方程式/観測データ比較ではない。']
rationales=[
['順序を見る比較軸のみで図名との対応が残る','分岐/並行/同期の意味を教えるが図の名称は残る','アクティビティ図と特徴を直接対応させる'],
['流れという対象の整理で図名の判別は残る','フォーク/ジョインの仕組みを教えるが図名との対応は残る','アクティビティ図と他三図を名称付きで区別'],
['分析対象の分類のみで枠組み名が残る','五圧力の収益への作用を説明するが名称との対応は残る。説明→名称型で名称未提示、全誤答排除もない','ファイブフォースの名称を明示'],
['Aの新規製造数のみで下位需要計算が残る','a新規500を求めるがb二経路合算と在庫控除が残る','bの最終加減乗算を本人に残す'],
['A新規200だけで下位展開が残る','a新規500を教えるがb正味計算が残る','直接/間接bと在庫の最終計算が残る'],
['準委任/請負の定義と列記号の対応だけで工程条件適用が残る','a/dという正答組合せを明示','a/dを明示している'],
['コンティンジェンシーを発生時対応と対応させ正答エの内容を渡す','前段に加えて部品供給停止対応例でエを直接説明','エに固有の文言を示す'],
['依頼前後の役割を分けるが要求文書の名称対応は残る','要件定義書の名称と依頼の前提役割を明示','要件定義書を先に提示と答えを明示'],
['比較対象は示すが概念の定義がなく初学者への判断基準が不足。答えは開示しない','数値大小関係を示すが単価低下/共同費用削減を各効果へ対応させる判断が残る','両効果の有無とイを明示'],
['完成/遂行という一般基準を示すが開始終了工程への適用を本人に残す','内部設計から結合までという正答範囲を明示','エと工程範囲を直接明示'],
['調査対象例を補うが専門名称との対応が残る','詳細調査の具体例と市場分割との違いを教えるが調査名の対応が残り、全誤答を除外していない','デューデリジェンスの名称を明示'],
['サイバー/フィジカルの定義を補うが構想名が残る','融合の仕組みと行政電子化との差を補うがSociety 5.0への名称対応が残る','Society 5.0の名称を明示'],
['PMを二機能の両立と対応させ二次元のイを実質説明','P/Mの二機能を明示しイと同じ内容を渡す','目標達成/集団維持の二次元を直接指定'],
['SLを指導される相手の状況と対応させ、他の三肢と区別されるウの特徴を実質提示','部下成熟度・自律性とSLを直接対応','成熟度というウの説明を直接指定'],
['SLの主題を部下への指示支援と示し指導理論のイを確定','成熟度と四スタイルを直接説明','四スタイルと成熟度を示す肢を指定'],
['SLを部下状況に応じた指導と定義し、イの対象を直接提示','成熟度と四スタイルを直接説明','四指導スタイルの肢を指定'],
['発散/収束を定義するが収束技法の名称は残る','親和図法の名称とグループ化を対応','親和図法を選ぶと明示'],
['発散/収束の違いを教えるが名称との対応は残る','親和図法と収束の機能を直接対応','親和図法の名称を直接提示'],
['現金出入と分類軸を補うが三分類への各取引の適用が残る','仕入は営業と正答取引を直接分類','商品の仕入が営業と正答を直接示す'],
['デルファイを専門家知見と対応させ全数値分析肢を排除','専門家反復調査という正答説明を渡す','正答固有の反復アンケートを指定']]
assessed=[[False,False,True],[False,False,True],[False,False,True],[False]*3,[False]*3,[False,True,True],[True]*3,[False,True,True],[False,False,True],[False,True,True],[False,False,True],[False,False,True],[True]*3,[True]*3,[True]*3,[True]*3,[False,True,True],[False,True,True],[False,True,True],[True]*3]
issue_specs=[('r06h-q68',2,'reveal-overclassification','H2は五圧力の性質を教えるが枠組み名への対応が残る。true→falseとdesign同期。'),('r04a-q67',2,'reveal-overclassification','H2は調査の具体例とセグメンテーションの除外だけで調査名との対応が残る。true→falseとdesign同期。'),('r03h-q72',2,'reveal-overclassification','H2は融合の仕組み/電子政府との差を教えるが固有名称が未提示。true→falseとdesign同期。'),('r03a-q68',1,'beginner-definition','keepのH1は比較箇所だけで、スケールメリット=規模拡大による単価低下、シナジー=共同生産による別々の総費用からの削減という判断基準を教えていない。定義をヒント側に補う。'),('r03a-q68',2,'reveal-overclassification','現H2は数値比較を教えるが両概念への判定が残るためfalse。H1修正後は累積で再評価。比較/計算を残す表現へ必要に応じて調整する。'),('r04a-q66',1,'reveal-overclassification','H1は完成/遂行の一般基準を教えるが工程の開始終了への適用が残る。true→falseとdesign同期。'),('r04a-q66',None,'phase-scope-precision','choiceReasons[1]がシステムテストを請負範囲外と一律に読む文面。第二版は外部設計/システムテストが準委任又は請負（同組r07h原本表でも確認）。イの不適切理由は要件定義・受入導入支援を含むことに置き、explanationにも第二版/当問の範囲を明記して契約一般の固定分類へ広げない。'),('r03a-q74',1,'definition-reveal','用語→説明問題。H1はSLを「指導を受ける相手の状況」と対応させウの特徴を実質渡す。他肢は個人資質/二機能/リーダーと統制状況なのでtrueとdesign同期。')]
issues=[dict(id=f'B36-{n:02}',questionId=q,stage=st,type=t,severity='required',finding=f) for n,(q,st,t,f) in enumerate(issue_specs,1)]
qs=[]
for idx,(q,e) in enumerate(zip(c,d)):
 inv=inventory[q['id']]; hashes={path:sha((root/path).read_bytes()) for path in q['sourceHashes']};assert hashes==q['sourceHashes']==inv['sourceHashes']
 src=next(s for s in sources if s['year']==q['year'] and s['season']==q['season'] and s['kind']=='answer');pdf=cache/src['filename'];assert sha(pdf.read_bytes())==src['sha256'];assert src['url']==q['answerUrl']
 related=[i['id'] for i in issues if i['questionId']==q['id']]; ans='アイウエ'[q['answer']]
 qs.append(dict(id=q['id'],status='changes-requested' if related else 'content-reviewed-no-issues',decision=e['decision'],beforeEnvelopeSHA256=canon(e),beforeLessonSHA256=canon(e['lesson']),sourceImageActuallyOpened=q['sourceImages'][0],sourceImageSHA256=hashes[q['sourceImages'][0]],sourceHashes=hashes,questionUrl=q['questionUrl'],officialAnswerPDF=dict(path=str(pdf),sha256=src['sha256'],url=src['url'],existingCacheUsed=True,verification=f'問{q["number"]} 正解{ans}を'+('PDFスキャン由来の既存PNGをview_imageで実表示して実読。' if 'r04h' in q['id'] else '公式PDF実バイトからpdftotext -layout再抽出し実読。'),renderedImageActuallyOpened=str(cache/'batch35-r04h-answer.png') if 'r04h' in q['id'] else None),officialAnswer=ans,independentResult=notes[idx],choiceReasonsReview='原本全4肢と独立解答の分岐点を照合。工程範囲の記述に関する指摘以外に理由不整合なし。' if q['id']=='r04a-q66' else '原本全4肢の意味・順序を独立解答と照合し、4理由の分岐点を確認。',lessonReview='summary/explanation/takeaway/checkedAgainstとdesign全読。指摘以外に事実・数値・単位・時点の不備なし。',hintReview=[dict(stage=j+1,currentRevealsAnswer=h['revealsAnswer'],independentlyAssessedRevealsAnswer=assessed[idx][j],rationale=rationales[idx][j],designRead=True) for j,h in enumerate(e['lesson']['hints'])],checks=dict(source=True,answer=True,choices=True,hints=True,explanation=q['id']!='r04a-q66',design=True,revealFlags=all(h['revealsAnswer']==a for h,a in zip(e['lesson']['hints'],assessed[idx])),calculation=True if q['id'] in ['r04a-q72','r06a-q73','r03a-q68'] else 'not-applicable'),issues=related))
report=dict(reviewer='Codex /root/ap_batch36_review',initialAuthorHead='16990d426a8fb3aaaea0d5c07764ea3eab1bb551',frozenBeforeSnapshot=dict(path=str((p/'review/initial-drafts.json').relative_to(root)),sha256=sha((p/'review/initial-drafts.json').read_bytes())),counts=dict(questions=20,originalImagesActuallyOpened=20,choiceReasons=80,hints=60,officialAnswerPDFsRead=8,officialAnswerPDFsTextRead=7,officialAnswerPDFsImageRead=1,requiredIssues=len(issues),questionsWithIssues=len(set(i['questionId'] for i in issues)),questionsWithoutIssues=20-len(set(i['questionId'] for i in issues))),issues=issues,kind='initial-independent-content-review',status='changes-requested',checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),method='指定resume指示/AGENTS/共通3規約/組README/assignment/context/drafts/inventoryの対象項目を読了。原本20画像をview_imageで実表示し独立解答、keepを含む全20lesson/design・80肢理由・累積60ヒントを実読。公式8PDFの実SHAとdata/sources.jsonのURL/実SHAを照合。7PDFは再pdftotext、R4春スキャンは既存PNG実表示。初学者効果測定・アプリ検証は未実施。drafts/reviews/凍結は無変更。',questions=qs)
out=p/'review/independent-review.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('REPORT_SHA256',sha(out.read_bytes()));print('DRAFTS_SHA256',sha((p/'drafts.json').read_bytes()));print('SNAPSHOT_SHA256',sha((p/'review/initial-drafts.json').read_bytes()));print(json.dumps(report['counts'],ensure_ascii=False))
