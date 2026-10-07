"""Verify the first draft batch without approval or modifying any record.

This replays the author's checks. It is not an independent lesson review.
"""
import json,hashlib,re,itertools,copy,importlib.util
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];path=root/'content/ap/diagnostic-drafts/20261008-first-round.json';batch=json.loads(path.read_text());qs={q['topicId']:q for q in batch['questions']};config=json.loads((root/'content/ap/qualification.json').read_text());raw=json.loads((root/'data/questions.json').read_text());parents={q['id']:q for q in raw}
digest=lambda obj:hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
spec=importlib.util.spec_from_file_location('draft_builder',root/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
generic=dict(config);generic.pop('adapter',None)
# Shape validation uses an in-memory copy only. No review or publication state is changed.
shape=[builder.normalize({**q,'enrichment':'reviewed'},generic) for q in qs.values()];builder.validate_questions(shape,generic,root,diagnostic=True)
assert len(qs)==17 and set(qs)=={t['id'] for t in config['topics']}
assert len({q['id'] for q in qs.values()})==17 and len({q['parentQuestionId'] for q in qs.values()})==17
active=json.loads((root/'content/ap/diagnostic-questions.json').read_text())
assert all(q['enrichment']=='draft' and q['diagnosticOnly'] is True and len(q['choices'])==4 and len(q['choiceReasons'])==4 and all(q['choiceReasons']) and q['hints']==[] for q in qs.values())
for q in qs.values():
 assert q['stem'] and q['explanation'] and q['adaptation'] and q['correctChoiceId'] in [c['id'] for c in q['choices']]
 assert parents[q['parentQuestionId']]['topic']==next(t['name'] for t in config['topics'] if t['id']==q['topicId'])
for item in batch['sourceChecks']:
 for image in item['sourceImages']:assert hashlib.sha256((root/image['path']).read_bytes()).hexdigest()==image['sha256']
proofs=[]
def check(topic,answer_indexes,result,method):
 q=qs[topic];assert len(answer_indexes)==1,(topic,answer_indexes);assert q['choices'][answer_indexes[0]]['id']==q['correctChoiceId'],topic
 proofs.append({'questionId':q['id'],'draftSha256':digest(q),'method':method,'result':result,'uniqueChoiceIndex':answer_indexes[0],'status':'author-self-check-only'})
def num(text):return int(text.replace(',',''))
# Evaluate both R values; no answer index is used to choose a result.
q=qs['theory'];assert 'Pは真、Qは偽' in q['stem'];P,Q=True,False;imp=lambda a,b:not a or b
outputs=[[imp(P,Q) and R,P and imp(Q,R),imp(Q,P) and R,imp(R,Q)] for R in [False,True]]
check('theory',[i for i in range(4) if all(row[i] for row in outputs)],outputs,'Rを偽・真の両方に変えて4式を真理値評価。')
# Compare the composed circuit with independently evaluated named gates.
q=qs['logic'];assert 'C=NAND(A,B)' in q['stem'] and 'Y=NAND(C,C)' in q['stem'];inputs=list(itertools.product([False,True],repeat=2));out=[not ((not(a and b)) and (not(a and b))) for a,b in inputs]
gates={'AND':lambda a,b:a and b,'OR':lambda a,b:a or b,'XOR':lambda a,b:a!=b,'NOR':lambda a,b:not(a or b)}
check('logic',[i for i,c in enumerate(q['choices']) if [gates[c['text']](a,b) for a,b in inputs]==out],out,'全4入力を列挙し、2段NANDの出力と各ゲートの真理値表を比較。')
q=qs['algorithm'];assert 'n=0なら0' in q['stem'] and 'n+g(n−1)' in q['stem'];n=int(re.search(r'g\((\d+)\)が',q['stem'])[1]);result=n*(n+1)//2
check('algorithm',[i for i,c in enumerate(q['choices']) if num(c['text'])==result],result,'加算再帰の展開とは別に、1からnまでの等差数列の和n(n+1)/2で計算。')
q=qs['architecture'];periodA,cpiA,periodB,cpiB=map(F,re.findall(r'は([\d.]+)(?:ナノ秒|である|。)',q['stem']));ratio=periodA*cpiA/(periodB*cpiB)
check('architecture',[i for i,c in enumerate(q['choices']) if F(c['text'].replace('倍',''))==ratio],str(ratio),'問題文の周期とCPIを抽出し、命令数を共通の1として有理数で実行時間比を計算。')
q=qs['hardware'];zero=int(re.search(r'入力0の出力は(\d+)ミリV',q['stem'])[1]);step=int(re.search(r'出力は(\d+)ミリV増える',q['stem'])[1]);code=int(re.search(r'16進数([0-9A-F]+)',q['stem'])[1],16);assert 0<=code<=255;voltage=zero+sum(step for _ in range(code))
check('hardware',[i for i,c in enumerate(q['choices']) if num(c['text'])==voltage],{'code':code,'offset':zero,'steps':code,'voltageMilliV':voltage},'16進入力を整数へ変換し、入力0から1段階ずつ電圧を積算。範囲0〜255も確認。')
q=qs['network'];mtu=num(re.search(r'MTUは([\d,]+)',q['stem'])[1]);ip=int(re.search(r'IPヘッダーは(\d+)',q['stem'])[1]);tcp=int(re.search(r'TCPヘッダーはオプションを含め(\d+)',q['stem'])[1]);total=num(re.search(r'([\d,]+)バイトのアプリケーションデータ',q['stem'])[1]);capacity=mtu-ip-tcp;segments=[];remaining=total
while remaining:
 payload=min(capacity,remaining);segments.append(payload);remaining-=payload
assert len(segments)==2 and all(payload+ip+tcp<=mtu for payload in segments) and sum(segments)==total
check('network',[i for i,c in enumerate(q['choices']) if num(c['text'])==segments[1]],{'dataSegments':segments,'packetSizes':[n+ip+tcp for n in segments]},'残データを上限まで繰返し割り当てる分割処理で確認。IP全長と総データ保存を検証。')
q=qs['project'];bac,pv,ev,ac=map(num,re.findall(r'は([\d,]+)万円',q['stem']));cpi=F(ev,ac);spi=F(ev,pv);tcpi=F(bac-ev,bac-ac);assert bac>ac and bac>ev
observed=(cpi<1,spi<1,tcpi>cpi);claims=[(True,True,True),(False,True,False),(True,False,True),(True,True,False)]
check('project',[i for i,claim in enumerate(claims) if claim==observed],{'CPI':str(cpi),'SPI':str(spi),'TCPI':str(tcpi),'claimVector':observed},'EV/AC・EV/PV・残予算価値/残実コストを分数で算出し、4択の費用・進捗・必要効率の主張と照合。文言対応は作者の自己確認であり独立確認待ち。')
q=qs['business'];salesA,profitA,assetA,salesB,profitB,assetB=map(num,re.findall(r'は([\d,]+)百万円',q['stem']));turnA,turnB=F(salesA,assetA),F(salesB,assetB);marginA,marginB=F(profitA,assetA),F(profitB,assetB);observed=(turnA>turnB,marginA>marginB);claims=[(True,False),(True,True),(False,False),(False,True)]
check('business',[i for i,claim in enumerate(claims) if claim==observed],{'turnoverA':str(turnA),'turnoverB':str(turnB),'returnA':str(marginA),'returnB':str(marginB)},'問題文の6つの金額を抽出し、資産回転率・資産営業利益率の分数を計算。')
q=qs['business-strategy'];boundary,growth=map(F,re.findall(r'(\d+)%',q['stem']));threshold=F(re.search(r'シェアが(\d+)以上',q['stem'])[1]);share=F(re.search(r'シェアは([\d.]+)',q['stem'])[1]);matrix={(True,True):'花形',(True,False):'問題児',(False,True):'金のなる木',(False,False):'負け犬'};name=matrix[growth>=boundary,share>=threshold]
check('business-strategy',[i for i,c in enumerate(q['choices']) if c['text']==name],{'growth':str(growth),'growthBoundary':str(boundary),'share':str(share),'shareBoundary':str(threshold),'classification':name},'明示した高低の境界を適用し、PPMの四象限へ対応付ける。四類型の用語対応は作者の自己確認であり独立確認待ち。')
q=qs['database'];fds=[({'社員番号'},{'氏名','部署番号'}),({'部署番号'},{'部署名'})]
assert '候補キーは社員番号だけ' in q['stem'] and '社員番号→氏名・部署番号、部署番号→部署名' in q['stem']
def closure(attrs):
 result=set(attrs)
 while True:
  old=set(result)
  for left,right in fds:
   if left<=result:result|=right
  if old==result:return result

def powerset(attrs):
 values=sorted(attrs)
 return [set(items) for n in range(len(values)+1) for items in itertools.combinations(values,n)]
def third_normal_form(attrs):
 superkeys=[a for a in powerset(attrs) if attrs<=closure(a)];keys=[a for a in superkeys if not any(b<a for b in superkeys)];prime=set().union(*keys)
 for left in powerset(attrs):
  for right in (closure(left)&attrs)-left:
   if not attrs<=closure(left) and right not in prime:return False
 return True
verdicts=[]
for c in q['choices']:
 relations=[set(s.split(',')) for s in re.findall(r'\(([^)]+)\)',c['text'])];assert len(relations)==2
 intersection=relations[0]&relations[1];lossless=any(r<=closure(intersection) for r in relations);normal=all(third_normal_form(r) for r in relations);verdicts.append({'lossless':lossless,'thirdNormalForm':normal})
check('database',[i for i,v in enumerate(verdicts) if v['lossless'] and v['thirdNormalForm']],verdicts,'候補キーと関数従属の閉包を全列挙。各関係の第3正規形と共通属性による無損失分解の条件を別々に判定。')
report={'format':'hitomon-draft-author-checks','version':1,'batchId':batch['batchId'],'author':batch['author'],'checkedAt':datetime.now(timezone.utc).isoformat(),'independentReview':False,'draftCount':len(qs),'structureCheck':'passed','originalImageHashes':'matched','activePoolContamination':'none','numericalAndLogicalChecks':proofs,'notice':'作成実行による自己検算のみ。公開用のdiagnostic-reviews.jsonへ転記して独立確認扱いにしない。','draftHashes':{q['id']:digest(q) for q in qs.values()}}
saved=json.loads((root/'content/ap/diagnostic-drafts/20261008-first-round-author-checks.json').read_text());assert saved['draftHashes']==report['draftHashes'], 'Draft changed: author check evidence no longer matches'
assert saved['independentReview'] is False
progress=json.loads((root/'content/ap/diagnostic-progress.json').read_text());pending={item['questionId'] for item in progress['items'] if item['status']=='awaiting-independent-review'}
assert not pending&{q['id'] for q in active}, 'Unreviewed draft reached active pool'
print('PASS 17 draft structures / 17 topics / 17 different parents / original image hashes / active-pool exclusion / 10 numerical, logic and normalization checks. Independent review NOT completed.')
