#!/usr/bin/env python3
"""r05a official-image independent checks.

Inputs below were transcribed while reading all 80 official crops before lesson
comparison. No lesson explanation text is used. Run from tests/ or pass repo root.
Q71 initial broad-IoT interpretation was rechecked against official E and the
actual city-model/simulation condition; audit is in review.json.
"""
from pathlib import Path
from itertools import product, combinations
from fractions import Fraction
import ipaddress
import json
import math
import sqlite3
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
LABELS = 'アイウエ'
# Final independent answers, with q71 reread documented rather than hidden.
INDEPENDENT = (
    'ウエアアウウイウウア'
    'イイイエエエアイエエ'
    'ウウアアイエアアイア'
    'ウイイイエウアウアア'
    'イウアアエウエアアア'
    'エウアエアイイウウイ'
    'イアエウアエアウイウ'
    'エイイエエイエエアイ'
)
KEY = next(x['answers'] for x in json.loads((ROOT/'data/answer-keys.json').read_text())
           if x['year'] == 2023 and x['season'] == 'autumn')
BANK = {r['number']: r for r in json.loads((ROOT/'data/questions.json').read_text())
        if r['id'].startswith('r05a-q')}
assert len(INDEPENDENT) == len(KEY) == len(BANK) == 80
for q, label in enumerate(INDEPENDENT, 1):
    assert label == KEY[q-1] == LABELS[BANK[q]['answer']], (q, label, KEY[q-1], BANK[q]['answer'])
GROUPS = []
def answer(q, index, reason):
    assert LABELS[index] == KEY[q-1] == LABELS[BANK[q]['answer']], (q, reason)
    GROUPS.append((q, reason))

# Q1 two-bit swap. Evaluate all four candidates on all possible input values.
swap = lambda x: 2*(x % 2) + x//2
coefficients = [4,5,-3,-4]
match = [all(2*x+c*(x//2) == swap(x) for x in range(4)) for c in coefficients]
assert match == [False,False,True,False]
answer(1, match.index(True), 'all four two-bit inputs and all candidate formulae')

# Q3 ABCD-×+ is independently evaluated as a stack program.
stack=[]
for token in [16,8,4,2,'-','*','+']:
    if isinstance(token,int): stack.append(token)
    else:
        b,a=stack.pop(),stack.pop()
        stack.append({'-': lambda:a-b, '*':lambda:a*b, '+':lambda:a+b}[token]())
assert stack == [32]
answer(3,[32,46,48,94].index(stack[0]),'postfix stack evaluation')

# Q4 actual 4×4 even-parity data; one-error syndromes are unique, two are not.
data=[[1,0,0,0],[0,1,1,0],[0,0,1,0],[1,1,0,1]]
assert [sum(row)%2 for row in data] == [1,0,1,1]
assert [sum(row[c] for row in data)%2 for c in range(4)] == [0,0,0,1]
def syndrome(flips):
    rows,cols=[0]*4,[0]*4
    for r,c in flips: rows[r]^=1;cols[c]^=1
    return tuple(rows+cols)
cells=list(product(range(4),repeat=2))
assert len({syndrome([p]) for p in cells}) == 16
assert syndrome([(0,0),(1,1)]) == syndrome([(0,1),(1,0)])
assert syndrome([(0,0),(0,1),(1,0),(1,1)]) == (0,)*8
answer(4,0,'one-bit correction guaranteed; ambiguous two-bit error positions')

# Q5 elem/next/prev are copied from the original table, 1-based.
elem=['', 'A','F','D','B','E'];nxt=[0,4,0,5,3,2];prev=[0,0,5,4,1,3]
order=[];i=1
while i: order.append(elem[i]);i=nxt[i]
assert order == ['A','B','D','E','F']
new_next,new_prev=nxt[3],3
nxt.append(new_next);prev.append(new_prev);elem.append('C');nxt[3]=6;prev[new_next]=6
order=[];i=1
while i: order.append(elem[i]);i=nxt[i]
assert order == ['A','B','D','C','E','F']
answer(5,[(2,3),(3,4),(5,3),(5,4)].index((new_next,new_prev)),'array-linked insertion')

# Q6 reproduce complete adjacent-comparison passes, not a chosen named answer.
values=[3,5,9,6,1,2];states=[]
for end in [5,4]:
    for i in range(end):
        if values[i]>values[i+1]: values[i],values[i+1]=values[i+1],values[i]
    states.append(values[:])
assert states == [[3,5,6,1,2,9],[3,5,1,2,6,9]]
answer(6,2,'bubble passes reproduce both original intermediate states')

# Q15 no double failure: repair runs while service remains on standby.
availability=Fraction(99,99+2)
assert round(float(availability),2)==.98
answer(15,[.82,.89,.91,.98].index(round(float(availability),2)),'99h up / (99h up + 2h failover)')

# Q16 weighted mean, independent of the authored equation string.
p=Fraction(60-30,60-20)
assert 20*p+60*(1-p)==30 and p==Fraction(3,4)
answer(16,[.25,.33,.67,.75].index(float(p)),'20/60ms weighted mean equals 30ms')

# Q17 simulate priority scheduling for each candidate until B first completion.
task_options=[(2,4,3,8),(3,6,4,9),(3,5,5,13),(4,6,5,15)]
completion=[]
for ca,ta,cb,tb in task_options:
    remaining=cb;t=0
    while remaining:
        if t%ta >= ca: remaining-=1
        t+=1
    completion.append(t)
assert completion == [7,10,14,17]
assert [r<=o[3] for r,o in zip(completion,task_options)] == [True,False,False,False]
answer(17,0,'discrete 1ms priority scheduling of all four candidates')

# Q22 trace gates in their signal order and verify stable feedback equations.
x,y=0,1;r=1
s=0;x=int(not(s and y));y=int(not(r and x));assert (x,y)==(1,0)
s=1;x=int(not(s and y));y=int(not(r and x));assert (x,y)==(1,0)
assert x==int(not(s and y)) and y==int(not(r and x))
answer(22,[(0,0),(0,1),(1,0),(1,1)].index((x,y)),'cross-connected AND/inverter state transition')

# Q23 every gate shape was read: AND+OR, XOR+OR, OR+AND/NOT, XOR+AND/NOT.
expected=[0,0,0,1,0,1,1,1]
def circuits(a,b,c):
    pairs=[(a,b),(b,c),(c,a)]
    return [int(any(u and v for u,v in pairs)), int(any(u^v for u,v in pairs)),
            int(not all(u or v for u,v in pairs)), int(not all(u^v for u,v in pairs))]
columns=list(zip(*(circuits(*bits) for bits in product([0,1],repeat=3))))
assert [list(c)==expected for c in columns] == [True,False,False,False]
assert list(columns[3]) == [1]*8
answer(23,0,'all eight truth-table rows for all four gate diagrams')

# Q28 view provenance: the literal original SQL operators determine eligibility.
view_sql=[
 'SELECT 商品番号,商品名,商品単価 FROM 商品 WHERE 商品単価>1000',
 'SELECT DISTINCT 商品番号 FROM 受注',
 'SELECT 商品番号,SUM(受注数量) FROM 受注 GROUP BY 商品番号',
 'SELECT AVG(受注数量) FROM 受注',
]
# SQL-standard directly updatable single-table views preserve individual rows.
eligible=[not any(op in sql for op in ['DISTINCT','GROUP BY','SUM(','AVG(']) for sql in view_sql]
assert eligible==[True,False,False,False]
answer(28,0,'row-preserving selection versus original DISTINCT/SUM/AVG views')

# Q29 SQL actually executes the original NOT EXISTS on independently copied rows.
db=sqlite3.connect(':memory:')
db.executescript('CREATE TABLE product(id TEXT);CREATE TABLE stock(warehouse TEXT,id TEXT,amount INTEGER);')
db.executemany('INSERT INTO product VALUES (?)',[(v,) for v in ['AB1805','CC5001','MZ1000','XZ3000','ZZ9900']])
db.executemany('INSERT INTO stock VALUES (?,?,?)',[
 ('WH100','AB1805',20),('WH100','CC5001',200),('WH100','ZZ9900',130),
 ('WH101','AB1805',150),('WH101','XZ3000',30),('WH102','XZ3000',20),
 ('WH102','ZZ9900',10),('WH103','CC5001',40)])
rows=db.execute('SELECT DISTINCT id FROM product WHERE NOT EXISTS '
 '(SELECT id FROM stock WHERE amount>30 AND product.id=stock.id)').fetchall()
assert rows==[('MZ1000',),('XZ3000',)]
answer(29,[1,2,3,4].index(len(rows)),'SQLite execution with all stock rows, strict >30 and missing stock')

# Q30 diagram facts: checkpoint=0, commits after/before it, writes copied table.
transactions={'T1':(-1,20),'T2':(1,20),'T3':(None,0),'T4':(None,0),'T5':(2,10),'T6':(None,10)}
redo={t for t,(commit,writes) in transactions.items() if writes and commit is not None and commit>0}
undo={t for t,(commit,writes) in transactions.items() if writes and commit is None}
assert redo=={'T2','T5'} and undo=={'T6'}
answer(30,0,'checkpoint/commit positions and write counts determine redo/undo')

# Q31 byte/bit conversion and 50% effective LAN throughput.
seconds=Fraction(1000*1000*8,100_000_000)*2
assert seconds==Fraction(4,25)
answer(31,[.02,.08,.16,1.6].index(float(seconds)),'1000B × 1000 × 8 / (100M × 50%)')

# Q32 inverse NAPT mapping modifies precisely destination tuple in response.
private=('192.168.1.8',51000);external=('203.0.113.1',61000);web=('198.51.100.5',80)
response={'dst_ip':external[0],'src_ip':web[0],'dst_port':external[1],'src_port':web[1]}
restored={**response,'dst_ip':private[0],'dst_port':private[1]}
changed=tuple(restored[k]!=response[k] for k in ['dst_ip','src_ip','dst_port','src_port'])
assert changed==(True,False,True,False)
answer(32,1,'response destination IP and port inverse mapping')

# Q34 AND all four independently copied octets and cross-check stdlib network.
network=tuple(a&m for a,m in zip([172,30,123,45],[255,255,252,0]))
assert network==(172,30,120,0)
assert str(ipaddress.IPv4Network('172.30.123.45/255.255.252.0',strict=False).network_address)=='172.30.120.0'
answer(34,1,'four-octet mask AND and independent ipaddress result')

# Q52 numerical example proves current variance, not a final-date prediction.
ev,pv=80,100
assert ev-pv<0 and ev/pv<1
answer(52,2,'negative earned/planned variance = current work behind plan')

# Q53 full DAG earliest finishes, including zero-duration right-to-left dummy.
def finish(edges):
    nodes={v for e in edges for v in e[:2]};times={0:0};pending=nodes-{0}
    while pending:
        ready=[v for v in pending if all(u in times for u,w,d in edges if w==v)]
        assert ready, 'cycle or bad transcription'
        for v in ready:
            times[v]=max(times[u]+d for u,w,d in edges if w==v)
            pending.remove(v)
    return times
# nodes 0 start,1 A-end,2 B-end,3 D-end,4 C-end,5 H-start,6 H-end,7 finish.
basic=[(0,1,5),(1,2,8),(2,3,7),(3,7,7),(1,4,7),(4,5,5),(5,6,4),(6,7,2)]
old=finish(basic+[(2,5,9)])
# E1 ends at8, E2 at9, dummy9→8; E3 goes8→5.
new=finish(basic+[(2,8,3),(2,9,4),(9,8,0),(8,5,2)])
assert old[7]==28 and new[7]==27 and new[8]==17 and new[5]==19
answer(53,[1,2,3,4].index(old[7]-new[7]),'all DAG paths and actual dummy direction: 28→27 days')

# Q56 service provision excludes four Monday planned outages.
provided=30*24-4*6;allowed=Fraction(provided,100)
assert provided==696 and allowed==Fraction(174,25)
answer(56,[0,6,7,13].index(math.floor(allowed)),'696h service × 1% = 6.96h, floor 6h')

# Q57 differential backup reconstructs the full base plus all later changes.
base={'unchanged':1,'modified':2};latest={'unchanged':1,'modified':3,'new':4}
diff={k:v for k,v in latest.items() if base.get(k)!=v}
assert {**base,**diff}==latest and diff!=latest
answer(57,1,'full plus latest differential restores unchanged and modified records')

# Q77 straight line depreciation; disposal is a cost rather than proceeds.
annual=Fraction(30)*Fraction(250,1000);book=30-annual*2;loss=book+2
assert annual==Fraction(15,2) and book==15 and loss==17
answer(77,[9.5,13,15,17].index(loss),'30 − 30×0.250×2 + 2 = 17万円')

print(f'r05a: 80 independent answers match official key and bank; {len(GROUPS)} executable calculation/diagram/SQL groups passed')
for q,reason in GROUPS: print(f'q{q}: {reason}')
