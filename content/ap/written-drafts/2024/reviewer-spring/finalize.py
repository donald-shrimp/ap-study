import json,pathlib,hashlib,datetime
from PIL import Image
r=pathlib.Path(__file__).parent;base=r.parent
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
canonical=lambda o:json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
counts=[]
for no in range(1,12):
 source=base/('author-spring-1-6'if no<=6 else'author-spring-7-11')/f'ap-r06h-pm{no}.json'
 a=json.loads(source.read_text());p=r/f'approved-case-ap-r06h-pm{no}.json';c=json.loads(p.read_text());rv=r/f'review-ap-r06h-pm{no}.json';v=json.loads(rv.read_text())
 delta=[k for k in set(a)|set(c)if k not in ['status','authoringStatus']and a.get(k)!=c.get(k)]
 if delta:
  assert delta==['topicId'],delta
  c['topicId']=a['topicId'];v['metadataRecheck']='作者によるtopicId最終訂正をqualification.json登録分野と照合。本文/設問/全解答/解説/rubricは変更なしをオブジェクト比較確認。'
 c['status']='reviewed';c['authoringStatus']='independently-reviewed'
 v['canonicalCaseSHA256']=hashlib.sha256(canonical(c)).hexdigest();v['reviewedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();v['actualCounts']={'items':len(c['items']),'fields':sum(len(i['fields'])for i in c['items']),'sourceImages':len(c['sourceImages']),'bodyFigures':len(c.get('bodyFigures',[]))}
 if no==2:v['findings']=[{'issue':'表1/2のセル中の実改行がMarkdown行を途切れさせる。','resolution':'作者がセル内を一行化し原文の各箇条書き語句を保持。修正後全表セルと全文を再照合。'}]
 if no==4:v['answerCheck']=v['answerCheck'].replace('全6小問9欄','全6小問8欄')
 if no==6:v['answerCheck']=v['answerCheck'].replace('ER図全8entity','ER図全9entity').replace('8小問12欄','8小問11欄')
 if no==11:v['answerCheck']=v['answerCheck'].replace('全システムデータ6種','全システムデータ7種')
 if no in [3,4,5,7]:v['calculationEvidence']='content/ap/written-drafts/2024/reviewer-spring/calculations.json'
 if no==6:v['calculationEvidence']='content/ap/written-drafts/2024/reviewer-spring/sql-pm6.json'
 for path,digest in {**v['sourceHashes'],**v['assetHashes']}.items():assert sha(path)==digest,path
 for item in c['items']:
  for f in item['fields']:
   if f['type']!='singleChoice':assert 'maxLength'in f
 p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');rv.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');counts.append({'caseId':c['id'],**v['actualCounts'],'canonicalCaseSHA256':v['canonicalCaseSHA256']})
# Independently recompute all figure crops against original PNG pixels.
crops=json.loads((base/'author-spring-1-6/crops.json').read_text());second=json.loads((base/'author-spring-7-11/evidence.json').read_text())['cropEvidence'];records=[]
for path,x in crops.items():records.append({'image':path,'source':x['source'],'box':x['rectangle']})
records+=second
for x in records:
 expected=Image.open(x['source']).crop(x['box']);actual=Image.open(x['image']);assert expected.size==actual.size and expected.tobytes()==actual.tobytes(),x['image'];x['pixelIdentical']=True;x['sourceSHA256']=sha(x['source']);x['sha256']=sha(x['image'])
(r/'final-verification.json').write_text(json.dumps({'reviewer':'/root/review_2024_spring','checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':counts,'totalFields':sum(c['fields']for c in counts),'crops':records,'allSourceAndAssetHashesRecomputed':True},ensure_ascii=False,indent=2)+'\n')
f=r/'independent-findings.json';x=json.loads(f.read_text());x['cases']['ap-r06h-pm5']['officialComparison']='独立計算/選択/通信方向/全IPを公式例と照合。保守用PCは200.c.d.101。全欄整合。';f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');print('Final verification PASS',len(counts),'cases',sum(c['fields']for c in counts),'fields',len(records),'crops')
