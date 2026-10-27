"""Independent supplemental arithmetic, representation and truth-table checks."""
from fractions import Fraction as F
from itertools import product,combinations
import json,pathlib
out={}
ratio=(F(40,100)/(1-F(40,100)))/(F(25,100)/(1-F(25,100)));assert ratio==2
out['r06a-q1']=str(ratio)
steps=[str(F(1,2**n)) for n in range(1,11)];assert F(1,512)>=F(1,1000)>F(1,1024)
out['r07h-q2']=dict(halfWidths=steps,count=10)
assert F(1,2)/(1-F(1,2))==1
out['r07a-q2']='rho/(1-rho)>=1 <=> rho>=1/2'
stack=[]
for t in [16,8,4,2,'-','*','+']:
 if isinstance(t,int):stack.append(t)
 else:
  r=stack.pop();l=stack.pop();stack.append({'-':lambda:l-r,'*':lambda:l*r,'+':lambda:l+r}[t]())
assert stack==[32];out['r05a-q3']=stack
prob=F(90,100)*F(89,99)*F(88,98);assert prob==F(178,245);out['r04a-q3']=str(prob)
# Count fraction bits after normalizing exact positive binary rationals.
def precision(v):
 e=0
 while v>=2:v/=2;e+=1
 while v<1:v*=2;e-=1
 frac=v-1;bits=0
 while frac:
  frac*=2;frac-=int(frac);bits+=1
 return e,bits
vals={'A intermediate':F(1,4),'A final':F(129,4),'B final':F(257,8),'C intermediate':F(515,16),'D intermediate':F(511,16)}
out['r04h-q1']={k:{'exact':str(v),'exponent':precision(v)[0],'fractionBits':precision(v)[1]} for k,v in vals.items()}
assert [precision(vals[k])[1] for k in vals]==[0,7,8,9,8]
# Syndrome of every data-bit error and ambiguity of two opposite diagonals.
def syndrome(coords):
 rows=[0]*4;cols=[0]*4
 for r,c in coords:rows[r]^=1;cols[c]^=1
 return tuple(rows+cols)
singles=[syndrome([t]) for t in product(range(4),repeat=2)]
assert len(set(singles))==16
assert syndrome([(0,0),(1,1)])==syndrome([(0,1),(1,0)])
assert syndrome([(0,0),(0,1),(1,0),(1,1)])==(0,)*8
out['parity']={'uniqueSingleSyndromes':len(set(singles)),'twoDiagonalErrorAmbiguous':True,'rectangleUndetected':True}
# Evaluate all expressions for element membership in A and B.
rows=[]
for a,b in product([False,True],repeat=2):
 target=not a and not b
 choices=[not a and not b,((not a)or(not b))and not(a and b),(not a)or(not b),not(a and b)]
 rows.append(dict(A=a,B=b,target=target,choices=choices))
assert [all(row['choices'][i]==row['target'] for row in rows) for i in range(4)]==[True,False,False,False]
out['r04h-q2']=rows
assert 40000*16//8//1000==80;out['r03h-q3']='80 kbyte'
vals=[int(not ((not x) and (not y))) for x,y in product([0,1],repeat=2)];assert vals==[0,1,1,1]
out['r05h-q21']=vals
json.dump(out,open(pathlib.Path(__file__).with_suffix('.json'),'w'),ensure_ascii=False,indent=2)
print('Independent exact arithmetic, 16 parity syndromes, set and NAND truth tables: passed')
