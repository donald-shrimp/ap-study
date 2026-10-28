# Independent reviewer calculations; original diagrams transcribed by reviewer.
import itertools,json
from pathlib import Path
P=Path(__file__).parent
rows=[]
for a,b,c in itertools.product([0,1],repeat=3):
 pair_and=(a and b,b and c,c and a);pair_or=(a or b,b or c,c or a);pair_xor=(a^b,b^c,c^a)
 out=[int(any(pair_and)),int(any(pair_xor)),int(not all(pair_or)),int(not all(pair_xor))]
 assert out[0]==int(a+b+c>=2)
 rows.append({'ABC':[a,b,c],'a_i_u_e':out})
eq=[]
for x,y in itertools.product([0,1],repeat=2):
 out=[int((x and y) and (not x and not y)),int((x or y) or (not x or not y)),int(not((not(x and y)) and (not(not x and not y)))),int(not((not(x or y)) or (not(not x or not y))))]
 assert out==[0,1,int(x==y),x^y]
 assert ((x+y)//2,(x+y)%2)==(x&y,x^y)
 eq.append({'XY':[x,y],'a_i_u_e':out})
stack_outputs=set()
def stack(i,st,out):
 if len(out)==3:stack_outputs.add(out);return
 if i<3:stack(i+1,st+'ABC'[i],out)
 if st:stack(i,st[:-1],out+st[-1])
stack(0,'','');assert stack_outputs=={'ABC','ACB','BAC','BCA','CBA'}
def walk(t):
 if isinstance(t,str):return t
 v,l,r=t;return walk(r)+walk(l)+v
traversal=walk(('+','A',('÷',('×','B','C'),('−','D','E'))));assert traversal=='ED−CB×÷A+'
# AVL left-left rotation from original tree after insertion 1 then 0.
tree=(5,(3,(1,(0,None,None),(2,None,None)),(4,None,None)),(7,(6,None,None),None))
def check(t,low=-1,high=99):
 if t is None:return 0
 v,l,r=t;assert low<v<high
 a,b=check(l,low,v),check(r,v,high);assert abs(a-b)<=1;return 1+max(a,b)
check(tree)
# Two stable quicksort partitions, pivot2 then pivot3.
a=[2,3,5,4,1];p=a[0];left=[x for x in a[1:] if x<p];right=[x for x in a[1:] if x>p]
p2=right[0];second=left+[p]+[x for x in right[1:] if x<p2]+[p2]+[x for x in right[1:] if x>p2]
assert second==[1,2,3,5,4]
result={'majorityTruthTables':rows,'equalityTruthTables':eq,'stackOutputs':sorted(stack_outputs),'rightLeftPostorder':traversal,'avlFinalTree':tree,'quicksortSecondPartition':second}
(P/'reviewer-4-calculations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Independent truth tables, half-adder, stack enumeration, traversal, AVL balance/order, quicksort verified.')
