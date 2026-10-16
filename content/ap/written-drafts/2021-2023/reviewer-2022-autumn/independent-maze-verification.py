import json
obstacles={(2,4),(2,2),(3,3),(4,3),(3,5),(4,5),(4,1)}
def run(ob):
 path=[];events=[];solutions=[];visited=set()
 def visit(x,y):
  if path:events.append({'kind':'forward','to':[x,y],'depth':len(path)+1})
  path.append((x,y));visited.add((x,y))
  if(x,y)==(5,5):solutions.append({'path':path.copy(),'event':len(events),'visited':len(visited)})
  else:
   for nx,ny in [(x,y+1),(x+1,y),(x,y-1),(x-1,y)]:
    if 1<=nx<=5 and 1<=ny<=5 and(nx,ny) not in ob and(nx,ny) not in path:visit(nx,ny)
  path.pop()
  if path:events.append({'kind':'back','to':list(path[-1]),'depth':len(path)})
 visit(1,1)
 return events,solutions
es,ss=run(obstacles);es2,ss2=run(obstacles-{(3,3)})
print('first unvisited=',25-len(obstacles)-ss[0]['visited'],'13thdepth=',es[12]['depth'],'ss2=',len(ss2))
print('postfirst next forward=',next(x for x in es2[ss2[0]['event']:] if x['kind']=='forward'));start=next(i for i,x in enumerate(es2[ss2[0]['event']:],ss2[0]['event']) if x['kind']=='forward');end=ss2[1]['event'];print('moves nextcall to 2ndsol',end-start-1,'visits42=',sum(x['to']==[4,2] for x in es2[start+1:end]))
print(es2[ss2[0]['event']:ss2[1]['event']+1])

assert 25-len(obstacles)-ss[0]["visited"]==3
assert es[12]["depth"]==2
assert len(ss2)==4
assert es2[start]["to"]==[5,3]
assert end-start-1==22
assert sum(x["to"]==[4,2] for x in es2[start+1:end])==3
