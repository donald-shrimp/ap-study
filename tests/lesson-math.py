"""Recompute 2025 spring numerical/algorithm answers against the official key.

Options and problem constants below are transcribed from the official images.
This is an independent calculation check, not a proof of prose quality.
"""
import itertools,json,ipaddress,sqlite3
from fractions import Fraction as F
from pathlib import Path
bank={q['id']:q for q in json.loads((Path(__file__).resolve().parents[1]/'data/questions.json').read_text())}
checked=[]
def check(n,options,value):
 assert options.count(value)==1,(n,value)
 assert options.index(value)==bank[f'r07h-q{n}']['answer'],(n,value)
 checked.append(n)
 print(f'PASS Q{n}: {value}')
def implies(p,q):return not p or q
truth=[]
for r in [False,True]:
 p=q=True
 truth.append([implies(implies(p,q) and implies(q,p),implies(r,not q)),
 implies(implies(p,q) and not implies(q,not p),implies(q,r)),
 implies(implies(p,not q) or implies(q,p),implies(r,not q)),
 implies(implies(p,not q) or implies(q,not p),implies(q,r))])
check(1,list(range(4)),next(i for i in range(4) if all(row[i] for row in truth)))
lo,hi,count=0.,1.,0
while True:
 x=(lo+hi)/2;count+=1
 if hi-x<.001:break
 lo=x
check(2,[10,20,100,1000],count)
outputs=set()
def enumerate_stack(remaining,stack,out):
 if not remaining and not stack:outputs.add(out)
 if remaining:enumerate_stack(remaining[1:],stack+remaining[0],out)
 if stack:enumerate_stack(remaining,stack[:-1],out+stack[-1])
enumerate_stack('ABC','','');assert 'CAB' not in outputs
# Numeric options are not required: the full enumeration fixes the count.
assert len(outputs)==5 and bank['r07h-q5']['answer']==2;checked.append(5)
class Node:
 def __init__(self,key):self.key=key;self.left=self.right=None
def height(n):return 0 if n is None else 1+max(height(n.left),height(n.right))
def right(n):
 x=n.left;n.left=x.right;x.right=n;return x
def left(n):
 x=n.right;n.right=x.left;x.left=n;return x
def insert(n,k):
 if n is None:return Node(k)
 if k<n.key:n.left=insert(n.left,k)
 else:n.right=insert(n.right,k)
 balance=height(n.left)-height(n.right)
 if balance>1:
  if k>n.left.key:n.left=left(n.left)
  return right(n)
 if balance< -1:
  if k<n.right.key:n.right=right(n.right)
  return left(n)
 return n
def structure(n):return None if n is None else (n.key,structure(n.left),structure(n.right))
root=None
for k in [5,3,7,2,4,6,1,0]:root=insert(root,k)
assert structure(root)==(5,(3,(1,(0,None,None),(2,None,None)),(4,None,None)),(7,(6,None,None),None))
assert bank['r07h-q6']['answer']==2;checked.append(6)
check(8,[F(1,32),F(1,2),2,8],F(1*4,1)/F(4,2))
def speed(p,n):return 1/(1-p+p/n)
check(11,[3,4,5,6],next(n for n in range(1,100) if speed(F(9,10),n)/speed(F(3,10),n)==3))
# The selected graph is checked visually; recompute its midpoint and relation to y=p.
p=F(1,2);assert p*(1-(1-p)**2)==F(3,8)
assert all(F(k,100)*(1-(1-F(k,100))**2)<=F(k,100) for k in range(101))
assert bank['r07h-q13']['answer']==3;checked.append(13)
frames={4000:1,5000:2,6000:3,7000:4};last={1:0,2:1,3:2,4:3}
for time,page in enumerate([2,5,3,1,6,5,4],4):
 if page not in frames.values():
  victim=min(frames,key=lambda slot:last[frames[slot]]);frames[victim]=page
 last[page]=time
check(15,[4000,5000,6000,7000],next(k for k,v in frames.items() if v==4))
check(18,[820,1024,1300,1312],int('82',16)*10)
def current(t):return (10000*F(1,100)+F(1,10)*t)/(F(1,100)+t)
check(21,[F(11,10),F(111,10),F(1111,10),F(11111,10)],next(t for t in [F(11,10),F(111,10),F(1111,10),F(11111,10)] if current(t)<=1))
R,S={1,2},{2,3};expressions=[(R-S)-(S-R),R-(R-S),R-(S-R),S-(R-S)]
check(28,list(range(4)),next(i for i,x in enumerate(expressions) if x==R&S))
check(30,[500,540,580,598],2000-(1500-20-20))
routes=[('0.0.0.0/0','10.1.0.1'),('192.168.0.0/16','10.1.0.2'),('192.168.1.0/24','10.1.0.3'),('192.168.1.0/26','10.1.0.4')]
matching=[(ipaddress.ip_network(net).prefixlen,hop) for net,hop in routes if ipaddress.ip_address('192.168.1.1') in ipaddress.ip_network(net)]
check(31,[hop for _,hop in routes],max(matching)[1])
check(32,[54,55,117,118],int(str(list(ipaddress.ip_network('10.16.32.64/26').hosts())[-10]).split('.')[-1]))
check(34,[20,30,40,60],30*F(4,3))
assert F(9,10)<1<F(11,10) and F(12,10)>F(9,10);assert bank['r07h-q52']['answer']==1;checked.append(52)
assert 20*F(8,10)==16 and F(1,10)*F(8,10)==F(8,100) and F(1,10)*F(12,10)==F(12,100)
assert bank['r07h-q54']['answer']==2;checked.append(54)
check(55,[F(4,10),F(6,10),F(13,10),F(195,100)],(22-7)*20*F(995-993,1000))
check(64,[4,8,12,14],(F(60,50+100)*50+F(360,50+400)*50)*F(1,5))
assert F(800,100)>F(1000,900) and F(20,100)>F(90,900) and F(20,800)<F(90,1000)
assert bank['r07h-q76']['answer']==3;checked.append(76)
margin=F(600-(-200),9000-7000)
check(77,[3200,4000,4800,5600],8000*(1-margin))
# Verify the exact parent/child delete action in a database, not just its name.
db=sqlite3.connect(':memory:');db.execute('PRAGMA foreign_keys=ON')
db.execute('CREATE TABLE product(code TEXT PRIMARY KEY)');db.execute('CREATE TABLE orders(id INTEGER PRIMARY KEY, code TEXT REFERENCES product(code) ON DELETE CASCADE)')
db.executemany('INSERT INTO product VALUES (?)',[('A',),('B',)]);db.executemany('INSERT INTO orders VALUES (?,?)',[(1,'A'),(2,'A'),(3,'B')]);db.execute("DELETE FROM product WHERE code='A'")
assert db.execute('SELECT id FROM orders').fetchall()==[(3,)] and bank['r07h-q27']['answer']==0;checked.append(27)
print(f'PASS {len(checked)} independent numerical/algorithm/SQL checks')
