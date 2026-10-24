"""Recalculate numeric answers from inspected official operands; compare all 68 official fields."""
from decimal import Decimal as D, ROUND_DOWN, ROUND_HALF_UP
import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]);cases=json.loads((root/'content/fp2/practical-cases.json').read_text())
def trunc(v,n=0):return D(v).quantize(D(1).scaleb(-n),rounding=ROUND_DOWN)
def rnd(v,n=0):return D(v).quantize(D(1).scaleb(-n),rounding=ROUND_HALF_UP)
# Transcribed directly from the independently opened official answer page (not read from authored JSON).
answers={1:['×','×','○','○'],2:['4'],3:['1'],4:['0.435'],5:['35.71','1.35'],6:['1490000'],7:['×','×','×','○'],8:['168'],9:['1'],10:['×','×','○','○'],11:['63'],12:['2110'],13:['19','572','5220'],14:['3'],15:['×','○','○','×'],16:['1'],17:['6570'],18:['680000'],19:['140'],20:['3'],21:['250'],22:['×','×','○','○'],23:['2','5','1'],24:['2100'],25:['151'],26:['2'],27:['○','○','×','×'],28:['156'],29:['647'],30:['3'],31:['2460800'],32:['1133000'],33:['5650'],34:['3585'],35:['2'],36:['×','×','×','○'],37:['4'],38:['1'],39:['2'],40:['×','×','○']}
# unit / decimal places / original rounding instruction / independently calculated result / derivation
calcs={
4:[('％',3,'truncate',trunc((D('.5')+(D(100)-D('100.5'))/8)/D('100.5')*100,3),'(0.50+(100-100.50)/8)/100.50*100')],
5:[('％',2,'halfUp',rnd(D(200)/560*100,2),'200/560*100'),('倍',2,'halfUp',rnd(D(3460)/2560,2),'3460/2560')],
6:[('円',0,'none',5300000-3500000-200000-100000-10000,'5300000-3500000-(200000+100000+10000); exclude special distribution')],
8:[('㎡',0,'none',D(240)*D('.7'),'240*(.60+.10)')],
11:[('万円',0,'none',144-10-15-8-1-12-5-30,'144-(10+15+8+1+12+5+30); exclude loan principal40')],
12:[('万円',0,'none',D(5600)-D(5600)*D('.05')-210-3000,'5600-5600*.05-210-3000')],
13:[('万円',0,'none',D(14)*D('.5')+18*D('.5')+10*D('.3'),'14*.5+18*.5+10*.3'),('万円',0,'none',500+40*D('.5')+20+44*D('.5')+10,'500+40*.5+20+44*.5+10'),('万円',0,'none',200+2500+500+2000+20,'200+2500+500+2000+20')],
17:[('円',0,'none',D(1800)*D('.5')/100*730,'1800*.5/100*730')],
18:[('円',0,'none',(96-18-10)*10000,'(96-18-10)*10000; survivor pension exempt, oldage below110 deduction')],
19:[('万円',0,'none',D(2200-(800+70*(36-20)))/2,'(2200-(800+70*(36-20)))/2; 35y10m ->36y')],
21:[('万円',0,'none',1560-480-640-180-10,'1560-480-640-180-10')],
24:[('万円',0,'none',800+300+1000+1200-500*2-200,'800+300+1000+1200-500*2-200; taxable price before basic exemption')],
25:[('万円',0,'none',D(2800-2000-110)*D('.4')-125,'(2800-2000-110)*.4-125')],
28:[('万円',0,'halfUp',rnd(D(150)*D('1.01')**4),'(100+50)*1.01^4 -> nearest万円')],
29:[('万円',0,'halfUp',rnd(D(593)*D('1.01')+48),'593*1.01+48 -> nearest万円')],
31:[('円',0,'none',400000*D('6.152'),'400000*6.152; supplied annuity future coefficient')],
32:[('円',0,'none',5500000*D('.206'),'5500000*.206; supplied capital recovery coefficient')],
33:[('万円',0,'none',1500+300+450+200+120+400+280+120+2400+720+250+100-1120-70,'2450+920+3120+350-1190')],
34:[('万円',0,'floor',trunc(trunc(D(8500000)*D('.2')/12)/3951*100),'floor_yen(8500000*.20/12)/3951*100 -> floor万円')]
}
output=[];numeric_count=0
for n,c in enumerate(cases,1):
 fs=[f for i in c['items'] for f in i['fields']];got=[f['referenceAnswers'][0] for f in fs]
 assert got==answers[n],(n,got,answers[n])
 row={'caseId':c['id'],'officialAnswerPage':1,'answers':answers[n],'allFieldsMatchOfficial':True,'calculations':[]}
 nums=[f for f in fs if f['type']=='numeric']; assert len(nums)==len(calcs.get(n,[]))
 for f,(unit,places,rounding,result,formula) in zip(nums,calcs.get(n,[])):
  assert D(f['referenceAnswers'][0])==D(result),(n,result)
  assert f['numeric']=={'unit':unit,'decimalPlaces':places,'rounding':rounding},(n,f['numeric'],unit,places,rounding)
  numeric_count+=1;row['calculations'].append({'fieldId':f['id'],'unit':unit,'decimalPlaces':places,'rounding':rounding,'formula':formula,'result':str(result)})
 output.append(row)
assert len(cases)==40 and sum(len(a) for a in answers.values())==68 and numeric_count==22
print(json.dumps({'officialFields':68,'numericRecalculations':22,'choiceFields':46,'cases':output,'additionalChoiceCalculations':{'q03':'1000000*1*3.3%=33000yen; 9600-9000=600special','q14':'32000+35000+50000=117000yen =>3','q20':'400000*.1+130000*.05=46500yen =>3','q23':'A share1/2 reserve1/4;B0 =>2,5,1','q26':'300*500*1.00*.70=105000thousand yen =>2','q35':'21124151-20324815=799336<=800000; +67626=866962>800000 =>12months =>2'}},ensure_ascii=False,indent=2))
