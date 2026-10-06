import json,itertools,ipaddress
from fractions import Fraction as F
from pathlib import Path
out=[]
def check(q,detail,result,expected):
 assert result==expected,(q,result,expected)
 out.append({'id':f'r04h-q{q}','detail':detail,'result':result,'expected':expected,'passed':True})
def fits(v):
 v=abs(v);e=0
 while v>=2:v/=2;e+=1
 while v<1:v*=2;e-=1
 return (v*128).denominator==1
small=F(3,16);tiny=F(1,16);large=F(32)
exact=[fits(small+tiny) and fits(small+tiny+large),fits(small-tiny) and fits(small-tiny+large),fits(large+small) and fits(large+small+tiny),fits(large-tiny) and fits(large-tiny+small)]
check(1,'正規化仮数×128が整数となるかを各中間値で検査',[bool(z) for z in exact],[True,False,False,False])
S=set(range(4));A={0,1};B={1,2};target=(S-A)&(S-B);cand=[(S-A)-B,((S-A)|(S-B))-(A&B),(S-A)|(S-B),S-(A&B)]
check(2,'Aだけ・共通・Bだけ・外側の4要素で集合演算',[c==target for c in cand],[True,False,False,False])
check(3,'(.40/.60)/(.25/.75)',str((F(40,100)/(1-F(40,100)))/(F(25,100)/(1-F(25,100)))),'2')
def parity(word):
 x1,x2,x3,p3,x4,p2,p1=map(int,word)
 return [x1^x3^x4^p1,x1^x2^x4^p2,x1^x2^x3^p3]
check(4,'受信1110011検査と四候補の検査',[parity(z) for z in ['1110011','0110011','1010011','1100011','1110111']],[[1,1,1],[0,0,0],[1,0,0],[0,1,0],[0,0,1]])
check(9,'ヒット.95/30+ミス.05、最も近い選択肢',min([.03,.08,.37,.95],key=lambda z:abs(z-(.95/30+.05))),.08)
check(11,'6台うち予備1、RAID5パリティ1、各8TB',(6-1-1)*8,32)
check(15,'独立2台でちょうど一方稼働',str(F(7,10)*F(4,10)+F(3,10)*F(6,10)),'23/50')
succ={'A':['B','C'],'B':['D','E'],'C':['E'],'D':['F'],'E':['F'],'F':[]};pred={j:[] for j in succ}
for j,js in succ.items():
 for k in js:pred[k].append(j)
first={j:js[0] for j,js in succ.items() if js};done=set();files=set();queue=['A'];running=[];peak=0;trace=[]
while queue or running:
 while queue and len(running)<2:
  j=queue.pop(0);running.append(j);files.add(j);peak=max(peak,50*len(files));trace.append({'event':'start '+j,'files':sorted(files),'MB':50*len(files)})
 ended=running;running=[]
 for j in ended:
  done.add(j)
  for k in list(files):
   if first.get(k)==j:files.remove(k)
  for k in succ[j]:
   if set(pred[k])<=done and k not in done and k not in queue:queue.append(k)
  trace.append({'event':'end '+j,'files':sorted(files),'MB':50*len(files)})
check(16,'各ジョブ同時間、2並行、初回後続だけ参照・終了時削除',peak,200);out[-1]['trace']=trace
ends={}
for slots in [1,2]:
 free=[0]*slots;completed=[]
 for arrive in [0,1,2,3]:
  k=min(range(slots),key=lambda k:free[k]);end=max(arrive,free[k])+4;free[k]=end;completed.append(end)
 ends[str(slots)]=completed
check(19,'到着0,1,2,3、各4秒、空き枠にFIFO投入',max(ends['1'])-max(ends['2']),7);out[-1]['completions']=ends
slope=F(8-4,9-5);y=4+(7-5)*slope
check(21,'始点(5,4)、終点(9,8)、x7のyと640画素/16bitの番地',int((640*y+7)*(16/8)),7694)
net=ipaddress.ip_network('192.168.30.32/28');check(34,'IPv4 /28 hosts列挙',len(list(net.hosts())),14)
def branch(a,b):
 c=1;one=a>0 and b==0;c=a*c if one else 2;two=a>0 and c==1
 return [one,two]
cases=[[(0,0),(1,1)],[(1,0),(1,1)],[(0,0),(1,1),(1,0)],[(0,0),(0,1),(1,0)]]
coverage=[all({branch(*t)[j] for t in cs}=={False,True} for j in [0,1]) for cs in cases]
check(47,'初期C1、第一YesでA×C、Noで2、第二A>0かつC1',coverage,[False,True,True,True]);check(47,'分岐網羅する最少候補の件数',min(len(cases[i]) for i,v in enumerate(coverage) if v),2)
check(51,'EV40/AC60が継続、BAC100',int(F(100)/(F(40)/60)),150)
finish={'requirements':30};finish['design']=finish['requirements']+20;finish['manufacture']=finish['design']+25;finish['test']=finish['manufacture']+15;finish['manual']=finish['design']+20;finish['training']=max(finish['test'],finish['manual'])+10
check(53,'表の先行関係を独立に前進計算',finish['training'],100);out[-1]['finishDays']=finish
check(55,'RPO12hを満たす選択肢3,9,12,15の最大間隔',max(z for z in [3,9,12,15] if z<=12),12)
m=[[0,2,1,2],[1,0,1,2],[3,2,0,2],[4,3,2,0]];paths=[(''.join('abcd'[j] for j in order),sum(m[a][b] for a,b in zip(order,order[1:]))) for order in itertools.permutations(range(4))]
check(73,'原本FROM行TO列の方向付き表から全24順序',min(v for _,v in paths),4);out[-1]['all24']=paths
prices=[1000,1200,1400,1600];demand=[80000,70000,60000,50000];profits=[(p-600)*n-1000000 for p,n in zip(prices,demand)]
check(76,'固定100万円、変動600円、原本価格と需要の4行',profits,[31000000,41000000,47000000,49000000]);check(76,'最大利益の価格',prices[profits.index(max(profits))],1600)
print(json.dumps({'count':len(out),'questions':sorted(set(r['id'] for r in out)),'allPassed':True},ensure_ascii=False))
