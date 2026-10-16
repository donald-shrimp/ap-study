from pathlib import Path
from fractions import Fraction
import json
D=Path(__file__).parent
# Input transcribed independently from official p14 Figure 1; no author program used.
board=[int(v) for row in ['201090700','040200300','500008029','090670200','600305004','007049010','760900003','009006040','004010600'] for v in row]
initial=board[:];calls=0

def ok(n,x):
    row=x//9*9;column=x%9;frame=x-((x//9*9)%27)-x%3
    return n not in board[row:row+9] and all(board[column+9*i]!=n for i in range(9)) and all(board[frame+9*i+j]!=n for i in range(3) for j in range(3))

def solve(x):
    global calls
    calls+=1
    if x>80:return True
    if board[x]!=0:return solve(x+1)
    for n in range(1,10):
        if ok(n,x):
            board[x]=n
            if solve(x+1):return True
            board[x]=0
    return False
assert solve(0)
expected=['281493765','946257381','573168429','495671238','618325974','327849516','762984153','159736842','834512697']
rows=[''.join(map(str,board[i:i+9])) for i in range(0,81,9)]
assert rows==expected
assert all(set(board[i:i+9])==set(range(1,10)) for i in range(0,81,9))
assert all(set(board[j::9])==set(range(1,10)) for j in range(9))
assert all(x==0 or x==board[i] for i,x in enumerate(initial))
checks=[]
for x in range(81):
    row=x//9*9;column=x%9;frame=x-((x//9*9)%27)-x%3
    direct=(x//9//3)*27+(x%9//3)*3
    assert frame==direct
    assert ((x//9*9)%27)==9*((x//9)%3)
    checks.append(dict(x=x,row=row,column=column,frame=frame))
# Counterexample to keeping modified Z on backtracking: a candidate removed by one trial
# must become available for its sibling trial; save/restore returns exact original matrix.
z=[[1]*10 for _ in range(81)];saved=[r[:] for r in z];z[1][1]=0
assert saved[1][1]==1 and z[1][1]==0
z=[r[:] for r in saved];assert z==saved
profits=[[640,880,1200],[720,800,960],[740,780,800]]
mins=[min(r) for r in profits];assert mins==[640,720,740]
shares=[[(41,22),(37,28)],[(36,24),(35,30)]]
nash=[(a+1,b+1) for a in range(2) for b in range(2) if shares[a][b][0]>=shares[1-a][b][0] and shares[a][b][1]>=shares[a][1-b][1]]
assert nash==[(1,2)]
reg=1000//200;ref=4000//500;paas=(reg+ref)*200;cpu=1000*50+4000*10;faas=cpu*Fraction(2,100)
assert (reg,ref,paas,cpu,faas)==(5,8,2600,90000,1800)
out={'reviewer':'/root/author_2021_autumn','ap-r04h-pm2':{'minimumProfits':mins,'maximinSelected':3,'NashEquilibria':nash,'deviationAtA1B2':{'A':[37,35],'B':[28,22]}},'ap-r04h-pm3':{'independentInput':initial,'solvedRows':rows,'matchesOfficialQuestionFigure2':True,'recursiveCalls':calls,'all81FrameIndices':checks,'ZSaveRestoreCheck':True},'ap-r04h-pm4':{'registrationInstances':reg,'referenceInstances':ref,'PaaSYen':paas,'cpuMilliseconds':cpu,'requestCount':5000,'requestCharge':0,'FaaSYen':int(faas),'intervalBoundary':'20 minutes excluded; interval must be strictly less than 20.'}}
(D/'a21-independent-calculations.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Independent game/Sudoku81/fee verification passed',calls)
