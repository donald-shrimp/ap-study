"""Reviewer calculations, constants independently read from official r04a images."""
from fractions import Fraction as F
from itertools import product,permutations
from collections import Counter
from pathlib import Path
import math,json,ipaddress
out=[]
def check(n,result,expected,detail=''):
 assert result==expected,(n,result,expected)
 out.append({'id':f'r04a-q{n}','result':result,'expected':expected,'passed':True,'detail':detail})
check(1,[(n,((2**n-1)**2).bit_length()) for n in range(1,9)],[(1,1)]+[(n,2*n) for n in range(2,9)],'n=1例外を含む最大値のbit_length')
rows=[(0,0),(0,1),(1,1),(1,0)];cols=rows;grid=[[1,0,0,1],[0,1,1,0],[0,1,1,0],[0,0,0,0]]
mism=[0,0,0,0];witness=[]
for ri,(a,b) in enumerate(rows):
 for ci,(c,d) in enumerate(cols):
  opts=[(a and b and not c and d) or (not b and not d),(not a and not b and not c and not d)or(b and d),(a and b and d)or(not b and not d),(not a and not b and not d)or(b and d)]
  for k,v in enumerate(opts):mism[k]+=int(bool(v)!=bool(grid[ri][ci]))
  if bool(opts[2])!=bool(grid[ri][ci]):witness.append([a,b,c,d,grid[ri][ci],int(bool(opts[2]))])
check(2,[i for i,z in enumerate(mism) if z==0],[3],f'全16入力、各選択肢不一致数{mism}、ウ不一致{witness}')
check(3,str(F(90,100)*F(89,99)*F(88,98)),'178/245','無復元の3回積')
check(5,all((a%n==b%n)==((a-b)%n==0) for n in range(1,21) for a in range(1,41) for b in range(1,41)),True,'n=1..20,a,b=1..40の32000組')
def sort(xs):
 a=list(xs);n=len(a)
 for i in range(n-1):
  for j in range(n-1,i,-1):
   if a[j]<a[j-1]:w=a[j];a[j]=a[j-1];a[j-1]=w
 return a
check(6,all(sort(p)==list(range(5)) for p in permutations(range(5))),True,'図のi=1..n−1,j=n..i+1を0基点へ変換し全120順列')
check(10,str(F(95,100)+F(5,100)*F(6,10)),'49/50','0.98、L1ミス分にL2率を掛ける')
check(14,F(15,10)*F(9)/(F(15,10)*F(9)+F(15,10)*F(1))==F(9,10),True,'例MTBF9,MTTR1で倍率相殺を確認')
check(15,[100*10**6//10**6,8*10**7//(2*10**5*8)],[100,50],'命令/件とbit/件で件/秒へ')
free=[0,0,0];work=[[],[],[]];trace=[]
for dur in [4,6,3,2,5,3,4,3,1]:
 k=min(range(3),key=lambda k:(free[k],k));start=free[k];free[k]+=dur;work[k].append(dur);trace.append([chr(65+k),start,dur,free[k]])
check(19,sum(work[2]),11,str(trace))
truth=[]
for x,y in product([0,1],repeat=2):
 u=not((not(x and y))and(not((not x)and(not y))));truth.append(int(u))
check(23,truth,[1,0,0,1],'00,01,10,11を3 NANDの図から評価')
need=F(8000)*F(12,10)**3
check(24,[int(need),min(n for n in range(1,8) if 26**n>=need)],[13824,3],'26²=676,26³=17576')
prices=[1000,2500,1500,2500,2000,3000,2500,2500,2500,1300];costs=[800,2300,1400,1600,1600,2800,2200,2000,2000,1000];supplier=['S1','S2','S2','S1','S1','S3','S3','S4','S5','S6'];margin=[a-b for a,b in zip(prices,costs)];avg=F(sum(margin),10);codes=sorted(set(s for s,m in zip(supplier,margin) if m>avg))
check(28,[int(avg),codes],[360,['S1','S4','S5']],str(margin))
net=ipaddress.ip_network('192.168.16.40/29');check(33,[str(net.netmask),len(list(net.hosts())),str(net.broadcast_address)],['255.255.255.248',6,'192.168.16.47'])
branches=set();commands=set();trace=[]
for v,w,x,y,z in [(0,0,0,0,0),(1,1,1,1,1)]:
 c=[]
 branches.add(('v',v==0))
 if v==0:c.append(1)
 c1=w==0 and x==0;branches.add(('wx0',c1))
 if c1:c.append(2)
 else:
  c2=w!=0 and x!=0;branches.add(('wxNZ',c2))
  if c2:c.append(3)
 c3=y==0 and z==0;branches.add(('yz0',c3))
 if c3:c.append(4)
 else:
  c4=y!=0 and z!=0;branches.add(('yzNZ',c4))
  if c4:c.append(5)
 commands.update(c);trace.append(c)
check(48,[len(commands),len(branches)],[5,8],f'命令経路{trace},全10枝中8枝')
a_start=0;a_end=a_start+6;b_start=a_end-2;b_end=b_start+7;c_start=b_start+3;c_end=c_start+5
check(52,[a_end,b_start,b_end,c_start,c_end,max(a_end,b_end,c_end)],[6,4,11,7,12,12],'終了開始lead2・開始開始lag3')
old=F(6,2)+F(12,2+F(2,2))+F(12,2);new=F(6,3)+F(12,3+F(2,2))+F(12,3)
check(53,[int(old),int(new),int(old-new)],[13,9,4],'初級2人=上級1人、工程非重複')
weights=[5,1,4];scores=[[7,9,8],[8,10,5],[9,4,7],[9,7,6]];totals=[sum(w*s for w,s in zip(weights,row)) for row in scores];check(54,totals,[76,70,77,76])
shift_count=(2+4+2)*7;max_shifts=math.floor(40/7.5);staff=math.ceil(shift_count/max_shifts);assigned=Counter(i%12 for i in range(56));check(56,[shift_count,max_shifts,staff,max(assigned.values())],[56,5,12,5],'12人に56枠を順番に割当てる存在確認：各日8枠は異なる8人で各週最大37.5h')
npv=[sum(F(v)*F(20,21)**t for t,v in enumerate(row,1))-220 for row in [[40,80,120],[120,80,40],[80,80,80]]]+[F(0)]
check(64,max(range(4),key=lambda i:npv[i]),1,str([round(float(v),6) for v in npv]))
a_new=300-100;part_a_new=a_new*3-100;b_gross=a_new*2+part_a_new;b_net=b_gross-300;check(72,[a_new,part_a_new,b_gross,b_net],[200,500,900,600])
best=(-1,None)
for q in range(1001):
 o=(10000-10*q)//8;profit=(30-18)*q+(25-14)*o-10000
 if profit>best[0]:best=(profit,[q,o])
check(77,best,(3750,[0,1250]),'甲数量0..1000の全探索、余った時間に乙を最大製造')
# Fraction/tuple are intentionally converted to standard JSON values.
p=Path(__file__).parent
print(json.dumps({'passed':len(out),'failed':0,'ids':[x['id'] for x in out]},ensure_ascii=False))
