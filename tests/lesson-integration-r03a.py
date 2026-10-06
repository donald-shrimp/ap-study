"""Root calculations transcribed from IPA images before reading author lessons.

This checks original numerical conditions and diagrams, not prose quality.
"""
import calendar
from datetime import date
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
import json
import sqlite3
from pathlib import Path

bank = {q['id']: q for q in json.loads(
    (Path(__file__).resolve().parents[1]/'data/questions.json').read_text())}

def official(n, answer):
    assert bank[f'r03a-q{n}']['answer'] == 'アイウエ'.index(answer), n

# Q1: the x-intercept of the tangent, using x^2-2 as an illustration.
x = F(3, 2)
for _ in range(5):
    old = x
    x -= (x*x-2)/(2*x)
    assert (old*old-2) + 2*old*(x-old) == 0
    assert abs(x*x-2) < abs(old*old-2)
official(1, 'エ')
print('PASS Q1: tangent intercept satisfies the original update geometry')

# Q2: merged arrival rate doubles; service time is unchanged.
for rho in [F(1,10), F(1,5), F(2,5)]:
    load = 2*rho
    candidates = [rho/(1-rho), rho/(1-2*rho),
                  2*rho/(1-rho), 2*rho/(1-2*rho)]
    assert candidates.index(load/(1-load)) == 3
assert 2*F(1,5)/(1-2*F(1,5)) == F(2,3)
official(2, 'エ')
print('PASS Q2: stable M/M/1 load 2rho and waiting time excluding service')

# Q8: opposite signs bound the sum by its two operands. Three counterexamples.
lower, upper = -32768, 32767
for x,y in product([lower,-32767,-1,0,1,32766,upper], repeat=2):
    if x*y < 0: assert lower <= x+y <= upper
counterexamples = [(16384,16384), (32766,32766), (20000,20000)]
assert abs(sum(counterexamples[0])) == 32768
assert sum(map(abs,counterexamples[0])) <= 32768
assert all(abs(x)<32767 for x in counterexamples[1])
assert counterexamples[2][0]*counterexamples[2][1] > 0
assert all(not lower<=x+y<=upper for x,y in counterexamples)
official(8,'エ')
print('PASS Q8: asymmetric signed range, three candidate counterexamples')

# Q11: 6000 rpm, 10 ms seek, 10 decimal Mbyte/s, 1000 bytes.
rotation_ms = F(60*1000,6000)
read_ms = 10+rotation_ms/2+F(1000*1000,10_000_000)
assert read_ms == F(151,10)
official(11,'ア')
print('PASS Q11: half rotation plus seek and decimal-byte transfer, 15.1 ms')

# Q15: simulate three independently occupied resources to expose warm-up.
ends = [0,0,0]; completions = []
for item in range(100):
    upstream = 0
    for stage,duration in enumerate([40,30,50]):
        ends[stage] = max(ends[stage],upstream)+duration
        upstream = ends[stage]
    completions.append(upstream)
assert completions[:4] == [120,170,220,270]
assert all(b-a==50 for a,b in zip(completions,completions[1:]))
assert 60_000//50 == 1200
official(15,'エ')
print('PASS Q15: simulated pipeline, 120 ms first item, 50 ms steady interval')

# Q17: original delay is per instruction; faults counted per access.
maximum_p = F(4,10)/(2*40_000)
assert maximum_p == F(5,1_000_000)
assert [2*p*40_000 for p in [maximum_p,F(1,100000),F(5,100000),F(1,10000)]] == [F(2,5),F(4,5),4,8]
official(17,'ア')
print('PASS Q17: millisecond to microsecond conversion and two accesses')

# Q22: all four original half-adder gate combinations, all input pairs.
valid = [True]*4
for a,b in product([0,1],repeat=2):
    candidates = [(a&b,a^b),(a|b,a^b),(a|b,a&b),(a&b,a|b)]
    expected = divmod(a+b,2)
    valid = [old and value==expected for old,value in zip(valid,candidates)]
assert valid == [True,False,False,False]
official(22,'ア')
print('PASS Q22: four gate diagrams across all four half-adder inputs')

# Q23: active-high LED1=bit3, LED2=bit6; all 256 initial port values.
operations = [lambda x:x&0x08,lambda x:x|0x08,
              lambda x:x&0x48,lambda x:x|0x48]
valid = [all((fn(x)&8)==8 and (fn(x)&64)==(x&64)
             for x in range(256)) for fn in operations]
assert valid == [False,True,False,False]
assert all((x|8)&~8 == x&~8 for x in range(256))
official(23,'イ')
print('PASS Q23: all four masks on all 256 port values, LED2 preserved')

# Q26: whole rows, not just IDs, define equality for the relation union.
R = {('0001','a',100),('0002','b',200),('0003','d',300)}
S = {('0001','a',100),('0002','a',200)}
X = {('0001','a',100),('0002','a',200),('0002','b',200),('0003','d',300)}
assert R|S == X and len(R&S)==1 and len(R-S)==2
assert len(list(product(R,S))) == 6
official(26,'エ')
print('PASS Q26: original union has four rows including two different ID0002 rows')

# Q29: execute the four relational operations on the original three rows.
db=sqlite3.connect(':memory:')
db.execute('CREATE TABLE sales (department TEXT, first INTEGER, second INTEGER)')
db.executemany('INSERT INTO sales VALUES (?,?,?)', [('D01',1000,4000),('D02',2000,5000),('D03',3000,8000)])
first="SELECT department, '第1期' AS period, first AS amount FROM sales"
second="SELECT department, '第2期' AS period, second AS amount FROM sales"
intersection=db.execute(first+' INTERSECT '+second).fetchall()
union=db.execute(first+' UNION '+second+' ORDER BY department,period').fetchall()
cross=db.execute("SELECT a.department,'第1期',a.first FROM sales a CROSS JOIN sales t").fetchall()
joined=db.execute("SELECT a.department,'第1期',a.first FROM sales a JOIN sales t ON a.department=t.department").fetchall()
assert len(intersection)==0 and len(cross)==9 and len(joined)==3
assert union==[('D01','第1期',1000),('D01','第2期',4000),('D02','第1期',2000),('D02','第2期',5000),('D03','第1期',3000),('D03','第2期',8000)]
official(29,'イ')
print('PASS Q29: actual SQL operations, all six output values and three wrong row counts')

# Q35: preserve network bits and set host bits to one. Exhaust every bit.
for ip,mask in product([0,1],repeat=2):
    expected = ip if mask else 1
    assert (ip | (1-mask)) == expected
assert (0xc0000207 | (0xffffffff ^ 0xffffff00)) == 0xc00002ff
official(35,'エ')
print('PASS Q35: all four IP/mask bit cases and an explicit /24 example')

# Q52: activities lie on edges; all upstream activities imply FS constraints.
base = [(0,1,'A'),(0,2,'B'),(1,3,'C'),(2,4,'D'),
        (3,5,'E'),(4,6,'F'),(5,7,'G'),(6,7,'H')]
def prerequisites(edges):
    @lru_cache(None)
    def upstream(v):
        out=set()
        for u,w,label in edges:
            if w==v:
                out.update(upstream(u))
                if label:out.add(label)
        return frozenset(out)
    return {label:set(upstream(u)) for u,_,label in edges if label}
reference = {'A':set(),'B':set(),'C':{'A'},'D':{'B'},
             'E':{'A','C'},'F':{'A','B','D'},
             'G':{'A','C','E'},'H':{'A','B','D','F'}}
variants = [base,base+[(1,4,None)],
            base+[(1,4,None),(1,6,None)],base+[(1,6,None)]]
assert [prerequisites(v)==reference for v in variants] == [False,True,True,False]
# ウ adds the redundant A→H dummy: it does not create different effective FS
# constraints. イ represents the extra A→F relation with only one dummy.
assert len(variants[1]) < len(variants[2])
official(52,'イ')
print('PASS Q52: all four dependency graphs; ウ is redundant, not a changed dependency')

# Q55: at a mid-month date the six-month cutoff lies in a seventh month.
def month_offset(d,months):
    ordinal = d.year*12+d.month-1+months
    year,month = divmod(ordinal,12);month+=1
    return date(year,month,min(d.day,calendar.monthrange(year,month)[1]))
for current in [date(2021,10,15),date(2021,10,31),date(2022,3,30)]:
    cutoff=month_offset(current,-6)
    retained_months=current.year*12+current.month-(cutoff.year*12+cutoff.month)+1
    assert retained_months==7
assert month_offset(date(2021,10,31),-6) == date(2021,4,30)
assert 7*2 == 14
official(55,'ウ')
print('PASS Q55: seven overlapping monthly full/differential tape pairs')

# Q56: 42 weekly shifts cannot fit into 8 people at 5 shifts each.
assert 7*3*2==42 and 8*5<42<=9*5
# A feasible weekly 21-shift roster, two people each, every person 4 or 5 times.
roster = [(2*i%9,(2*i+1)%9) for i in range(21)]
counts = [sum(person in shift for shift in roster) for person in range(9)]
assert sum(counts)==42 and max(counts)==5 and min(counts)==4
official(56,'イ')
print('PASS Q56: capacity lower bound and a feasible nine-person weekly roster')

# Q64: 10 people, five years, one avoided 50万円 recruitment per year.
savings = (10+12)*10*5 + 50*5
costs = (8+1)*10 + (2+6)*10*5
assert (savings,costs,savings-costs)==(1350,490,860)
official(64,'イ')
print('PASS Q64: initial versus annual costs, recruitment counted per year')

# Q68: original A..F table, scale costs rise, joint costs save money.
A,B,C,D,E,F_cost = 1500,3300,500,1100,1900,4200
assert B>2*A and D>2*C
assert E<A+C and F_cost<B+D
assert (A+C-E,B+D-F_cost)==(100,200)
official(68,'イ')
print('PASS Q68: both scale comparisons and both joint-production comparisons')

# Q75: the minimum in each row, not just the low-growth column.
rows = [[20,10,15],[25,5,20],[30,20,5],[40,10,-10]]
worst = list(map(min,rows))
assert worst==[10,5,5,-10] and worst.index(max(worst))==0
official(75,'ア')
print('PASS Q75: all twelve table cells and maximin row minima')

# Q76: all feasible integer production combinations, plus continuous bound.
feasible=[(x,y) for x in range(41) for y in range(31)
          if 3*x+2*y<=120 and x+2*y<=60]
best=max(x+y for x,y in feasible)
assert best==45 and [(x,y) for x,y in feasible if x+y==best]==[(30,15)]
# Summing one quarter of the two resource inequalities gives x+y<=45.
assert (F(3,4)+F(1,4),F(2,4)+F(2,4))==(1,1)
assert F(120,4)+F(60,4)==45
official(76,'ウ')
print('PASS Q76: exhaustive feasible outputs and continuous optimum bound')

# Q77: fixed costs do not change with sales; contribution rates are 50%,20%.
rates=[F(1,2),F(1,5)];fixed=[400,100]
break_even=[f/r for f,r in zip(fixed,rates)]
assert break_even==[800,500]
profits=[[sales*r-f for sales in [900,1000,1100]]
         for r,f in zip(rates,fixed)]
assert profits==[[50,100,150],[80,100,120]]
official(77,'ア')
print('PASS Q77: margins, break-even and profits at three sales levels')
print('PASS 19 independently transcribed numerical/diagram groups')
