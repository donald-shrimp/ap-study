import json,pathlib,sqlite3
out={};INF=10**9;n=5
edges=[(1,2,10),(1,3,16),(2,3,4),(2,4,3),(3,4,2),(3,5,3),(4,5,6)]
e=[[INF]*(n+1)for _ in range(n+1)]
for a,b,w in edges:e[a][b]=e[b][a]=w
d=[INF]*(n+1);d[1]=0;done=set();via=[0]*(n+1);trace=[]
while True:
 cur=min((v for v in range(1,n+1) if v not in done),key=lambda v:d[v]);done.add(cur);trace.append([cur,d[cur]])
 if cur==5:break
 for k in range(1,n+1):
  if d[cur]+e[cur][k]<d[k] and k not in done:via[k]=cur;d[k]=d[cur]+e[cur][k]
rev=[5]
while rev[-1]!=1:rev.append(via[rev[-1]])
assert trace==[[1,0],[2,10],[4,13],[3,14],[5,17]] and rev==[5,3,2,1]
out['pm3']={'edges':edges,'trace':trace,'reversePath':rev,'minimumInsertionLine':25,'alsoWorksButNotMinimum':26}
a=800/4;b=1200*(10000/40000)+(300+200)*(10000/20000);assert(a,b)==(200,550)
out['pm4']={'transferMs':a,'serverProcessingMs':b,'totalMs':300+a+b+500}
amount=10000*60*500/1000000;assert amount==300;out['pm5']={'weatherMBytesPerHour':amount,'sshRule':4,'httpsRule':7}
# Reload occurs between countdown ticks; 320 decrements cover 10 ms.
assert 320/32000==.01
samples=[1,1,0,0,0,0,0,0,0,0,1,0,1,1,1,1,1,1,1];labels=list('アイウエオカキクケコサシスセソタチツテ');state=1;last=None;run=0;events=[]
for lab,value in zip(labels,samples):
 run=run+1 if value==last else 1;last=value
 if run>=4 and state!=value:state=value;events.append([lab,value])
assert events==[['カ',0],['タ',1]];out['pm7']={'counterInitial':320,'sensorSamples':dict(zip(labels,samples)),'debouncedEvents':events}
pathlib.Path(__file__).with_suffix('.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
