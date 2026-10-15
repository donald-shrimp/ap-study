import json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
BASE=Path('content/ap/written-drafts/two-exams')
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def approve(n,method,calculation='not-applicable',findings=None):
 folder='author-spring-2-6' if n<=6 else 'author-spring-7-11';cid=f'ap-r07h-pm{n}'
 c=json.loads((ROOT/BASE/folder/(cid+'.json')).read_text());c['status']='reviewed';c['authoringStatus']='independently-reviewed'
 for i in c['items']:
  for f in i['fields']:
   if f['type']!='singleChoice': assert all(len(a)<=f['maxLength'] for a in f['referenceAnswers'])
 assets=c['sourceImages']+[f['image'] for f in c.get('bodyFigures',[])]
 ans={2:1,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,11:6}[n];cmnt=1 if n<=4 else 2 if n<=8 else 3
 assets += [str(BASE/'sources'/f'r07h-ans-p0{ans}.png'),str(BASE/'sources'/f'r07h-cmnt-p0{cmnt}.png')]
 r={'caseId':cid,'version':c['version'],'status':'approved','author':c['author'],'reviewer':'/root/written_review_spring','reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonicalCaseSHA256':hashlib.sha256(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'sourceEvidence':str(BASE/'sources/sources.json'),'independentFindings':str(BASE/'reviewer-spring/independent-findings.json'),'sourceHashes':{str(BASE/'sources'/f'2025r07h_ap_pm_{kind}.pdf'):digest(BASE/'sources'/f'2025r07h_ap_pm_{kind}.pdf') for kind in ['qs','ans','cmnt']},'assetHashes':{p:digest(Path(p)) for p in assets},'method':method,'answerCheck':'作者JSON・公式解答例・講評を読む前に原問画像全頁を実表示し解答方針をindependent-findings.jsonへ逐次保存。その後公式例・講評画像と全解答欄/解説/rubric/字数指定を照合。自己の独立案と公式例の違いも同ファイルに記録。','gradingCheck':'選択・登録短答は登録例との一致時だけ自動正解。未一致を機械的不正解にしない。説明文・順不同/全列挙/図の記述は自己評価。rubricは学習用であり公式の点数・部分点基準を推定しない。','calculationCheck':calculation,'findings':findings or []}
 out=ROOT/BASE/'reviewer-spring'
 (out/f'approved-case-{cid}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
 (out/f'review-{cid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(cid,r['canonicalCaseSHA256'])
if __name__=='__main__':
 approve(2,'原本p12〜16の全5頁、成長マトリクスcrop、公式解答例p1と講評p1をview_imageで実表示。全段落/図1の4象限/下線①〜⑤/空欄a〜d/設問8件8欄/全解答群記号順/15・5・35・30・15・10字と指定字句を照合。設問2(1)のb/cは公式順不同を統合自己評価欄に保持。','数値演算なし。全制限字数内の公式例文字数をPython lenで検査。',[{'kind':'reviewer-correction','detail':'独立解答の多角化分類を集成型としていたが、ナノテクノロジーの既存コア技術を活用する関連多角化なので集中型（イ）と原本・公式例から訂正。作者の教材は正しかった。'}])
 approve(3,'原本p18〜23全6頁と共通擬似言語規則p4〜5、図1〜3のcrop、公式解答例p2と講評p1をview_imageで実表示。表1の4ルール、図2の①〜⑫遷移/終端⑤⑥⑩、図3全配列、図4〜6クラス全変数/メソッド、表2全6関数、図7全45行の記述/方向配列/1始まり範囲/全8空欄を照合。2設問9欄と公式配列/式を照合。','同じ初期盤面から方向4通り・境界判定・FIFO・重複登録を独立Python BFSで実行し最小31手、seen181440状態を確認。図2②の配列は上の駒5を空白9へ移すので{{8,6,7},{2,9,4},{3,5,1}}。登録短答は厳密一致のみで同義SQL等の自動不正解なし。')
