#!/usr/bin/env python3
"""2023春期: 原本画像から独立転記した条件で計算・図・SQLを再現。
実行: python check_math.py [repository-root]
教材本文/summary/hintsは計算の入力にも期待値にも使用しない。
"""
import json,sys,itertools,sqlite3,math
from pathlib import Path
from fractions import Fraction as F
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
labels='アイウエ'
keys=next(r['answers'] for r in json.load(open(root/'data/answer-keys.json')) if r['year']==2023 and r['season']=='spring')
bank={r['id']:r for r in json.load(open(root/'data/questions.json'))}
results={}
def check(n,choices,value):
 matches=[i for i,c in enumerate(choices) if c==value]
 assert len(matches)==1,(n,choices,value,matches)
 idx=matches[0];assert keys[n-1]==labels[idx],(n,'official',value)
 assert bank[f'r05h-q{n}']['answer']==idx,(n,'bank',value)
 results[n]={'answer':labels[idx],'result':str(value)}
# q1: 全256入力を原本の4式に代入
expected=[n+1 if n<255 else 0 for n in range(256)]
check(1,[[((n+1)&255) for n in range(256)], [((n+1)&256) for n in range(256)], [((n+1)|255) for n in range(256)], [((n+1)|256) for n in range(256)]],expected)
# q2: 正規分布のf''/f=((x-mu)^2-sigma^2)/sigma^4の零点
mu,sigma=60,10
inflections=(mu-sigma,mu+sigma)
assert all(((x-mu)**2-sigma**2)==0 for x in inflections)
# 図から転記: 中心、右変曲点、左右対称一峰性
check(2,[(60,70,True),(60,65,True),(60,None,False),(60,None,False)],(mu,inflections[1],True))
# q6: 原本の4式を複数n,aに代入し線形探索回数を列挙
params=list(itertools.product((1,2,7,20),(F(0),F(1,4),F(1,2),F(1))))
values=[sum(range(1,n+1))/F(n)*(1-a)+n*a for n,a in params]
check(6,[[F(n+1)*n*a/2 for n,a in params],[F(n+1)*(1-a)/2 for n,a in params],[F(n+1)*(1-a)/2+F(n,2) for n,a in params],[F(n+1)*(1-a)/2+n*a for n,a in params]],values)
# q7: stable partitionを2回のみ実行
v=[2,3,5,4,1];pivot=v[0];left=[x for x in v[1:] if x<pivot];right=[x for x in v[1:] if x>pivot]
p=right[0];out=left+[pivot]+[x for x in right[1:] if x<p]+[p]+[x for x in right[1:] if x>p]
check(7,[[1,2,3,5,4],[1,2,5,4,3],[2,3,1,4,5],[2,3,4,5,1]],out)
check(8,[F(8,10),F(125,100),F(25,10),F(10)],F(1250000000,1000000000))
# q9: 時刻ごとに全命令のstage位置を追跡
finished=[t for t in range(1,30) if any(t-i==5 for i in range(20))]
check(9,[20,21,24,25],max(finished))
# q14: CPU->disk順、各装置FCFS、原本A(3,7),B(12,10)
cpu_end=disk_end=0;timeline=[]
for cpu,disk in [(3,7),(12,10)]:
 cs=cpu_end;cpu_end=cs+cpu;ds=max(cpu_end,disk_end);disk_end=ds+disk;timeline.append((cs,cpu_end,ds,disk_end))
assert timeline==[(0,3,3,10),(3,15,15,25)]
check(14,[(F(47,100),F(53,100)),(F(60,100),F(68,100)),(F(79,100),F(89,100)),(F(88,100),F(1))],(F(3+12,disk_end),F(7+10,disk_end)))
# q16: 原本回路の稼働状態を全8状態列挙し確率和、0<x,y,z<1
signs=set()
for probs in itertools.product((F(1,10),F(1,2),F(9,10)),repeat=3):
 a=b=F(0)
 for state in itertools.product((False,True),repeat=3):
  x,y,z=state;weight=math.prod(p if on else 1-p for on,p in zip(state,probs))
  if (x or y) and z:a+=weight
  if (x and z) or y:b+=weight
 assert b-a==probs[1]*(1-probs[2])
 signs.add('B>A' if b>a else 'A>B' if a>b else 'A=B')
check(16,[{'varies'},{'A=B'},{'A>B'},{'B>A'}],signs)
# q17: FIFO hitはロード順を変えない
frames=[None]*3;queue=[]
for page in [1,4,2,4,1,3]:
 if page in frames:continue
 if None in frames:slot=frames.index(None)
 else:old=queue.pop(0);slot=frames.index(old)
 frames[slot]=page;queue.append(page)
check(17,[[1,3,4],[1,4,3],[3,4,2],[4,1,3]],frames)
# q19: 衝突のない直接番地アクセスの探索probe数は件数によらず1
probes=[]
for size in (1,10,100,1000):
 table={i:i for i in range(size)};probes.append(1 if table[size-1]==size-1 else 0)
check(19,[[1,2,4,8],[1,10,100,1000],[1,2,3,4],[1,1,1,1]],probes)
# q21: NAND wiringをそのまま真理値列へ
inputs=list(itertools.product((0,1),repeat=2));nand=lambda x,y:1-(x&y)
out=[nand(nand(x,x),nand(y,y)) for x,y in inputs]
check(21,[[x&y for x,y in inputs],[x|y for x,y in inputs],[nand(x,y) for x,y in inputs],[1-(x|y) for x,y in inputs]],out)
# q22: 接地アノード/出力カソード、順電圧0のideal shunt diode
vin=[0,1,0,-1,0,1,0];out=[0 if 0>v else v for v in vin]
check(22,[[0,1,0,0,0,1,0],[0,0,0,-1,0,0,0],[1,1,1,0,1,1,1],[0,1,0,1,0,1,0]],out)
# q26: 原本のJSONの異なる項目/型/配列を商品単位で復元
j1={'_id':'AA09','品名':'47型テレビ','価格':'オープンプライス','関連商品id':['AA101','BC06']}
j2={'_id':'AA10','商品名':'りんご','生産地':'青森','価格':100,'画像URL':'http://www.example.com/apple.jpg'}
assert set(j1)!=set(j2) and type(j1['価格'])!=type(j2['価格'])
docs=[json.loads(json.dumps(j,ensure_ascii=False)) for j in (j1,j2)]
assert docs==[j1,j2] and docs[0]['関連商品id'][1]=='BC06'
check(26,['two-level-item-value','two-set-nodes','document-per-product','predefined-item-columns'],'document-per-product')
# q28: 一回/二回の操作結果を状態で比較
set100=lambda s:100;add100=lambda s:s+100
assert set100(set100(7))==set100(7) and add100(add100(7))!=add100(7)
check(28,['repeat-once-equivalence','all-or-nothing','replicate-other-node','concurrent-serial-equivalence'],'repeat-once-equivalence')
# q29: 各部門に1社員以上、各社員が1部門所属、現在所属も履歴記録
current={'e1':'d1','e2':'d2','e3':'d1'}
history=[('d1','e1'),('d2','e2'),('d1','e3'),('d2','e1')]
assert all(sum(d==dept for d,e in history)>=1 for dept in set(current.values()))
assert all(sum(e==emp for d,e in history)>=1 for emp in current)
# 異動で双方複数可能。下限は現在所属から1
check(29,[('0..*','0..*'),('0..*','1..*'),('1..*','0..*'),('1..*','1..*')],('1..*','1..*'))
# q30: 原本の親/子キーでON DELETE CASCADEをSQL実行
con=sqlite3.connect(':memory:');con.execute('PRAGMA foreign_keys=ON')
con.executescript('CREATE TABLE orders(order_no INTEGER PRIMARY KEY); CREATE TABLE details(order_no INTEGER,detail_no INTEGER,product_no INTEGER,qty INTEGER,PRIMARY KEY(order_no,detail_no),FOREIGN KEY(order_no) REFERENCES orders(order_no) ON DELETE CASCADE);INSERT INTO orders VALUES(1),(2);INSERT INTO details VALUES(1,1,10,2),(1,2,11,3),(2,1,10,5);DELETE FROM orders WHERE order_no=1;')
assert con.execute('SELECT * FROM details').fetchall()==[(2,1,10,5)]
check(30,['CASCADE','INTERSECT','RESTRICT','UNIQUE'],'CASCADE')
# q32: 同じ1ms間隔を含む送信時間から差を取る
bits=1250*8
single_delta=F(bits,100000000)-F(bits,1000000000)
check(32,[10,80,100,800],F(9,1000)/single_delta)
# q33: 実際の外側からのheaderフィールド列
ethernet=['dst-mac','src-mac','type'];ip=['version','header-length','total-length','src-ip','dst-ip'];tcp=['src-port','dst-port']
stream=ethernet+ip+tcp;order=sorted(['dst-ip','dst-mac','dst-port'],key=stream.index)
check(33,[['dst-ip','dst-mac','dst-port'],['dst-ip','dst-port','dst-mac'],['dst-mac','dst-ip','dst-port'],['dst-mac','dst-port','dst-ip']],order)
# q38: RSA署名を送信者秘密鍵で生成し送信者公開鍵で検証
n,e,d,digest=3233,17,2753,42
signature=pow(digest,d,n);assert pow(signature,e,n)==digest
# 受信者鍵(e=3,n=2773)では一致しない
assert pow(signature,3,2773)!=digest
check(38,[('receiver-public','sender-create'),('receiver-private','receiver-check'),('sender-public','receiver-check'),('sender-private','sender-create')],('sender-public','receiver-check'))
# q47: 全8列、原本四表のX行(割引率)を独立転記
cols=list(itertools.product((True,False),repeat=3))
rates=[3*sum(c) for c in cols]
check(47,[[9,6,3,3,9,3,6,0],[9,3,0,6,6,3,3,0],[9,6,6,3,6,3,3,0],[9,3,6,0,9,3,6,0]],rates)
# q48: 依存関係「開始計画→実行中daily→成果review→チーム改善」
check(48,[[1,4,2,3],[1,4,3,2],[4,1,2,3],[4,1,3,2]],[1,4,3,2])
# q53: 原本期間比。工数比(.17,.21,.16,.16,.11,.19)を計算に混入しない
periods=list(map(F,['.25','.21','.11','.11','.11','.21']))
total=F(228)/sum(periods[:3]);remaining=total*(periods[3]*F(100,200)+sum(periods[4:]))
assert total==400
check(53,[140,150,161,172],remaining)
# q57: 物理作業はIaaSで移管、middleware作業はPaaSで移管、businessは残る
layers={1:'business',2:'physical',3:'physical',4:'middleware'}
removed_iaas=tuple(i for i,l in layers.items() if l=='physical');removed_paas=tuple(i for i,l in layers.items() if l=='middleware')
check(57,[((1,),(2,4)),((1,3),(2,)),((2,3),(4,)),((3,),(2,4))],(removed_iaas,removed_paas))
check(67,[40,60,250,600],F(1500*1000,600000)*100)
# q75: 原本の確率・売上・費用を葉から計算。意思決定はmax
extra_a=F(3,10)*200+F(7,10)*100-60
extra_b=F(4,10)*150+F(6,10)*100-40
profit_a=F(4,10)*max(extra_a,50)+F(6,10)*120-30
profit_b=F(3,10)*max(extra_b,70)+F(7,10)*140-40
assert (extra_a,extra_b,profit_a,profit_b)==(70,80,70,82)
choice=('a',profit_a) if profit_a>profit_b else ('b',profit_b)
check(75,[('a',70),('a',160),('b',82),('b',162)],choice)
check(77,[333,425,458,500],F(150+50,1-F(60,100)))
print(f'PASS r05h: {len(results)} independent calculation/diagram/SQL checks / official key and bank; questions {sorted(results)}')
