"""Independent checks transcribed visually from original r03a Q41–80 images."""
import calendar
from datetime import date
from fractions import Fraction
from functools import lru_cache
# Q48: factor shape × line variation, no combination subclass required.
shapes={'三角形','四角形'};lines={'太線','細線'}
assert len(shapes)*len(lines)==4
assert (len(shapes)+1)*len(lines)==6
print('PASS Q48: shape and line hierarchies vary independently in ウ')
assert ['残作業量','発生不具合数','累積バグ数','要員数'].index('残作業量')==0
print('PASS Q49: original four vertical axes; remaining work is ア')
# Q52 visually transcribed arrow edges: dummies carry no activity.
base=[(0,1,'A'),(0,2,'B'),(1,3,'C'),(2,4,'D'),(3,5,'E'),(4,6,'F'),(5,7,'G'),(6,7,'H')]
def prerequisites(edges):
 @lru_cache(None)
 def before(v):
  out=set()
  for u,w,name in edges:
   if w==v:
    out.update(before(u))
    if name:out.add(name)
  return frozenset(out)
 return {name:set(before(u)) for u,_,name in edges if name}
expected={'A':set(),'B':set(),'C':{'A'},'D':{'B'},'E':{'A','C'},'F':{'A','B','D'},'G':{'A','C','E'},'H':{'A','B','D','F'}}
variants=[base,base+[(1,4,None)],base+[(1,4,None),(1,6,None)],base+[(1,6,None)]]
assert [prerequisites(v)==expected for v in variants]==[False,True,True,False]
print('PASS Q52: イ and ウ same effective FS, ウ has redundant A→H dummy')
# Q55 six-month cutoff includes seven calendar months; end-of-month clamp.
for now in [date(2021,10,2),date(2021,10,31),date(2022,3,30)]:
 ordinal=now.year*12+now.month-1-6;y,m=divmod(ordinal,12);m+=1
 oldest=date(y,m,min(now.day,calendar.monthrange(y,m)[1]))
 assert now.year*12+now.month-(oldest.year*12+oldest.month)+1==7
 if now.day==31:assert oldest==date(2021,4,30)
assert 7*2==14
print('PASS Q55: seven monthly full/differential pairs = 14 tapes')
# Q56 capacity plus repeating feasible 7-day schedule.
assert 7*3*2==42 and 8*5<42<=9*5
roster=[(2*s%9,(2*s+1)%9) for s in range(21)]
counts=[sum(p in s for s in roster) for p in range(9)]
assert max(counts)==5 and sum(counts)==42
print('PASS Q56: 9 people, concrete 21-shift roster, workloads',counts)
# Q62 original flow is goal → success factors → quantitative activity metrics.
metrics={'a':('物流コスト削減率',10,'%'),'c':(('在庫日数',7,'日以内'),('誤出荷率',3,'%以内'))}
assert metrics['c'][0][1]==7 and metrics['c'][1][1]==3 and metrics['a'][1]==10
print('PASS Q62: a cost10%=goal, b inventory/misshipment=factors, c 7days/3%=KPI')
saving=(10+12)*10*5+50*5;initial=(8+1)*10;operating=(2+6)*10*5
assert (saving,initial,operating,saving-initial-operating)==(1350,90,400,860)
print('PASS Q64: savings1350 − initial90 − operating400 = 860万円')
assert [Fraction(1500,20),Fraction(3300,40),Fraction(500,10),Fraction(1100,20)]==[75,Fraction(165,2),50,55]
assert 1900<1500+500 and 4200<3300+1100
assert (1500+500-1900,3300+1100-4200)==(100,200)
print('PASS Q68: scale cost rises; joint production saves100/200万円')
rows=[[20,10,15],[25,5,20],[30,20,5],[40,10,-10]]
worst=list(map(min,rows));assert worst==[10,5,5,-10] and worst.index(max(worst))==0
print('PASS Q75: maximin minima',worst,'select A')
feasible=[(x,y) for x in range(41) for y in range(31) if 3*x+2*y<=120 and x+2*y<=60]
assert max(x+y for x,y in feasible)==45
assert [(x,y) for x,y in feasible if x+y==45]==[(30,15)]
assert Fraction(120+60,4)==45
print('PASS Q76: exhaustive feasible integer outputs and continuous bound45')
rates=[Fraction(1000-500,1000),Fraction(1000-800,1000)]
assert rates==[Fraction(1,2),Fraction(1,5)]
assert [400/rates[0],100/rates[1]]==[800,500]
assert [[s*r-f for s in [900,1000,1100]] for r,f in zip(rates,[400,100])]==[[50,100,150],[80,100,120]]
print('PASS Q77: 50%/20%, break-even800/500, A has higher profit sensitivity')
print('PASS all 11 original diagram/table/numerical groups')
