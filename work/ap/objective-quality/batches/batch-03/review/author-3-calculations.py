"""Author's supplemental enumeration; not independent approval."""
import itertools,json,pathlib
root=pathlib.Path(__file__).parent
out={}
# Read gate connections from the original figures before expressing them here.
triples=list(itertools.product((0,1),repeat=3))
majority=lambda a,b,c:int(a+b+c>=2)
funcs=[lambda a,b,c:(a&b)|(b&c)|(c&a),lambda a,b,c:(a^b)|(b^c)|(c^a),lambda a,b,c:1-((a|b)&(b|c)&(c|a)),lambda a,b,c:1-((a^b)&(b^c)&(c^a))]
out['r05a-q23']={'inputs':[''.join(map(str,t)) for t in triples],'expected':[majority(*t) for t in triples],'choices':[[f(*t) for t in triples] for f in funcs]}
assert [all(f(*t)==majority(*t) for t in triples) for f in funcs]==[True,False,False,False]
pairs=list(itertools.product((0,1),repeat=2))
f=[lambda x,y:(x&y)&((1-x)&(1-y)),lambda x,y:(x|y)|((1-x)|(1-y)),lambda x,y:1-((1-(x&y))&(1-((1-x)&(1-y)))),lambda x,y:1-((1-(x|y))|(1-((1-x)|(1-y))))]
out['r04a-q23']={'inputs':[''.join(map(str,t)) for t in pairs],'choices':[[g(*t) for t in pairs] for g in f]}
assert [all(g(x,y)==int(x==y) for x,y in pairs) for g in f]==[False,False,True,False]
out['r03a-q22']=[{'A':a,'B':b,'X':(a+b)//2,'Y':(a+b)%2} for a,b in pairs]
# Enumerate all legal push/pop histories, with A/B/C inputs fixed.
outputs={};histories=[]
def walk(i,stack,emitted,ops):
 if i==3 and not stack:
  outputs.setdefault(emitted,[]).append(ops);histories.append(ops);return
 if i<3:walk(i+1,stack+'ABC'[i],emitted,ops+'push'+'ABC'[i]+' ')
 if stack:walk(i,stack[:-1],emitted+stack[-1],ops+'pop'+stack[-1]+' ')
walk(0,'','','')
assert set(outputs)=={'ABC','ACB','BAC','BCA','CBA'}
assert len(histories)==5
out['r03h-q5']={'legalOperationHistories':len(histories),'outputs':outputs}
# Stable partitions specified by this question, rather than an exchange implementation.
a=[2,3,5,4,1];p=a[0];lo=[x for x in a[1:] if x<p];hi=[x for x in a[1:] if x>p]
first=lo+[p]+hi;q=hi[0];second=lo+[p]+[x for x in hi[1:] if x<q]+[q]+[x for x in hi[1:] if x>q]
assert first==second==[1,2,3,5,4]
out['r05h-q7']={'first':first,'second':second}
tree={'+':('A','÷'),'÷':('×','−'),'×':('B','C'),'−':('D','E')}
def traverse(n):
 if n not in tree:return n
 l,r=tree[n];return traverse(r)+traverse(l)+n
assert traverse('+')=='ED−CB×÷A+'
out['r06h-q6']={'rightLeftSelf':traverse('+')}
json.dump(out,open(root/'author-3-calculations.json','w'),ensure_ascii=False,indent=2)
print('circuit truth tables / stack histories / stable partitions / recursive output: all assertions passed')
