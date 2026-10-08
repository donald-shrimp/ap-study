"""Reviewer-written computations; no author verification code imported or copied."""
from pathlib import Path
import json, math, sqlite3, re, hashlib, argparse
parser=argparse.ArgumentParser()
parser.add_argument("--root",type=Path,default=Path.cwd())
parser.add_argument("--questions",type=Path)
parser.add_argument("--research",type=Path,default=Path("/workspace/research/ap-five-years"))
parser.add_argument("--answer-text",type=Path)
parser.add_argument("--output",type=Path)
parser.add_argument("--skip-pdf",action="store_true",help="Run content calculations without local official PDFs; historical PDF evidence remains in reviews.json.")
ARGS=parser.parse_args()
ROOT=Path(__file__).parent
REPO=ARGS.root
question_path=ARGS.questions or REPO/'content/ap/diagnostic-questions.json'
questions=json.loads(question_path.read_text());questions=questions.get('questions',[]) if isinstance(questions,dict) else questions
byid={q['id']:q for q in questions}
snapshot_path=ROOT/'calculation-inputs.json'
snapshot=json.loads(snapshot_path.read_text())
for expected in snapshot:
 q=byid[expected['id']]
 current={k:q[k] for k in expected}
 assert current==expected,(q['id'],'calculation inputs or four choices changed; rerun reviewer reasoning')
for im in json.loads((ROOT/"calculation-image-hashes.json").read_text()):
 assert hashlib.sha256((REPO/im["path"]).read_bytes()).hexdigest()==im["sha256"],(im["path"],"diagram bytes differ from visually reviewed inputs")
RESULT_INPUTS=True
RESULT={}
def record(n, value, expected):
 assert value==expected,(n,value,expected)
 RESULT[str(n)]={'computed':value,'expected':expected,'passed':True}
# queueing: shared service time, aggregate arrivals
rho=.1;ts=2
record(2,round((3*rho)/(1-3*rho)*ts,10),round(6/7,10))
def syndrome(word):
 b=[0]+list(map(int,word));c=[sum(b[i] for i in g)%2 for g in [(1,3,5,7),(2,3,6,7),(4,5,6,7)]];return c,sum(x*2**i for i,x in enumerate(c))
def correct(word):
 c,pos=syndrome(word);b=list(word)
 if pos:b[pos-1]=str(1-int(b[pos-1]))
 return ''.join(b)
record(4,correct('1001111'),'0001111')
RESULT['4']['allChoiceSyndromes']={s:syndrome(s)[0] for s in ['1001110','1001011','0001111','1000111']}
assert correct('1000101')=='1010101'
# enumerate each loop condition, cap a nonterminating candidate
conds=[lambda n,m:n>m-1,lambda n,m:n>m,lambda n,m:n>m+1,lambda n,m:n<m]
loop={}
for i,c in enumerate(conds):
 outcomes=[]
 for m in range(2,11):
  n=2;x=1
  for _ in range(20):
   x*=n;n+=1
   if c(n,m):break
  else:x=None
  outcomes.append(x==math.factorial(m))
 loop[str(i)]=outcomes
record(5,[i for i,v in loop.items() if all(v)],['1']);RESULT['5']['allChoices']=loop
# independent right-left postorder tree
TREE=('＋','A',('÷',('×','C','B'),('−','D','E')))
def traversal(node):
 return node if isinstance(node,str) else traversal(node[2])+traversal(node[1])+node[0]
record(6,traversal(TREE),'ED−BC×÷A＋')
# memmove: unique values at every address; execute every option
memout=[]
for src,dst,step in [(2003,2001,1),(2003,2001,-1),(2006,2004,1),(2006,2004,-1)]:
 mem={a:a for a in range(1990,2020)}
 for k in range(4):mem[dst+k*step]=mem[src+k*step]
 memout.append([mem[a] for a in range(2001,2005)])
record(8,[i for i,x in enumerate(memout) if x==[2003,2004,2005,2006]],[0]);RESULT['8']['allChoiceResults']=memout
record(11,round(20*.3/15+20*.3*.04,8),.64)
record(14,1/.2,5)
# exhaustive acquisition interleavings, release all on completion
from functools import lru_cache
def deadlock(order1,order2):
 orders=(order1,order2)
 @lru_cache(None)
 def walk(a,b,owners):
  indices=[a,b];steps=[]
  for p in (0,1):
   i=indices[p]
   if i==3:
    newowners=tuple(-1 if x==p else x for x in owners);newidx=indices[:];newidx[p]=4;steps.append((*newidx,newowners))
   elif i<3 and owners[orders[p][i]]==-1:
    newowners=list(owners);newowners[orders[p][i]]=p;newidx=indices[:];newidx[p]+=1;steps.append((*newidx,tuple(newowners)))
  if not steps:return a<4 and b<4
  return any(walk(*s) for s in steps)
 return walk(0,0,(-1,-1,-1))
record(17,[deadlock((0,1,2),o) for o in [(0,1,2),(0,2,1),(2,1,0)]],[False,False,True])
def finish(arrivals,service,width):
 avail=[0]*width;end=[]
 for a in arrivals:
  p=min(range(width),key=lambda k:avail[k]);avail[p]=max(a,avail[p])+service;end.append(avail[p])
 return end
record(18,max(finish(range(5),3,1))-max(finish(range(5),3,2)),6)
RESULT['18']['completionTimes']=[finish(range(5),3,i) for i in [1,2]]
# full truth tables 00,01,10,11
record(21,[int(a==b) for a,b in [(0,0),(0,1),(1,0),(1,1)]],[1,0,0,1])
RESULT['21']['allChoiceTables']={'XOR':[0,1,1,0],'XNOR':[1,0,0,1],'NAND':[1,1,1,0],'NOR':[1,0,0,0]}
record(22,(640*4+5)*2,5130)
# SQL candidates executed, including outer join NULL group
con=sqlite3.connect(':memory:');con.executescript('CREATE TABLE p(id TEXT, reorder INTEGER); CREATE TABLE s(id TEXT, qty INTEGER); INSERT INTO p VALUES ("P01",120),("P02",100),("P03",80); INSERT INTO s VALUES ("P01",60),("P01",80),("P02",100);')
results=[]
for f,replacement in [('MIN','0'),('MIN','NULL'),('SUM','0'),('SUM','NULL')]:
 sql=f'SELECT p.id,CASE WHEN p.reorder>COALESCE({f}(s.qty),{replacement}) THEN "必要" ELSE "不要" END FROM p LEFT JOIN s ON p.id=s.id GROUP BY p.id,p.reorder ORDER BY p.id';results.append(con.execute(sql).fetchall())
record(26,[i for i,r in enumerate(results) if r==[('P01','不要'),('P02','不要'),('P03','必要')]],[2]);RESULT['26']['allChoiceResults']=results
record(33,min([10,16,80,160],key=lambda x:abs(x-5000*(1-(1-2e-6)**8000))),80);RESULT['33']['exact']=5000*(-math.expm1(8000*math.log1p(-2e-6)))
record(38,5*2,10)
# EVM numerical coordinates taken from rendered chart endpoints
record(51,[180/85>1,180/135>1],[True,True])
edges=[(1,2,4),(1,3,3),(2,3,2),(2,4,2),(2,5,3),(3,5,4),(4,5,0),(4,6,1),(5,6,1)];t={1:0}
for node in range(2,7):t[node]=max(t[a]+d for a,b,d in edges if b==node)
record(52,t[5],10);RESULT['52']['allNodes']=t
record(54,[.8*190+.2*60-90,.8*130+.2*50-60],[74,54])
record(55,[int(rate*volume*12/10000-1100) for rate,volume in [(3500,300),(600,1800),(250,4000),(1800,700)]],[160,196,100,412])
flows=[[100,150,200,250,300],[100,200,400,200,100],[200,150,100,150,200],[300,200,100,50,50]]
def payback(flow,investment):
 cumul=0
 for year,f in enumerate(flow):
  if cumul+f>=investment:return year+(investment-cumul)/f
  cumul+=f
 return None
periods=[payback(f,700) for f in flows];record(64,periods,[4,3,4.5,5])
feasible=[(x+y,x,y) for x in range(151) for y in range(91) if 3*x+2*y<=150 and x+2*y<=90];record(75,max(feasible)[0],60);RESULT['75']['maximizers']=[v for v in feasible if v[0]==60]
record(76,math.ceil(((180-90)*3000-120000+120000*1.1)/(180*.95-90)),3482)
record(77,(120+120)/(1-(180+120)/600),480)
# Source PDFs and all80 key verification, performed after all first-pass solutions were saved.
ledger=json.loads((REPO/'data/answer-keys.json').read_text());key=next(r for r in ledger if r['year']==2024 and r['season']=='spring')
extracted=(ARGS.answer_text or ROOT/'official-answer-extracted.txt').read_text();pairs={int(n):a for n,a in re.findall(r'問\s*(\d+)\s+([アイウエ])',extracted)}
assert len(pairs)==80 and [pairs[i] for i in range(1,81)]==key['answers']
sources=json.loads((REPO/'data/sources.json').read_text());pdfs=[]
for r in sources:
 if r['year']==2024 and r['season']=='spring':
  f=ARGS.research/r['filename'];h=r['sha256'] if ARGS.skip_pdf else hashlib.sha256(f.read_bytes()).hexdigest();assert h==r['sha256'];pdfs.append({'kind':r['kind'],'path':str(f),'url':r['url'],'sha256':h,'matchesSourcesLedger':True,'bytesRecheckedInThisRun':not ARGS.skip_pdf})
RESULT['officialPdf']={'all80MatchLedger':True,'extractedAnswers':pairs,'pdfChecks':pdfs,'answerUrl':key['url'],'answerPdfSha256':key['sha256']}
RESULT['contentInputsMatchReviewedSnapshot']=RESULT_INPUTS
(ARGS.output or ROOT/'independent-checks.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2));print('Independent calculations and official 80-answer extraction passed.')
