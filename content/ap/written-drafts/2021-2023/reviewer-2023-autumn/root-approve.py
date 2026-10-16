"""Seal only root's manually checked cases after original/crop/answer comparison."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,sys,fitz
from PIL import Image
ROOT=Path(__file__).resolve().parents[5];BASE=ROOT/'content/ap/written-drafts/2021-2023';OUT=BASE/'reviewer-2023-autumn'
canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
methods={int(k):v for k,v in json.loads((OUT/'root-reviewed-methods.json').read_text()).items()}
for n in map(int,sys.argv[1:]):
 assert n in methods,'No completed manual review notes for this question'
 cid=f'ap-r05a-pm{n}';p=BASE/'author-2023-autumn'/f'{cid}.json';c=json.loads(p.read_text());ec=json.loads((p.parent/'evidence.json').read_text())['cases'][cid]
 finding=json.loads((OUT/'root-independent-findings.json').read_text())['cases'][cid];assert finding['beforeAuthorDraft'] and not finding['openQuestions']
 pixel=[];pdf=fitz.open(BASE/'sources/2023r05a_ap_pm_qs.pdf')
 for path in c['sourceImages']:
  page=int(re.search(r'question-p(\d+)',path).group(1));pix=pdf[page-1].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False);expected=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);actual=Image.open(ROOT/path).convert('RGB');assert actual.size==expected.size and actual.tobytes()==expected.tobytes();pixel.append({'path':path,'pdfPage':page,'officialRenderPixelEqual':True})
 for crop in ec['crops']:
  src=Image.open(ROOT/crop['source']);actual=Image.open(ROOT/crop['output']);expected=src.crop(crop['box']);assert actual.size==expected.size and actual.mode==expected.mode and actual.tobytes()==expected.tobytes()
 for f in c['bodyFigures']:assert c['body'].count(f['anchor'])==1
 c['status']='reviewed';c['authoringStatus']='independently-reviewed'
 assets=c['sourceImages']+[f['image'] for f in c['bodyFigures']]+[ec['answerImageViewed'],ec['commentaryImageViewed']]
 if n in [9,10,11]:assets += [str(p.relative_to(ROOT)) for p in sorted(OUT.glob(f'root-q{n}-*source.png'))]
 if n==8:assets.append(str((OUT/'root-q8-underline-source.png').relative_to(ROOT)))
 if n==7:assets += [str((OUT/(name+'.png')).relative_to(ROOT)) for name in ['root-q7-rounding-source','root-q7-q2-source']]
 r={'caseId':cid,'version':c['version'],'status':'approved','author':c['author'],'reviewer':'/root','reviewedAt':datetime.now(timezone.utc).isoformat(),'canonicalCaseSHA256':hashlib.sha256(canonical(c)).hexdigest(),'sourceEvidence':'content/ap/written-drafts/2021-2023/sources/sources.json','sourceHashes':{f'content/ap/written-drafts/2021-2023/sources/2023r05a_ap_pm_{kind}.pdf':sha(f'content/ap/written-drafts/2021-2023/sources/2023r05a_ap_pm_{kind}.pdf') for kind in ['qs','ans','cmnt']},'assetHashes':{path:sha(path) for path in assets},'method':methods[n],'answerCheck':'保存したroot-independent-findings.jsonの実際の原問からの判断/検算と公式例を照合。共有ページによる先行閲覧や独立解答の誤りも同所見へ区別して記録。','gradingCheck':'説明/図示/順不同は自己評価、登録短答のみ例一致判定。図の形/向き/下線を単語だけでauto正解にしない。字数原本無指定2000は入力上限。公式部分点の採点基準とは扱わない。','pixelChecks':pixel,'cropChecks':ec['crops'],'independentEvidence':['content/ap/written-drafts/2021-2023/reviewer-2023-autumn/root-independent-findings.json',*(['content/ap/written-drafts/2021-2023/reviewer-2023-autumn/root-sql-check.py'] if n==6 else ['content/ap/written-drafts/2021-2023/reviewer-2023-autumn/root-pwm-echo-check.py'] if n==7 else ['content/ap/written-drafts/2021-2023/reviewer-2023-autumn/root-thread-check.py'] if n==8 else [])],'findings':([{'issue':'図1右端の超音波センサー文字clip','resolution':'作者が右端540から558へ拡張、rootが最終cropを実表示し全ラベル/隣図非混入を再確認','status':'resolved'},{'issue':'root先行解答の丸め/距離基準誤読','resolution':'独立所見に元の誤答を保持し原本拡大/公式例と再検算、作者側は当初から正しく修正不要','status':'resolved'}] if n==7 else [{'issue':'下線③終端がしたまで拡張されていた','resolution':'原本元画素拡大から追加までと確認し作者が訂正。rootが原本と最終bodyを再照合。','status':'resolved'}] if n==8 else [])}
 (OUT/f'approved-case-{cid}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');(OUT/f'review-{cid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('APPROVED by actual root reviewer:',cid,r['canonicalCaseSHA256'])
