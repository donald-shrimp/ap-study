"""原本画像から転記した定数だけによる独立検算。教材への依存なし。"""
import itertools,json
results={}
# Q47: columns 1 ready, 2 high, 3 low, 4 paused; empty means unchanged.
table={'m1':{1:2,3:2,4:2},'m2':{2:3,3:4,4:1},'hot':{2:3,3:4},'cold':{3:2,4:3}}
s=1;trace=[s]
for e in ['m1','m1','hot','m2','cold','m2']:
 s=table[e].get(s,s);trace.append(s)
assert trace==[1,2,2,3,4,3,4];results['q47']={'trace':trace,'answer':'エ'}
# Q48 exhaust all choices; find smallest covering subset.
paths=list(itertools.product(range(3),range(2),range(3)))
universe={(stage,branch) for stage,count in enumerate([3,2,3]) for branch in range(count)}
for k in range(1,5):
 found=next((p for p in itertools.combinations(paths,k) if {(i,b) for path in p for i,b in enumerate(path)}==universe),None)
 if found:break
assert k==3;results['q48']={'minimum':k,'witness':found,'allPaths':len(paths)}
# Q52 original matrix and exact four mutations.
m=[list('R C A C C'.split()),list('R R I A C'.split()),list('R I A I I'.split()),list('R A C A I'.split())]
opts=[(0,0,'I'),(1,1,'A'),(2,2,'C'),(3,3,'R')];valid=[]
for row,col,value in opts:
 a=[r.copy() for r in m];a[row][col]=value;valid.append(all(r.count('R')>=1 and r.count('A')==1 for r in a))
assert valid==[False,False,False,True];results['q52']={'validChoices':valid}
# Q53 generic DAG earliest finish; second diagram dummy points E2-end to E1-end.
def finish(edges):
 times={0:0};pending=edges.copy()
 while pending:
  nodes={v for u,v,d in pending}
  ready=[v for v in nodes if all(u in times for u,w,d in edges if w==v)]
  assert ready
  for v in ready:times[v]=max(times[u]+d for u,w,d in edges if w==v)
  pending=[e for e in pending if e[1] not in ready]
 return times
old=[(0,1,5),(1,2,8),(1,3,7),(2,4,7),(2,5,9),(3,5,5),(4,7,7),(5,6,4),(6,7,2)]
new=[(0,1,5),(1,2,8),(1,3,7),(2,4,7),(2,8,3),(2,9,4),(9,8,0),(8,5,2),(3,5,5),(4,7,7),(5,6,4),(6,7,2)]
a,b=finish(old),finish(new);assert(a[7],b[7],a[7]-b[7])==(28,27,1)
results['q53']={'oldNodeTimes':a,'newNodeTimes':b,'shortening':a[7]-b[7]}
# Q55 unordered pairs, 0.5 hours each.
pairs=list(itertools.combinations(range(16),2));hours=len(pairs)*.5
assert len(pairs)==120 and hours==60;results['q55']={'pairs':len(pairs),'hours':hours}
print(json.dumps({'targets':5,'passed':5,'results':results},ensure_ascii=False,indent=2))
