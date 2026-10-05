"""Independent transcription of r06a source-image calculations, diagrams and SQL.
Run after copying to repository tests/, or pass repository root as argv[1].
No lesson text is used in deriving expected answers.
"""
from pathlib import Path
import itertools,json,sqlite3,sys
from fractions import Fraction as F
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
keys=next(x['answers'] for x in json.loads((ROOT/'data/answer-keys.json').read_text()) if x['year']==2024 and x['season']=='autumn')
questions={x['id']:x for x in json.loads((ROOT/'data/questions.json').read_text())}
checked=[]
def answer(n,index):
 assert keys[n-1]=='アイウエ'[index],(n,index,keys[n-1])
 assert questions[f'r06a-q{n}']['answer']==index
 checked.append(n)
# Q1 M/M/1 queue delay, constant mean service time.
ratio=(F(40,100)/(1-F(40,100)))/(F(25,100)/(1-F(25,100)))
answer(1,[F(125,100),F(160,100),F(2),F(3)].index(ratio))
# Q3 postfix interpreter; only C yields A+B*C for independently selected values.
def postfix(tokens,values):
 stack=[]
 for t in tokens:
  if t in '+*':
   if len(stack)<2:return None
   b=stack.pop();a=stack.pop();stack.append(a+b if t=='+' else a*b)
  else:stack.append(values[t])
 return stack[0] if len(stack)==1 else None
choices=['+*CBA','*+ABC','ABC*+','CBA+*'];matches=[]
for i,c in enumerate(choices):
 if all(postfix(c,dict(zip('ABC',v)))==v[0]+v[1]*v[2] for v in [(2,3,7),(11,5,2),(1,4,9)]):matches.append(i)
assert len(matches)==1;answer(3,matches[0])
# Q5 retain every edge except moved leaf and remove key12. Ordered tree property.
original={6:(4,8),4:(2,5),2:(1,3),8:(7,12),12:(10,14),10:(9,11),14:(13,15)}
def bst(tree,node,lo=float('-inf'),hi=float('inf')):
 if node is None:return True
 if not lo<node<hi:return False
 l,r=tree.get(node,(None,None));return bst(tree,l,lo,node) and bst(tree,r,node,hi)
valid=[]
for i,moved in enumerate([9,10,13,14]):
 tree=dict(original)
 # Remapping a nonleaf without reconnecting its children violates "move only".
 if moved in tree:continue
 for k,v in list(tree.items()):tree[k]=tuple(None if c==moved else moved if c==12 else c for c in v)
 tree[moved]=tree.pop(12)
 if bst(tree,6):valid.append(i)
assert valid==[2];answer(5,valid[0])
# Q6 universal modular collision condition, bounded exhaustive counterexamples.
conditions=[lambda a,b,n:(a+b)%n==0,lambda a,b,n:(a-b)%n==0,
 lambda a,b,n:n%(a+b)==0,lambda a,b,n:(a-b)!=0 and n%(a-b)==0]
valid=[i for i,c in enumerate(conditions) if all(c(a,b,n)==(a%n==b%n) for n in range(1,13) for a in range(1,21) for b in range(1,21) if a!=b)]
assert valid==[1];answer(6,valid[0])
# Q8 stages transcribed as writeback1, execute/address2, decode/register3, fetch4, memory5.
pipeline_options=[(3,4,2,5,1),(3,5,2,4,1),(4,3,2,5,1),(4,5,3,2,1)]
dependencies=[(4,3),(3,2),(2,5),(5,1)]
valid=[i for i,order in enumerate(pipeline_options) if all(order.index(a)<order.index(b) for a,b in dependencies)]
assert valid==[2];answer(8,2)
# Q10 weighted time and sequential cache-check alternative both round to .08.
weighted=F(95,100)*F(1,30)+F(5,100)
serial=F(1,30)+F(5,100)
for value in (weighted,serial):assert min(range(4),key=lambda i:abs(value-[F(3,100),F(8,100),F(37,100),F(95,100)][i]))==1
answer(10,1)
# Q14 exact polynomial differences plus rational range samples.
# A-C=r*(1-r)^2*(r+2), C-B=r^3*(1-r); factors >0 for 0<r<1.
for r in [F(i,101) for i in range(1,101)]:
 A=1-(1-r)**2;B=r*A;C=1-(1-r*r)**2
 assert A-C==r*(1-r)**2*(r+2)>0
 assert C-B==r**3*(1-r)>0
answer(14,1)
# Q15 capacity in searches/sec is bottleneck, not sum of resource times.
cpu=100*10**6//10**6;network=8*10**7//(2*10**5*8)
assert (cpu,network)==(100,50);answer(15,[50,100,200,400].index(min(cpu,network)))
# Q21 seven consecutive waveform intervals, transcribed independently from each candidate.
waveforms=[([0,1,0,0,0,1,0],[0,0,1,0,1,1,0],[0,1,1,0,1,1,0]),
 ([0,1,0,0,0,1,0],[0,0,0,1,0,1,0],[1,0,1,0,1,0,1]),
 ([0,0,1,0,1,0,1],[1,0,1,0,1,0,0],[0,0,1,0,1,0,0]),
 ([0,0,1,0,1,0,1],[1,0,1,0,1,0,0],[1,1,0,1,0,1,1])]
valid=[i for i,(a,b,y) in enumerate(waveforms) if y==[x&z for x,z in zip(a,b)]]
assert valid==[2];answer(21,2)
# Q26 raw pixel stream; units are bits from outset.
rate=800*600*24*30
answer(26,min(range(4),key=lambda i:abs([350e3,3.5e6,35e6,350e6][i]-rate)))
# Q28 two possible underlying purchase histories give identical supplied tables,
# but different daily buyer counts. A date-free purchase table cannot distinguish them.
from collections import Counter
def supplied_tables(world):
 daily=Counter();purchase=Counter()
 for customer,agent,product,date,quantity in world:
  daily[agent,date,product]+=quantity;purchase[customer,agent,product]+=quantity
 return daily,purchase
def daily_buyers(world):
 groups={}
 for customer,agent,product,date,quantity in world:groups.setdefault((agent,date),set()).add(customer)
 return {k:len(v) for k,v in groups.items()}
world1=[('C1','V','P','day1',2),('C2','V','P','day2',2)]
world2=[(c,'V','P',d,1) for c in ['C1','C2'] for d in ['day1','day2']]
assert supplied_tables(world1)==supplied_tables(world2)
assert daily_buyers(world1)!=daily_buyers(world2);answer(28,2)
# Q29 diagram object edges; evidence disproves reverse and one-to-one relations.
region_supplier=[('東京',11),('大阪',25),('大阪',37)]
supplier_purchase=[(11,1),(11,2),(11,3),(25,4),(25,5),(37,6)]
purchase_part=[(1,136),(2,205),(3,338),(4,136),(5,205),(6,338)]
assert len({s for r,s in region_supplier if r=='大阪'})==2
assert len({p for s,p in supplier_purchase if s==11})==3
assert all(sum(p==n for p,_ in purchase_part)==1 for n in range(1,7))
assert sum(c==136 for _,c in purchase_part)==2;answer(29,1)
# Q30 execute all four candidate windows against image table and original inner join.
db=sqlite3.connect(':memory:');db.execute('CREATE TABLE grades(student TEXT, round INTEGER, score INTEGER)')
db.executemany('INSERT INTO grades VALUES(?,?,?)',[('S01',1,70),('S01',7,80),('S02',2,85),('S02',5,82),('S03',3,83),('S03',9,78),('S03',12,90),('S04',6,100)])
sql1='SELECT a.student,a.round,a.score FROM grades a INNER JOIN (SELECT student,MIN(round) first_round FROM grades GROUP BY student) b ON a.student=b.student AND a.round=b.first_round'
expected=sorted(db.execute(sql1));windows=['ORDER BY student,round','PARTITION BY student ORDER BY round','PARTITION BY student ORDER BY score ASC','PARTITION BY student ORDER BY score DESC']
valid=[]
for i,w in enumerate(windows):
 query=f'SELECT student,round,score FROM (SELECT *,ROW_NUMBER() OVER({w}) n FROM grades) WHERE n=1'
 if sorted(db.execute(query))==expected:valid.append(i)
assert valid==[1];answer(30,1)
# Q32 transmission time including efficiency; find lowest sufficient service.
times=[F(8,1)/(F(6,10)*v) for v in [1,2,4,10]]
answer(32,next(i for i,t in enumerate(times) if t<=5))
# Q64 distinct annual cash effects; 4staff=>one transferred salary reduction, fixed contract.
effects=[]
for staff,outsourced in [(4,True),(4,False),(5,True),(5,False)]:
 internal=7000-(2000 if outsourced else 0)
 idle=staff*1800-internal
 effects.append((5-staff)*600+F(idle,100)*20-(700 if outsourced else 0))
assert effects==[340,640,100,400];answer(64,max(range(4),key=effects.__getitem__))
# Q72 directed Hamiltonian paths, no return-to-start requirement.
setup=[[0,2,1,2],[1,0,1,2],[3,2,0,2],[4,3,2,0]]
costs=[(sum(setup[a][b] for a,b in zip(p,p[1:])),p) for p in itertools.permutations(range(4))]
assert min(costs)==(4,(1,0,2,3));answer(72,[4,5,6,7].index(min(costs)[0]))
# Q73 net parent requirements before exploding next level.
A=300-100;a=A*3-100;b=A*2+a*1-300
assert (A,a,b)==(200,500,600);answer(73,[200,600,900,1500].index(b))
# Q75 Nash equilibrium: simultaneous best replies; cannot improve own payoff unilaterally.
market=[[(40,20),(50,30)],[(30,10),(25,25)]]
equilibria=[]
for a,b in itertools.product(range(2),repeat=2):
 if all(market[a][b][0]>=market[alt][b][0] for alt in range(2)) and all(market[a][b][1]>=market[a][alt][1] for alt in range(2)):equilibria.append((a,b))
assert equilibria==[(0,1)];answer(75,[(0,0),(0,1),(1,0),(1,1)].index(equilibria[0]))
# Q77 contribution margin, break-even, sensitivity under constant variable cost ratios.
marginA=F(1000-500,1000);marginB=F(1000-800,1000)
assert marginA>marginB and 400/marginA==800 and 100/marginB==500
assert (1100*marginA-400)-(1000*marginA-400)>(1100*marginB-100)-(1000*marginB-100)
answer(77,0)
print('r06a independent calculations/diagrams/SQL passed:',len(checked),'questions',checked)
