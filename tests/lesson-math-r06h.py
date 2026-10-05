"""Independent checks derived from the 2024 spring official question figures.
Copy into repository tests/ to run with a repository-relative data root.
"""
from pathlib import Path
from fractions import Fraction as F
import json, math, sqlite3
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'data/questions.json').exists():
    ROOT = Path('/workspace/ap-study')  # dedicated review workspace only
LABELS = 'アイウエ'
answers = next(x for x in json.loads((ROOT/'data/answer-keys.json').read_text()) if x['year']==2024 and x['season']=='spring')['answers']
questions = {x['id']:x for x in json.loads((ROOT/'data/questions.json').read_text())}
results = {}
def check(n, answer, evidence):
    q=questions[f'r06h-q{n}']
    assert answer == answers[n-1] == LABELS[q['answer']], (n, answer, answers[n-1])
    results[n] = {'answer':answer, 'evidence':evidence}
def candidate(n, value, choices, evidence):
    matches=[i for i,x in enumerate(choices) if x==value]
    assert len(matches)==1,(n,value,choices)
    check(n,LABELS[matches[0]],evidence)

# q2: arrival rates add; Wq excludes service. Evaluate all four original expressions.
rho=F(1,5); ts=F(3,1); u=2*rho
candidate(2,u*ts/(1-u),[rho*ts/(1-rho),rho*ts/(1-2*rho),2*rho*ts/(1-rho),2*rho*ts/(1-2*rho)],'u=2ρ; Wq=uTs/(1-u)')
# q4: bit positions are numbered from the LEFT, and syndrome weights are 1,2,4.
bits=list(map(int,'1000101')); groups=((1,3,5,7),(2,3,6,7),(4,5,6,7))
syndrome=[sum(bits[i-1] for i in g)%2 for g in groups]; pos=sum(c*(2**i) for i,c in enumerate(syndrome))
bits[pos-1]^=1
candidate(4,''.join(map(str,bits)),['1000001','1000101','1001101','1010101'],f'syndrome={syndrome}; left position={pos}')
# q5: compare actual flow-chart paths, including M=1 and termination.
def right(M,cond):
    x=n=1
    for _ in range(M+5):
        x*=n; n+=1
        if cond(n,M): return x
    return None
conds=[lambda n,m:n<m,lambda n,m:n>m-1,lambda n,m:n>m,lambda n,m:n>m+1]
valid=[i for i,c in enumerate(conds) if all(right(m,c)==math.prod(range(m,0,-1)) for m in range(1,12))]
assert valid==[2]; check(5,'ウ','M=1..11; only n>M matches descending product and terminates')
# q6: independently encode the original tree and recursion.
tree=('+',('A',None,None),('÷',('×',('B',None,None),('C',None,None)),('−',('D',None,None),('E',None,None))))
def traverse(t):
    if t is None:return ''
    v,l,r=t; return traverse(r)+traverse(l)+v
candidate(6,traverse(tree),['+÷−ED×CBA','ABC×DE−÷+','E−D÷C×B+A','ED−CB×÷A+'],'recursive right,left,self output')
# q8: execute overlap copies in the same memory, preserving original values.
def move(s,d,direction,count):
    mem={a:f'v{a}' for a in range(990,1020)}; step=-1 if direction else 1
    for i in range(count):mem[d+i*step]=mem[s+i*step]
    return [mem[a] for a in range(1003,1007)]
opts=[(1001,1003,0,4),(1001,1003,1,4),(1004,1006,0,4),(1004,1006,1,4)]
assert [i for i,x in enumerate(opts) if move(*x)==[f'v{a}' for a in range(1001,1005)]]==[3]
check(8,'エ','same-memory copy of four distinct sentinel values')
# q10 and q11: exact rational arithmetic avoids rounded candidates.
h=(F(60)-15)/(60-10)
candidate(10,h,[F(1,10),F(17,100),F(83,100),F(9,10)],'15=10h+60(1-h)')
compressed=15*F(40,100); transfer=compressed/20; expand=compressed*F(3,100)
candidate(11,transfer+expand,[F(48,100),F(75,100),F(93,100),F(120,100)],f'compressed={compressed}; transfer={transfer}; expand={expand}')
candidate(14,1/F(1,10),[5,10,15,20],'limit of n/(0.9+0.1n) = 1/0.1')
# q17: explore every interleaving of acquisition steps, not just compare order strings.
def deadlocks(orders):
    seen=set()
    def dfs(state):
        if state in seen:return False
        seen.add(state)
        owner={r:i for i,k in enumerate(state) if k<len(orders[i]) for r in orders[i][:k]}
        runnable=[]
        for i,k in enumerate(state):
            if k<len(orders[i]) and orders[i][k] not in owner:runnable.append(i)
        unfinished=[i for i,k in enumerate(state) if k<len(orders[i])]
        if not unfinished:return False
        if not runnable:return True
        for i in runnable:
            nxt=list(state);nxt[i]+=1
            if dfs(tuple(nxt)):return True
        return False
    return dfs((0,0))
found=[name for name,order in [('B','XYZ'),('C','ZXY'),('D','ZYX')] if deadlocks(('XYZ',order))]
assert found==['C','D']; check(17,'イ','all acquisition interleavings: C,D deadlock possible; B impossible')
# q18: request arrivals are staggered 0,1,2,3; two tasks still each take four seconds.
def completion(slots):
    free=[0]*slots; ends=[]
    for arrival in range(4):
        i=min(range(slots),key=lambda j:free[j]); end=max(arrival,free[i])+4
        free[i]=end; ends.append(end)
    return max(ends),ends
one,seq=completion(1);two,parallel=completion(2)
candidate(18,one-two,[6,7,8,9],f'serial={seq}; parallel={parallel}')
# q21: derive truth table from ALL distinct original waveform intervals.
wave={(0,1):1,(0,0):1,(1,1):0,(1,0):1}
gates=[lambda a,b:a^b,lambda a,b:1-(a^b),lambda a,b:1-(a&b),lambda a,b:1-(a|b)]
assert [i for i,g in enumerate(gates) if all(g(a,b)==y for (a,b),y in wave.items())]==[2]
check(21,'ウ','waveform 00/01/10 ->1; 11->0; original gates XOR/XNOR/NAND/NOR')
y=4+F(8-4,9-5)*(7-5); address=(640*y+7)*F(16,8)
candidate(22,address,[3847,7680,7694,8978],f'x7 on original line ->y{y}; 2 bytes/pixel')
# q26: run all four SQL expressions over original three-part/two-warehouse data.
db=sqlite3.connect(':memory:')
db.executescript("CREATE TABLE parts(id TEXT,reorder INT); CREATE TABLE stock(id TEXT,warehouse TEXT,qty INT); INSERT INTO parts VALUES('P01',100),('P02',150),('P03',100); INSERT INTO stock VALUES('P01','W01',90),('P01','W02',90),('P02','W01',150);")
exprs=['COALESCE(MIN(s.qty),0)','COALESCE(MIN(s.qty),NULL)','COALESCE(SUM(s.qty),0)','COALESCE(SUM(s.qty),NULL)']; outputs=[]
for expr in exprs:
    sql=f"SELECT p.id, CASE WHEN p.reorder>{expr} THEN '必要' ELSE '不要' END FROM parts p LEFT OUTER JOIN stock s ON p.id=s.id GROUP BY p.id,p.reorder ORDER BY p.id"
    outputs.append(db.execute(sql).fetchall())
expected=[('P01','不要'),('P02','不要'),('P03','必要')]
assert [i for i,v in enumerate(outputs) if v==expected]==[2];check(26,'ウ',f'all SQL outputs={outputs}')
# q33: exact packet-error probability and usual rare-event approximation agree on nearest choice.
p=F(1,10**6); bitcount=1500*8; exact=10000*(1-(1-float(p))**bitcount); approx=10000*bitcount*p
assert abs(exact-120)<1;candidate(33,min([10,15,80,120],key=lambda v:abs(v-exact)),[10,15,80,120],f'exact expected {exact:.6f}; approximate {approx}')
candidate(38,2*4,[4+1,2*4,4*(4-1)//2,4**2],'n=4 distinct per-person public/private keys; general 2n')
# q51: slopes in original figure show PV>AC>EV. Numeric values only encode that ordering.
pv,ac,ev=100,80,50
assert ev/ac<1 and ev/pv<1; check(51,'ア','CPI<1 -> cost overrun; SPI<1 -> late')
# q52: include the zero-duration dummy edge 4->5.
edges=[(1,2,3),(1,3,2),(2,3,1),(2,4,4),(2,5,2),(3,5,2),(4,5,0),(4,6,1),(5,6,1)]
earliest={1:0}
for node in range(2,7):earliest[node]=max(earliest[s]+d for s,t,d in edges if t==node)
candidate(52,earliest[5],[4,5,6,7],f'earliest nodes={earliest}')
new=F(7,10)*180+F(3,10)*50-100; modify=F(7,10)*120+F(3,10)*40-50
candidate(54,('modify',modify),[('modify',46),('modify',96),('new',41),('new',130)],f'new={new}; modify={modify}; choose max')
monthly=[4000*250,700*1500,300*3300,1600*650]; profit=max(monthly)*12/10000-1050
candidate(55,profit,[150,198,210,260],f'monthly yen={monthly}; annual profit after cost')
flows=[[100,150,200,250,300],[100,200,300,200,100],[200,150,100,150,200],[300,200,100,50,50]]
def payback(flows):
    total=0
    for year,value in enumerate(flows,1):
        if total+value>=500:return F(year-1)+(500-total)/F(value)
        total+=value
periods=list(map(payback,flows));candidate(64,min(range(4),key=lambda i:periods[i]),[0,1,2,3],f'fractional-year paybacks={list(map(str,periods))}')
feasible=[(x+y,x,y) for x in range(41) for y in range(31) if 3*x+2*y<=120 and x+2*y<=60]; best=max(feasible)
candidate(75,best[0],[30,40,45,60],f'integer enumeration best profit,x,y={best}; sum constraints proves x+y<=45')
this_profit=(200-100)*2500-150000; fixed=150000*F(105,100); price=200*F(95,100); need=(this_profit+fixed)/(price-100); n=math.ceil(need)
assert (price-100)*n-fixed>=this_profit and (price-100)*(n-1)-fixed<this_profit
candidate(76,n,[2575,2750,2778,2862],f'profit={this_profit}; next fixed={fixed}; price={price}; n>={need}')
variable_rate=F(200+100,500);fixed=100+80
candidate(77,fixed/(1-variable_rate),[225,300,450,480],f'variable rate={variable_rate}; fixed={fixed}')
if __name__=='__main__':
    print(json.dumps({'checked':len(results),'results':results},ensure_ascii=False,indent=2))
