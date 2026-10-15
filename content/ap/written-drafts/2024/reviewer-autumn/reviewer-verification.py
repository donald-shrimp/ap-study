import json,pathlib,hashlib,fitz,math,sqlite3
from PIL import Image
from fractions import Fraction as F
ROOT=pathlib.Path(__file__).resolve().parents[5]
BASE=ROOT/'content/ap/written-drafts/2024'
OUT=BASE/'reviewer-autumn'
# Independent execution: preserve the 1-based source indexing in each sieve.
def sieve1(n):
 out=[];count=0
 for d in range(2,n+1):
  ok=True
  for t in range(2,d):
   if d%t==0:ok=False
   count+=1
  if ok:out.append(d)
 return out,count
def sieve2(n):
 a=[None,False]+[True]*(n-1);out=[];count=0
 for d in range(2,n+1):
  if a[d]:
   out.append(d);t=d*d
   while t<=n:a[t]=False;t+=d;count+=1
 return out,count
def sieve3(n):
 a=[None]+[True]*((n-1)//2);out=[2];count=0
 for d in range(3,n+1,2):
  if a[(d-1)//2]:
   out.append(d);t=d*d
   while t<=n:a[(t-1)//2]=False;t+=2*d;count+=1
 return out,count
for n in range(2,301):assert sieve1(n)[0]==sieve2(n)[0]==sieve3(n)[0]
counts=[f(20)[1] for f in [sieve1,sieve2,sieve3]];assert counts==[171,13,2]
# Fixed-priority response time recurrence, deadlines = periods, no main/comms cost.
def sched(tasks,scale):
 times=[]
 for k,(c,p) in enumerate(tasks):
  r=c/scale
  while True:
   nr=c/scale+sum(math.ceil(r/pt)*ct/scale for ct,pt in tasks[:k])
   if nr==r:break
   if nr>p:r=nr;break
   r=nr
  times.append({'period':str(p),'response':str(r),'meetsDeadline':r<=p})
 return times
music1=[(F(1),F(2)),(F('3.4'),F(5)),(F(20),F(40))]
music2=music1[:2];call=[(F(1),F(2)),(F('.5'),F(5))]
assert all(t['meetsDeadline'] for t in sched(music1,F(2)))
assert all(t['meetsDeadline'] for t in sched(music2,F('1.5')))
assert all(t['meetsDeadline'] for t in sched(call,F(1)))
assert not all(t['meetsDeadline'] for t in sched(music1,F('1.5')))
assert not all(t['meetsDeadline'] for t in sched(music2,F(1)))
assert not all(t['meetsDeadline'] for t in sched(call,F('.5')))
# SQL independent test with descendants, partial match, range and state filters.
db=sqlite3.connect(':memory:');db.executescript('CREATE TABLE カテゴリ(カテゴリID INT,カテゴリ名 TEXT,上位カテゴリID INT);CREATE TABLE 出品(出品ID INT,カテゴリID INT,出品価格 NUMERIC,商品状態 INT,出品状況 INT,商品名 TEXT,商品説明 TEXT);');db.executemany('INSERT INTO カテゴリ VALUES(?,?,?)',[(1,'root',None),(2,'a',1),(3,'aa',2),(4,'b',1),(5,'other',None)]);db.executemany('INSERT INTO 出品 VALUES(?,?,?,?,?,?,?)',[(1,2,100,1,2,'rare card','x'),(2,3,200,1,2,'normal','rare'),(3,4,300,1,2,'rare','x'),(4,5,100,1,2,'rare','x'),(5,2,100,3,2,'rare','x'),(6,2,100,1,3,'rare','x')]);sql="""WITH RECURSIVE 指定カテゴリ(カテゴリID,カテゴリ名,上位カテゴリID) AS (SELECT A.カテゴリID,A.カテゴリ名,A.上位カテゴリID FROM カテゴリ A WHERE A.カテゴリID=:カテゴリID UNION ALL SELECT B.カテゴリID,B.カテゴリ名,B.上位カテゴリID FROM カテゴリ B,指定カテゴリ C WHERE B.上位カテゴリID=C.カテゴリID) SELECT 出品ID FROM 出品 INNER JOIN 指定カテゴリ ON 出品.カテゴリID=指定カテゴリ.カテゴリID WHERE 出品.出品価格 BETWEEN :下限価格 AND :上限価格 AND 出品.商品状態=:商品状態 AND 出品.出品状況=:出品状況 AND (出品.商品名 LIKE '%' || :キーワード || '%' OR 出品.商品説明 LIKE '%' || :キーワード || '%') ORDER BY 出品ID"""
rows=db.execute(sql,{'カテゴリID':2,'下限価格':90,'上限価格':250,'商品状態':1,'出品状況':2,'キーワード':'rare'}).fetchall();assert rows==[(1,),(2,)]
calculations={'passwordRatio':70**10//70**6,'sieveCountsAt20':counts,'sieveEquivalentN2Through300':True,'renderSeconds':{'ssd':800/500,'cpu4Cores':100000/(500*4),'gpu1':100000/10000,'forwardLAN':500*8/1000,'returnLAN':100*8/1000},'scheduler':{'music1@2':sched(music1,F(2)),'music1@1.5Fails':sched(music1,F('1.5')),'music2@1.5':sched(music2,F('1.5')),'call@1':sched(call,F(1))},'sqlDescendantPartialMatchRows':rows,'staffPersonDays':math.ceil(F(24*10+15*20+8*20)*F('1.2')*F('1.2')/(8*60))}
assert calculations['staffPersonDays']==3
(OUT/'independent-calculations.json').write_text(json.dumps(calculations,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(calculations,ensure_ascii=False))
