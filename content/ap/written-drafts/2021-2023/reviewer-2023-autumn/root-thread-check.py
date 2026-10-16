"""Independent Q8 DAG schedule calculation; official result was previously exposed."""
duration={1:100,2:10,3:100,4:150,5:200,6:50,7:10};parents={1:[],2:[1],3:[1],4:[3],5:[3],6:[4,5],7:[6]};end={};path={}
for n in range(1,8):
 last=max(parents[n],key=lambda p:end[p]) if parents[n] else None
 end[n]=(end[last] if last else 0)+duration[n];path[n]=(path[last] if last else [])+[n]
assert end=={1:100,2:110,3:200,4:350,5:400,6:450,7:460}
assert path[7]==[1,3,5,6,7]
print('PASS independent DAG completion times',end,'critical path',path[7],'total',end[7],'ms')
