"""Independent computations from visually read official r03h questions; no lessons imports."""
import itertools,math,json
out={}
out['q1']=[int(not(a^b)) for a,b in itertools.product([0,1],repeat=2)]
assert out['q1']==[1,0,0,1]
out['q3_kbyte']=40000*16/8/1000;assert out['q3_kbyte']==80
seqs=set()
def stack_paths(pending,stack,taken):
 if not pending and not stack:seqs.add(taken);return
 if pending:stack_paths(pending[1:],stack+[pending[0]],taken)
 if stack:stack_paths(pending,stack[:-1],taken+stack[-1])
stack_paths(list('ABC'),[],'');out['q5']=sorted(seqs)
assert seqs=={'ABC','ACB','BAC','BCA','CBA'}
levels=[[i for i in range(1,8) if int(math.log2(i))==d] for d in range(3)]
out['q6_levels']=levels;assert levels==[[1],[2,3],[4,5,6,7]]
avg=sum(t*f for t,f in [(10,.5),(40,.3),(40,.2)])
out['q9']={'average_ns':avg,'MIPS':1000/avg};assert 1000/avg==40
f=lambda x:1-(1-x*x)**2
out['q14']={str(x):f(x) for x in [0,.5,.8,1]}
assert f(.5)<.5 and f(.8)>.8
root=(math.sqrt(5)-1)/2;assert abs(f(root)-root)<1e-12
out['q14_cross']=root
end=0; schedule=[]
for name,arrival,duration in [('A',0,5),('B',2,6),('C',3,3)]:
 start=max(end,arrival);end=start+duration;schedule.append([name,start,end,end-arrival])
out['q16']=schedule;assert schedule[-1][-1]==11
# H-bridge: upper-left/lower-left/upper-right/lower-right; 1=conducting.
choices=[(0,0,0,0),(0,1,0,1),(0,1,1,0),(1,0,0,1)]
def direction(c):
 ul,ll,ur,lr=c
 if ur and ll and not ul and not lr:return 'reverse'
 if ul and lr and not ur and not ll:return 'forward'
 return 'not_driven'
out['q23']=[direction(c) for c in choices];assert out['q23']==['not_driven','not_driven','reverse','forward']
x,y=0,1;trace=[]
for s in [0,1]:
 for _ in range(4):x=int(not(s and y));y=int(not(1 and x))
 trace.append([s,x,y])
out['q25']=trace;assert trace==[[0,1,0],[1,1,0]]
# 32-bit sample verifies every candidate; original specifies abstract a,m only.
a=0xc0a8010a;m=0xffffff00;mask=0xffffffff
vals=[((~a)&mask)&m,((~a)&mask)|m,a&((~m)&mask),a|((~m)&mask)]
out['q34_sample']=[hex(v) for v in vals];assert vals[2]==10 and all(v!=10 for j,v in enumerate(vals) if j!=2)
print(json.dumps(out,ensure_ascii=False,indent=2));print('PASS: 10 question computations (q1,q3,q5,q6,q9,q14,q16,q23,q25,q34)')
