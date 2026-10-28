from fractions import Fraction
from math import factorial
from pathlib import Path
import json
out={}
# Divisibility equivalence independently enumerated; positive n and different positive keys.
assert all((a%n==b%n)==((a-b)%n==0) for n in range(1,20) for a in range(1,50) for b in range(1,50) if a!=b)
out['hash']='n=1..19,a,b=1..49で剰余一致と差の倍数の同値を全数検算'
A=[3,5,9,6,1,2];states=[]
for end in range(len(A)-1,0,-1):
 for j in range(end):
  if A[j]>A[j+1]:A[j],A[j+1]=A[j+1],A[j]
 states.append(A.copy())
assert states[:2]==[[3,5,6,1,2,9],[3,5,1,2,6,9]]
out['bubble_states']=states
# The second original diagram traverses from the right.
A=[3,5,9,6,1,2];left_states=[]
for i in range(len(A)-1):
 for j in range(len(A)-1,i,-1):
  if A[j]<A[j-1]:A[j],A[j-1]=A[j-1],A[j]
 left_states.append(A.copy())
assert A==[1,2,3,5,6,9]
out['reverse_bubble']=left_states
# Trace every flowchart termination candidate with safety limit.
conditions=[lambda n,m:n<m,lambda n,m:n>m-1,lambda n,m:n>m,lambda n,m:n>m+1]
def run(m,condition):
 x=1;n=1
 for _ in range(100):
  x*=n;n+=1
  if condition(n,m):return x
 return 'no termination in 100 loops'
out['termination_M3']=[run(3,c) for c in conditions]
assert all(run(m,conditions[2])==factorial(m) for m in range(1,20))
out['factorial']='M=1..19でウの流れ図結果が階乗に一致'
out['successful_search_average']={n:Fraction(sum(range(1,n+1)),n).__str__() for n in [1,2,5,10]}
# A genuine list reconstruction, followed by insertion and reverse traversal.
elem={1:'A',2:'F',3:'D',4:'B',5:'E',6:'C'}
nxt={1:4,2:0,3:5,4:3,5:2};prv={1:0,2:5,3:4,4:1,5:3}
nxt[6]=nxt[3];prv[6]=3;nxt[3]=6;prv[5]=6
order=[];i=1
while i:order.append(elem[i]);i=nxt[i]
reverse=[];i=2
while i:reverse.append(elem[i]);i=prv[i]
assert order==['A','B','D','C','E','F'] and reverse==list(reversed(order))
out['doubly_linked']={'next6':nxt[6],'prev6':prv[6],'order':order,'reverse':reverse}
out['CPI']=Fraction(125,100).__str__()
out['HPC']={'total_cores':8*1000*4,'nodes':8*1000*4//16,'TFLOPS':8*1000*4*20//1000}
out['availability_example']=str(Fraction(100,102))
Path(__file__).with_suffix('.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
