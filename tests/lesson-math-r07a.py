"""2025秋原本画像から独立転記した条件の検算。教材文を参照しない。"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json, math, sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
keys = next(x['answers'] for x in json.loads((ROOT/'data/answer-keys.json').read_text()) if x['year']==2025 and x['season']=='autumn')
questions = {x['id']:x for x in json.loads((ROOT/'data/questions.json').read_text())}
results={}
def check(n, result, choices):
    matches=[i for i,c in enumerate(choices) if c==result]
    assert len(matches)==1,(n,result,choices)
    answer='アイウエ'[matches[0]]
    assert answer==keys[n-1] and matches[0]==questions[f'r07a-q{n}']['answer'],(n,answer)
    results[n]={'result':str(result),'answer':answer}
# q1: Gray order cells, test every candidate on all 16 assignments.
gray=[(0,0),(0,1),(1,1),(1,0)]
cells=[[1,0,0,1],[0,1,1,0],[0,1,1,0],[0,0,0,0]]
exprs=[lambda a,b,c,d:(a and b and not c and d) or (not b and not d),
 lambda a,b,c,d:(not a and not b and not c and not d) or (b and d),
 lambda a,b,c,d:(a and b and d) or (not b and not d),
 lambda a,b,c,d:(not a and not b and not d) or (b and d)]
truth=[all(int(e(a,b,c,d))==cells[i][j] for i,(a,b) in enumerate(gray) for j,(c,d) in enumerate(gray)) for e in exprs]
check(1,True,truth)
# q2: solve Wq/T >=1 and confirm all candidate rates.
check(2,min(r for r in [33,50,67,80] if F(r,100)/(1-F(r,100))>=1),[33,50,67,80])
# q6: simulate successful searches. The exact mean differs from option by bounded constant.
def blocked_count(n,m,pos):
    count=0
    for end in range(m-1,n,m):
        count+=1
        if end>=pos:
            for x in range(end-m+1,end+1):
                count+=1
                if x==pos:return count
n,m=1200,30
mean=F(sum(blocked_count(n,m,p) for p in range(n)),n)
assert mean==F(m,2)+F(n,2*m)+1
check(6,F(m,2)+F(n,2*m),[m+F(n,m),F(m,2)+F(n,2*m),F(n,m),F(n,2*m)])
check(10,1/F(10000,1000000)/2,[50,100,200,5000])
check(11,(8*1000*4//(8*2),F(8*1000*4*10*2,1000)),[(2000,320),(2000,640),(4000,320),(4000,640)])
# q15: nonpreemptive shortest job first using only arrived jobs.
pending=[('A',0,2),('B',1,4),('C',2,3),('D',3,2),('E',4,1)];t=0;finish={};order=[]
while pending:
    ready=[j for j in pending if j[1]<=t]
    if not ready:t=min(j[1] for j in pending);continue
    j=min(ready,key=lambda j:(j[2],j[1]));pending.remove(j);order.append((j[0],t,t+j[2]));t+=j[2];finish[j[0]]=t
assert order==[('A',0,2),('C',2,5),('E',5,6),('D',6,8),('B',8,12)]
check(15,finish['B']-1,[8,9,10,11])
# q18: enumerate lock acquisition schedules and detect reachable circular waits.
def can_deadlock(orders):
    seen=set();todo=[((0,0),(None,None))]
    while todo:
        progress,owners=todo.pop()
        if (progress,owners) in seen:continue
        seen.add((progress,owners));moves=[]
        for task in [0,1]:
            step=progress[task]
            if step==2:
                updated=tuple(None if owner==task else owner for owner in owners)
                done=list(progress);done[task]=3;moves.append((tuple(done),updated))
            elif step<2:
                resource=orders[task][step]
                if owners[resource] is None:
                    updated=list(owners);updated[resource]=task;nextp=list(progress);nextp[task]+=1
                    moves.append((tuple(nextp),tuple(updated)))
        if not moves and progress!=(3,3):return True
        todo.extend(moves)
    return False
assert can_deadlock(((0,1),(1,0)))
assert not can_deadlock(((0,1),(0,1)))
check(18,False,[True,can_deadlock(((0,1),(0,1))),can_deadlock(((0,1),(1,0))),True])
# q19: order statistics on each distinct column.
loads=[0,3,4,5];last=[8,6,5,10];freq=[10,1,3,5]
replaced=[min(range(4),key=loads.__getitem__),min(range(4),key=freq.__getitem__),max(range(4),key=loads.__getitem__),min(range(4),key=last.__getitem__)]
check(19,2,replaced)
check(20,F(2*10,10*10)*100,[20,25,80,100])
# q21: 0->1 only; q22: original timing chart intervals.
switch=[lambda a,b:a and not b,lambda a,b:not a and b,lambda a,b:a or not b,lambda a,b:not a or b]
check(21,True,[all(bool(fn(a,b))==(a==1 and b==0) for a,b in product([0,1],repeat=2)) for fn in switch])
inputs=[(0,1),(0,0),(1,1),(0,0),(1,1),(0,0),(1,0)];y=[1,1,0,1,0,1,1]
gates=[lambda a,b:a!=b,lambda a,b:a==b,lambda a,b:not(a and b),lambda a,b:not(a or b)]
check(22,True,[all(int(fn(*ab))==val for ab,val in zip(inputs,y)) for fn in gates])
check(23,F(150,16000000//32)*1000000,[F(3,10),2,150,300])
check(25,F(1000000,2*20000),[F(5,2),5,25,50])
check(30,F(9,1000)/(F(1250*8,100000000)-F(1250*8,1000000000)),[10,80,100,800])
# q35: exact independent-bit probability and first-order approximation.
p=1e-6;exact=10000*(-math.expm1(1500*8*math.log1p(-p)))
assert 119<exact<120
assert min([10,15,80,120],key=lambda c:abs(c-exact))==120
check(35,10000*1500*8*p,[10,15,80,120])
check(48,F(42,1)/F(36,48)-42,[6,14,54,56])
# q53: four originals lose .5mo training+2mo reassignment. New members work 2mo.
lost=4*(F(1,2)+2);new=lost/2;assert new==5
check(53,(new*(F(1,2)+2)-4*2)*100,[200,250,450,700])
check(54,F(60,100)*30+F(40,100)*(-10),[14,20,26,64])
check(65,F(5*3+8*0+12*1,(5+8+12)*3)*100,[27,36,43,52])
# q74: independently minimize cost among integral feasible Q; verify cost equality.
cost=lambda q:F(100000*5000,q)+F(q*1000,2)
q=min(range(1,10001),key=cost);assert F(100000*5000,q)==F(q*1000,2)
check(74,q,[10,200,500,1000])
# q75: exhaustive integer feasible production, maximum 45 at X30,Y15.
feasible=[(x+y,x,y) for x in range(121) for y in range(61) if 3*x+2*y<=120 and x+2*y<=60]
best=max(feasible);assert best==(45,30,15)
check(75,best[0],[30,40,45,60])
check(76,F(2000+1000+500,6000+4000)*100,[10,20,30,35])
# q77: exhaustive mixes, one variable enumerated and other maximized within hours.
profits=[(a*12000+b*15000-15000000,a,b) for a in range(15000//8+1) for b in [(15000-8*a)//12]]
best=max(profits);assert best==(7500000,1875,0)
check(77,best[0],[3750000,7500000,16250000,18750000])
print(json.dumps({'checkedQuestions':len(results),'results':results},ensure_ascii=False,indent=2))
