import json,hashlib,datetime
from pathlib import Path
p=Path('work/ap/objective-quality/batches/batch-37'); ds=json.loads((p/'drafts.json').read_text()); cs=json.loads((p/'context.json').read_text()); inv={x['id']:x for x in json.load(open('work/ap/objective-quality/inventory.json'))}; sources=json.load(open('data/sources.json'))
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(o):return sha(json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
issues=[
 {'id':'B37-01','questionId':'r05a-q76','stage':2,'type':'overstated-reveal','severity':'required','finding':'H2は降順の棒と累積割合という構成を教えるが、原本の四肢は図法名のみ。パレート図という名称との対応付けは残り、他三図の名称と用途も全排除していない。説明→用語問題なのでH2とdesignをfalseへ。正答名を出すH3はtrue維持。'},
 {'id':'B37-02','questionId':'r04h-q77','stage':2,'type':'overstated-reveal','severity':'required','finding':'H2は原始的帰属の意味と創作側に発生する原則を教える。A/Bのどちらが本件の創作側かという条件適用は残り、B社という帰属先自体はH3で初めて明示する。H1の役割整理と合わせて解けることと開示は別。H2とdesignをfalseへ、H3はtrue維持。'}]
results=[
'要因別件数の降順棒と累積比率で重点を示すのはパレート図、イ。他は原因の系統化・行列関係・因果関係。',
'フィードラーは個人のスタイルと状況の適合、エ。アは特性、イはPM、ウは成熟度を使うSL。',
'観測で事前分布を事後分布へ更新するベイズ統計はイ。アは貿易統計、ウは記述統計、エの公開データ限定は不適切。',
'行ごとの最小はA10/B5/C5/D−10円。その最大10円を持つA＝ア。低成長列だけを取らない。',
'BCMのレジリエンスは対応・復元能力でエ。強みはコアコンピタンス、事前計画はBCP、全リスク回避は不適切。',
'製品・地域単位の利益責任は事業部制ウ。期間限定はプロジェクト、機能別は職能別、外部提携はネットワーク型。',
'利益差600−(−200)=800万円、売上差2000万円。限界利益率0.4、変動費率0.6、8000×0.6=4800万円でウ。固定費3000万円でも両条件成立。',
'中立に発言促進と論点整理を行うウ。専門家・経営層誘導・事務局に限定する他肢は異なる。',
'利益は(単価−600)×需要−1000000円。各価格で3100/4100/4700/4900万円、最大は1600円のエ。',
'今年度利益100000千円。次年度固定費157500、単価190、単位変動費100千円。n≥257500/90=2861.111…より2862台エ。2861台では不足。',
'Aはb1時40>30、b2時50>25でa1。Bはa1時30>20、a2時25>10でb2。単独変更で得をしないa1,b2＝イ。',
'特段の権利取決めなくBがプログラム作成。要求仕様提示や費用負担だけで発注者へ移転せず、原始帰属はB社エ。契約譲渡とは区別。',
'30×0.250=7.5万円/年、2年累計15万円、簿価15万円。廃棄支出2万円を加算し17万円エ。残存価額0と途中簿価を区別。',
'変動費200+100=300百万円、限界利益率1−300/500=0.4。固定費100+80=180、180/0.4=450百万円ウ。総利益は費用に足さない。',
'右からa追加max(0.3×200+0.7×100−60,50)=70、a全体0.4×70+0.6×120−30=70。b追加max(0.4×150+0.6×100−40,70)=80、b全体0.3×80+0.7×140−40=82億円。b82＝ウ。',
'甲(30−18)/10=1.2、乙(25−14)/8=1.375千円/時間。乙1250個で限界利益13750、固定費10000控除後3750千円イ。',
'A12000/8=1500、B15000/12=1250円/時間。A1875個で限界利益22500000円、固定費15000000を引き7500000円イ。',
'経営理念を実現する経営戦略から事業戦略へ具体化するウ。アは抽象/具体、イは期間、エは全社/事業の方向を逆にしている。',
'売上S百万円に対し利益0.4S−150=50。S=200/0.4=500百万円エ。各誤答の利益は−16.8/20/33.2。',
'移動平均の期間増大は直近の重みと反応を小さくする。指数平滑F次=α実績+(1−α)F前、α大なら直近重視。ア/イ/ウが逆でエ。精度向上は条件付き。']
rationales=[
['順位付けという目的の整理で図法名は未提示','図の構成から名称への対応付けが残り、全誤答排除もない','パレート図という正答名を明示'],
['特性/PMを整理してもSLとフィードラーの区別が残る','フィードラーの説明がエと実質同一','H2の開示に加えSLとの相違を教える'],
['集計との区別という観点で確率更新の定義は未提示','事前/事後と迷惑メールというイの説明を渡す','イと正答概念を明示'],
['行全体を見る観点を教え、最小値選択が残る','各行最小の計算が残る。最大を選ぶ定義はH3で完成する','最小値一覧とAを明示'],
['能力/文書の比較軸で、レジリエンスの意味はH2に残る','対応・回復というエの説明そのもの','エの対応・復元という正答説明を渡す'],
['組織分類の軸を示すが名称との対応は残る','利益責任を持つ事業単位というウの説明を渡す','製品/地域と利益責任を事業部制に結び付ける'],
['損失の負符号を教え、増分計算は残る','増分比の式を教え、計算と変動費率への換算は残る','和が1という関係を追加し、率と費用の計算が残る'],
['役割の分類と誘導/支援の比較でファシリテータとの対応は残る','中立な発言促進・整理というウの説明を渡す','H2の開示に加え四役割を整理'],
['単位と固定/変動の引く位置に注意を向ける','利益式と最初の行の代入を教え、全行計算比較が残る','全利益値と1600円を明示'],
['単位と費用の粒度を整理し、利益計算は残る','新価格/固定費への変更を教え、必要台数の式と計算は残る','必要台数の除算と整数切上げが残る'],
['各社の数値と比較方向を教え、最適反応比較が残る','比較対象の数値を教えるが大小比較と均衡特定は残る','a1,b2を明示して組合せを確定'],
['発注/作成と契約条件を整理し、帰属規則は未提示','一般則を本件の創作主体へ適用して帰属先を判断する作業が残る','B社という帰属先を明示'],
['定額法の率の適用と2年分計算が残る','簿価と支出の加算規則を教え、計算は残る','途中式を渡すが最終17万円の演算は残る'],
['費用区分と中間利益の違いを教え、合計計算は残る','変動費率の式を教え、比率計算と損益分岐点計算は残る','必要式を渡すが最終450の計算は残る'],
['○/□と費用控除を教え、全期待値計算は残る','右からの加重平均と最大選択を教え、条件適用は残る','追加投資の比較式を渡すが枝評価・初期期待値と費用計算は残る'],
['限界利益の定義を教え、製品別計算は残る','時間当たり式を教え、比較と年間利益計算は残る','乙の優位は明示するが問う営業利益は生産数計算と固定費控除が残る'],
['時間制約と個数限界利益の違いを教え、時間比の計算が残る','時間比と優先基準を教え、数値比較と年間利益計算は残る','A優位を教えても問う利益の生産数計算・固定費控除が残る'],
['全社/個別事業という比較軸で方向判断は残る','理念最上位の与件に加え全社から事業へという正答ウの関係を教える','ウを明示'],
['固定費/変動費率の意味を教え、利益式と計算は残る','40%から固定費を引く仕組みを教え、目標売上計算が残る','式は示すが変形と除算が残る'],
['ア/イは除けるが指数平滑のウ/エの比較が残る','H1でア/イを除外、αの重み説明でウも除外し、累積でエのみ残る','H2までの全誤答排除を含みtrue。条件付きの直近重視も追加']]
questions=[]
for i,(q,d) in enumerate(zip(cs,ds)):
 answer='アイウエ'[q['answer']]; pdf=Path('/workspace/scratch/ap-a-quality-review/sources')/q['answerUrl'].split('/')[-1]; ph=sha(pdf.read_bytes()); meta=next(s for s in sources if s['url']==q['answerUrl']); assert ph==meta['sha256']; ownissues=[x for x in issues if x['questionId']==q['id']]; flags=[h['revealsAnswer'] for h in d['lesson']['hints']]; assessed=flags.copy()
 if q['id'] in ['r05a-q76','r04h-q77']:assessed[1]=False
 calculations=i in [3,6,8,9,10,12,13,14,15,16,18]
 questions.append({'id':q['id'],'status':'changes-requested' if ownissues else 'content-reviewed-no-issues','beforeEnvelopeSHA256':canon(d),'beforeLessonSHA256':canon(d['lesson']),'sourceImageActuallyOpened':q['sourceImages'][0],'sourceImageSHA256':sha(Path(q['sourceImages'][0]).read_bytes()),'sourceHashes':q['sourceHashes'],'questionUrl':q['questionUrl'],'officialAnswerPDF':{'path':str(pdf),'sha256':ph,'url':q['answerUrl'],'existingCacheUsed':True,'verification':f'問{q["number"]} 正解{answer}を'+('PDF実バイトからpdftoppmで再描画した画像で実読。' if q['id'].startswith('r04h') else 'pdftotext -layout再抽出テキストで実読。')+'data/sources.jsonのURL/SHAと一致。','renderedImageActuallyOpened':str(p/'review/official-r04h-answer.png') if q['id'].startswith('r04h') else None},'officialAnswer':answer,'independentResult':results[i],'choiceReasonsReview':'全4肢と理由を原本に照合し、独立解答に記した各肢の分岐点と一致。','lessonReview':'summary/explanation/takeaway/checkedAgainstとdesign全文を確認。以下の開示フラグ指摘以外に教材内容の要修正なし。','hintReview':[{'stage':j+1,'currentRevealsAnswer':flags[j],'independentlyAssessedRevealsAnswer':assessed[j],'rationale':rationales[i][j],'designRead':True} for j in range(3)],'checks':{'source':True,'answer':True,'choices':True,'hints':True,'explanation':True,'design':True,'revealFlags':not ownissues,'calculation':True if calculations else 'not-applicable'},'issues':ownissues})
report={'reviewer':'Codex /root/ap_batch37_review','initialAuthorHead':'1c226d7384746b477f69d69f0b508064dd3d13d5','frozenBeforeSnapshot':{'path':str(p/'review/initial-drafts.json'),'sha256':sha((p/'review/initial-drafts.json').read_bytes())},'counts':{'questions':20,'originalImagesActuallyOpened':20,'supplementaryImagesActuallyOpened':2,'choiceReasons':80,'hints':60,'officialAnswerPDFsRead':9,'officialAnswerPDFsTextRead':8,'officialAnswerPDFsImageRead':1,'requiredIssues':2},'issues':issues,'kind':'initial-independent-content-review','status':'changes-requested','checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'指定resume全文とAGENTS/3規約/README/assignment/context/drafts/inventoryを先読。全20原本をview_imageで実表示し独立解答。keep含む20教材・80肢理由・累積60ヒント・design全読。公式PDF cacheの実SHA/URLをdata/sourcesと照合し8PDFをテキスト実読、r04hは実PDFから再描画して実表示。補助2画像も実表示。構造/アプリ試験と初学者試用は未実施。drafts/reviews/initial snapshotは未変更。','consideredAndResolved':[{'questionId':'r03a-q75','finding':'H2単独では最小値から最大を選ぶ定義が未提示だが、H3で最大を選ぶ手順と最終値を新情報として教えている。3段全体では定義不足にならず、不要な改稿は要求しない。'},{'questionId':'r07h-q74','finding':'H2は一般式の支援だけとみなさず、H1によるア/イ排除と合わせ全誤答が消えるためtrue妥当。'}],'questions':questions}
out=p/'review/independent-review.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n'); print('report',sha(out.read_bytes()));print('snapshot',report['frozenBeforeSnapshot']['sha256']);print('drafts',sha((p/'drafts.json').read_bytes()));print('reviews',sha((p/'reviews.json').read_bytes()));print('questions',[(q['id'],q['officialAnswer'],q['status']) for q in questions])
