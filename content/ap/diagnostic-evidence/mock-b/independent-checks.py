import json,itertools,sqlite3,hashlib,re,subprocess,argparse
from pathlib import Path
R=Path(__file__).parent
parser=argparse.ArgumentParser(description='Independent mock B calculations and completed-object/image fingerprints')
parser.add_argument('--root',type=Path,default=Path('/workspace/ap-study'))
parser.add_argument('--questions',type=Path,default=R/'corrected-questions.json')
parser.add_argument('--pdf-dir',type=Path,default=Path('/workspace/research/ap-five-years'))
parser.add_argument('--out',type=Path,default=R/'independent-checks.json')
args=parser.parse_args();B=args.root
out={}
def check(k,value,expected):
 assert value==expected,(k,value,expected)
 out[k]={'actual':value,'expected':expected,'passed':True}
# Stack evaluation checks expression syntax and operation order, not answer labels.
def postfix(expr,vals):
 stack=[]
 for t in expr.split():
  if t in vals:stack.append(vals[t])
  else:
   if len(stack)<2:return None
   b=stack.pop();a=stack.pop();stack.append(a+b if t=='＋' else a*b)
 return stack[0] if len(stack)==1 else None
check('q3-all-options',[postfix(s,dict(A=3,B=5,C=7)) for s in ['A B C × ＋','A B ＋ C ×','× ＋ A B C','A B C ＋ ×']],[38,56,None,36])
check('q5-replacement-valid',[all(x<v for x in [18,20,22] if x!=v) and all(x>v for x in [26,28,30] if x!=v) for v in [18,26,20,28]],[False,True,False,False])
check('q6-remainders',[x%13 for x in [35,12,23,48,52]],[9,12,10,9,0])
check('q10-weighted',round(.9/20+.1,6),.145)
check('q10-sequential',round(1/20+.1,6),.15)
check('q10-original',round(.95/30+.05,6),.081667)
r=.6
check('q14-three-systems',[round(1-(1-r)**2,6),round(r*(1-(1-r)**2),6),round(1-(1-r*r)**2,6)],[.84,.504,.5904])
check('q15-capacities',[100_000_000//2_000_000,80_000_000//(100_000*8)],[50,100])
check('q15-original',[100_000_000//1_000_000,80_000_000//(200_000*8)],[100,50])
# Execute all four SQL candidates with reviewer-transcribed rendered table.
c=sqlite3.connect(':memory:');c.execute('CREATE TABLE 成績(学生番号 TEXT,実施回 INT,得点 INT)')
c.executemany('INSERT INTO 成績 VALUES(?,?,?)',[('S01',2,65),('S01',8,75),('S02',1,88),('S02',6,81),('S03',4,72),('S03',10,86),('S03',13,92),('S04',7,98)])
base=c.execute('SELECT 学生番号,実施回,得点 FROM 成績 a WHERE 実施回=(SELECT MAX(実施回) FROM 成績 b WHERE a.学生番号=b.学生番号) ORDER BY 学生番号').fetchall()
clauses=['PARTITION BY 学生番号 ORDER BY 得点 DESC','ORDER BY 学生番号,実施回 DESC','PARTITION BY 学生番号 ORDER BY 実施回 DESC','PARTITION BY 学生番号 ORDER BY 実施回 ASC']
results=[c.execute('SELECT 学生番号,実施回,得点 FROM (SELECT *,ROW_NUMBER() OVER('+s+') n FROM 成績) WHERE n=1 ORDER BY 学生番号').fetchall() for s in clauses]
check('q30-option-equivalence',[x==base for x in results],[False,False,True,False]);out['q30-rows']={'expectedQuery':base,'fourCandidates':results}
check('q32-times',[16/(s*.8) for s in [10,2,1,4]],[2.,10.,20.,5.])
check('q32-binary-MB-minimum',min(s for s in [10,2,1,4] if (2*2**20*8)/(s*10**6*.8)<=6),4)
check('q35-hosts',2**16-2,65534)
for fee,expected,label in [(350,[690,640,450,400],'derived'),(700,[340,640,100,400],'original')]:
 res=[]
 for workers,external in [(4,True),(4,False),(5,True),(5,False)]:
  internal=7000-(2000 if external else 0)
  res.append((5-workers)*600+(workers*1800-internal)*20/100-(fee if external else 0))
 check('q64-'+label,res,expected)
times={'a':{'b':4,'c':2,'d':4},'b':{'a':2,'c':2,'d':4},'c':{'a':6,'b':4,'d':4},'d':{'a':8,'b':6,'c':4}}
orders=[(''.join(p),sum(times[x][y] for x,y in zip(p,p[1:]))) for p in itertools.permutations('abcd')]
check('q72-optimal',[list(t) for t in orders if t[1]==min(v for _,v in orders)],[['bacd',8]]);out['q72-all24']=orders
for demand,Astock,astock,bstock,expected,label in [(400,80,120,250,1230,'derived'),(300,100,100,300,600,'original')]:
 anew=max(0,demand-Astock);subnew=max(0,3*anew-astock)
 check('q73-'+label,max(0,anew*2+subnew-bstock),expected)
check('q73-all-choices',[1230==v for v in [1350,1480,1630,1230]],[False,False,False,True])
for matrix,expected,label in [([[(30,20),(35,15)],[(45,25),(40,10)]],[[1,0]],'derived'),([[(40,20),(50,30)],[(30,10),(25,25)]],[[0,1]],'original')]:
 cells=[]
 for i,j in itertools.product(range(2),repeat=2):
  valid=matrix[i][j][0]>=matrix[1-i][j][0] and matrix[i][j][1]>=matrix[i][1-j][1]
  if valid:cells.append([i,j])
 check('q75-'+label,cells,expected)
for sales,variables,fixed,expected,label in [(1200,[600,960],[450,90],[[.5,900.,150],[.2,450.,150]],'derived'),(1000,[500,800],[400,100],[[.5,800.,100],[.2,500.,100]],'original')]:
 check('q77-'+label,[[(sales-v)/sales,f/((sales-v)/sales),sales-v-f] for v,f in zip(variables,fixed)],expected)
# Official PDFs verified independently against source ledger and all 80 extracted keys.
sources=json.loads((B/'data/sources.json').read_text()); key=next(x for x in json.loads((B/'data/answer-keys.json').read_text()) if x['year']==2024 and x['season']=='autumn')
pdfs=[]
for s in sources:
 if s['year']==2024 and s['season']=='autumn':
  p=args.pdf_dir/s['filename'];h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==s['sha256']
  pdfs.append({'kind':s['kind'],'path':str(p),'url':s['url'],'sha256':h,'matchesSourcesLedger':True})
  if s['kind']=='answer':
   extracted=subprocess.check_output(['pdftotext','-layout',str(p),'-']).decode();(args.out.parent/'official-answer-extracted.txt').write_text(extracted)
   pairs={int(n):a for n,a in re.findall(r'問\s*(\d+)\s+([アイウエ])',extracted)}
   check('official-all80',[pairs[n] for n in range(1,81)],key['answers']);assert h==key['sha256']
out['pdfChecks']=pdfs

# Frozen reviewed fingerprints make this a reproducible check against supplied corpus.
REVIEWED_MANIFEST={'ap-mock-b-q2': {'sha256': 'cad3335a6573cf8a15b80334bc1cef5d3eaef33c4cc4f68917de35ec1780534b', 'derivedImages': []}, 'ap-mock-b-q3': {'sha256': 'fc0a422607ef9cd6dc2d4b220ebc60f7be328731fad0d2a7d324e7c5c793e928', 'derivedImages': []}, 'ap-mock-b-q4': {'sha256': '129f8fb9761b96d294cc3173faa59b00a9f845dd22bdbebfb628149c3e16bac6', 'derivedImages': []}, 'ap-mock-b-q5': {'sha256': 'f58d9dfe799f235973c95836661f09cc216e85eace2f585435a39979a0c72be7', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q5-tree.svg', 'sha256': 'f2f123450bf39fb9f745743c360be18669e723054b0ba7ca2cfa09e873c518f7'}]}, 'ap-mock-b-q6': {'sha256': '00032efe18f2483e8ab80a50dc02f3bc329d203fa73c18acd901f73f7a4eabbe', 'derivedImages': []}, 'ap-mock-b-q7': {'sha256': '6492650f86257a33372d2a7bf92247a5ebb6534d9844c980b160b9b881bec39e', 'derivedImages': []}, 'ap-mock-b-q8': {'sha256': 'db8687c968cb45a4c194668aca7ca701bfcb7fcf5a6cf3782e97620e1781e4f1', 'derivedImages': []}, 'ap-mock-b-q9': {'sha256': 'bbb44d20974c88d3e357f94e32c2a72077cc3089b8ae4e8117ea0f160c5a3d40', 'derivedImages': []}, 'ap-mock-b-q10': {'sha256': 'f8643dbce79bcf86659b4f40faf50499b10c3106add7afdd68bb55c83263768b', 'derivedImages': []}, 'ap-mock-b-q11': {'sha256': '13f6432f82d31c40c0843b0dc56476d318bdf49c87bd4b651b9b4782b50c99ff', 'derivedImages': []}, 'ap-mock-b-q12': {'sha256': 'fbd8dcc5dc2f5abd8455b88b3eb745406ffa145f1d80da1d86512cbb4ff9b262', 'derivedImages': []}, 'ap-mock-b-q13': {'sha256': '8dfaa12ae2499ce6f9ab729bace192dfcb60d0baa8d4f56ba398134e47bca3b8', 'derivedImages': []}, 'ap-mock-b-q14': {'sha256': '65952f4aee272bd9b3f170fd198bb8cca24736c4875a142eb8b5aabbf7a3828f', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q14-systems.webp', 'sha256': '761597d4d34d36d07619ad07bcf1933a27383973766cfae3a99ac27ff43e2fc9'}]}, 'ap-mock-b-q15': {'sha256': 'b7f74bcdfcb9cf0a1a28055071524616a2b74e6cf067d4215593ce62b46a26c2', 'derivedImages': []}, 'ap-mock-b-q16': {'sha256': 'dd34c3ecef8e2c246dfa5cde03d3dc3c79d4e9814641261bc87032c530179737', 'derivedImages': []}, 'ap-mock-b-q17': {'sha256': '6ef1c1e4103b48db5e278de8bb8cac9bf7da079c51ccefe92cead16f31ff3b6c', 'derivedImages': []}, 'ap-mock-b-q18': {'sha256': '8c9cbe7d8bd3478bcb9b36b524809ffad72336a1b08cb47146ed8ddf691ec771', 'derivedImages': []}, 'ap-mock-b-q19': {'sha256': '76aad6d8ab5269eeb8cf1052c73f9159c6919b9947c64d3a60f4ec09199e3ebb', 'derivedImages': []}, 'ap-mock-b-q20': {'sha256': 'd343ad0426b26a87908e83d2e25e0fc455988b6a2b8b9a9326d6430af07370e7', 'derivedImages': []}, 'ap-mock-b-q22': {'sha256': '7546e0616258dd6e497f02e7773ec120174c2b694ba87526cfdff30ceb6639da', 'derivedImages': []}, 'ap-mock-b-q23': {'sha256': '4a2b549039ccdb65a4345907c4e5541788e67bbc021760c73d7af1bdb2af20cf', 'derivedImages': []}, 'ap-mock-b-q24': {'sha256': 'ce64ec33b8c7427ced45be4c46f57bdb84f4468e7f4f4580046d6ae332eb69a1', 'derivedImages': []}, 'ap-mock-b-q25': {'sha256': '1935eacf8c09aa9ee2ab02363caaec8ea37eda9711ddc122f85162a63e0b625c', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q25-accordion.svg', 'sha256': '19d46fbc9a8c66a08e699f47c1d71920894da749cde9ae27f6f2c6e3088756b3'}]}, 'ap-mock-b-q27': {'sha256': '182ba5b652f78656d157d1dbae9bb99220430e8c7a4bf0df9669d81134005891', 'derivedImages': []}, 'ap-mock-b-q28': {'sha256': '54b9c56989d855ad34003145df4f90bd610ae45aa6c9a6b3bf3deb5bed600e11', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q28-tables.svg', 'sha256': '8d373159bc7a4e61d66815d5437ea6a8417cefab2e265b6857950dc04dcdc731'}]}, 'ap-mock-b-q29': {'sha256': 'bec1d61c64425bcfd625b4aea508da578d75ca12107d99df4b938327e7301531', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q29-objects.svg', 'sha256': '701360fcfb5b9465dcd2a11d505652ab62b9c443cb8ce76686abd2d77509d107'}, {'path': 'assets/questions/diagnostic/mock-b-q29-choice-0.svg', 'sha256': '961f9d101ca492736f5640fe91e5971b3aeedfafdb1f8e869b41f9edf27c08af'}, {'path': 'assets/questions/diagnostic/mock-b-q29-choice-1.svg', 'sha256': 'aac35066582e8c664b9f12b3943e245f31412dd18e5513f70baea3586b921de2'}, {'path': 'assets/questions/diagnostic/mock-b-q29-choice-2.svg', 'sha256': '77983c3728c833b786d80de2724220484ca4ff555f1e7c4772d938eb1b7eac17'}, {'path': 'assets/questions/diagnostic/mock-b-q29-choice-3.svg', 'sha256': 'c9e7173d2bab42e5128482d8904eaa3cc483a61e83631a85229d43ff1cb33e38'}]}, 'ap-mock-b-q30': {'sha256': '314457f94987499c8a0d79ad3c4db1b94a34300eafe93b8baa78e14a6fe5ba93', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q30-table.svg', 'sha256': '85bedcf08a8030d7502a88adb48f5c526f93d6eedd7763df28895d88b0a9327f'}]}, 'ap-mock-b-q31': {'sha256': '4b4081e20ed22c170e127a7c6a0bd634f505763dfaba4bc28bce8cfaa00f5b36', 'derivedImages': []}, 'ap-mock-b-q32': {'sha256': '488b6d605779fb861eeeda2e6cba855580140d442a5d7979228932253c692da4', 'derivedImages': []}, 'ap-mock-b-q33': {'sha256': '06c1520e6ad44802bf12557ea924c35aadbf08ec5eda22fc2a248894f1bbcac8', 'derivedImages': []}, 'ap-mock-b-q34': {'sha256': '66d7a4ba4420f4a947b67fe6ffd10be2cdc3c0fa5955482e777cde7e5d4b7d61', 'derivedImages': []}, 'ap-mock-b-q35': {'sha256': '3c25ffbbd9203d0c5cfc162e3d179efbe1385c891f995d3008a67b550a0321ef', 'derivedImages': []}, 'ap-mock-b-q36': {'sha256': '644334182ee6ba0123e3d1b98e6eb043ddebb8d91602b9654dd77e3fb258d295', 'derivedImages': []}, 'ap-mock-b-q37': {'sha256': 'b0eccf69a0cd4beed523c37571794fb16b66efc9307ba6e32c2562fa274ef5ef', 'derivedImages': []}, 'ap-mock-b-q38': {'sha256': '4427e5672dc61165305272907ad79c4de526c34d087d90a680df73a22d9e50d6', 'derivedImages': []}, 'ap-mock-b-q39': {'sha256': '6c2937a9816a4375416bf74adbc96f0cc5cf8f83408bd449991c8f0898907930', 'derivedImages': []}, 'ap-mock-b-q40': {'sha256': '8453bdc6cc471c61493cec0b8350c23b1cb8a43d77d287f05a27551afc7c362b', 'derivedImages': []}, 'ap-mock-b-q41': {'sha256': '103706e872dd5acac5ce2e5c9cc4fe7ab7cf9578fdf26aa0d6fafded3a9b7af2', 'derivedImages': []}, 'ap-mock-b-q42': {'sha256': '94b5c46fa58b2dfae413a19a641632394c1360b726cd5111541d2fa55f7b9bbd', 'derivedImages': []}, 'ap-mock-b-q43': {'sha256': '1c0f42c89da6e2c2bfac8989391fd4c21788f96dbd18b3f57c0b5ecdd44a54bb', 'derivedImages': []}, 'ap-mock-b-q44': {'sha256': 'ffa070056a0342bb316f3cc059ef2c31b43842d40374753970a16b76a3da7490', 'derivedImages': []}, 'ap-mock-b-q45': {'sha256': '93b1adc0cd2e048ec7790e5c78e874754dc91d25e96e504c2e72aa7521b4ae0e', 'derivedImages': []}, 'ap-mock-b-q46': {'sha256': '3537508b891066a4862884c5af6c45ddefae3788df4d34e28f2bd706be8bccac', 'derivedImages': []}, 'ap-mock-b-q47': {'sha256': 'dc970a905fe5f07026ff10325f49409e7ca2475b21df81b8d88c1aa9dcc00f3f', 'derivedImages': []}, 'ap-mock-b-q48': {'sha256': '6b53ca2db17fcb5d9e77bda2c4bbc614a95576d27c324c491461d3d558edd4d5', 'derivedImages': []}, 'ap-mock-b-q49': {'sha256': 'b15e092247de2662f3d4f5ddbc719191957553f05e0e3586436456e4482d2b16', 'derivedImages': []}, 'ap-mock-b-q50': {'sha256': '4579a72b43d1ee0aa8e4ddfaee2f6fe97877e4a1429582b3c62841843ff75f66', 'derivedImages': []}, 'ap-mock-b-q51': {'sha256': 'edd2958168536a00a9471bcc19dcbc3d32ede1928512eac0b4224cfa6d3b1f08', 'derivedImages': []}, 'ap-mock-b-q52': {'sha256': '55edf18d0244afc4e71123b62d3fcb7906737ead8146ffb9c9297a15fc896814', 'derivedImages': []}, 'ap-mock-b-q53': {'sha256': 'dbf0fa64c0bc1893418cdfaf20a9a3609236c95a438d200aca5c857fbe0ba76d', 'derivedImages': []}, 'ap-mock-b-q54': {'sha256': 'eb84adcd0d0020c67d1a5f2b205f6b0b3bd98a4517c0b172f6665c386c334542', 'derivedImages': []}, 'ap-mock-b-q55': {'sha256': '7c0a81c7c8025c4b34f14b0194ee31939f46e27a63a1f7db0d7f101eeb203086', 'derivedImages': []}, 'ap-mock-b-q56': {'sha256': '727271cb6c24ae2d811a6e6a97f54e623fc65eaed07ec062984c452a7e62f1c3', 'derivedImages': []}, 'ap-mock-b-q57': {'sha256': 'ea86ae9537ed8529341912bbb0e20667b96e56e982c9f483fbd5ee49873d247d', 'derivedImages': []}, 'ap-mock-b-q58': {'sha256': 'e8edcd597cb894fa27b974a7a7715c03258dbdda0cbd860eb13de78afb045d45', 'derivedImages': []}, 'ap-mock-b-q59': {'sha256': 'ae08be2fb0fa14a2ee16bbdb73b24d07944d736c4d15b7429bc5b50f9d5c52c6', 'derivedImages': []}, 'ap-mock-b-q60': {'sha256': '0ffce9983aee9907b0d119f11c14f2c4a9d840c9227a87049991631405301405', 'derivedImages': []}, 'ap-mock-b-q61': {'sha256': '92961be4429bd749d8b47fb676aef5a7907b8b1dcc4014d459124ce66d8e13da', 'derivedImages': []}, 'ap-mock-b-q62': {'sha256': 'd7d6bf7b9add9ad4be8c7d66442ece87a624cfe971220c1ac142ee1dda58198f', 'derivedImages': []}, 'ap-mock-b-q63': {'sha256': '72bfdcf7e7d4dd635597690effc81ef8867362adde133dd407b030ee8a4d3398', 'derivedImages': []}, 'ap-mock-b-q64': {'sha256': '59187262934a8eb0c33cadebdea5828c3e090f8861aaeb46b9004cf8fcd601eb', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q64-scenarios.svg', 'sha256': 'ec519913b835e9ae83c988d6d127d166b73039e6b1285b6815de56973a788e4e'}]}, 'ap-mock-b-q65': {'sha256': 'a943fa8a24c1249ac6c5af4082a144b7a84351afee58be68bfd5edc485b3b5ef', 'derivedImages': []}, 'ap-mock-b-q66': {'sha256': 'b1067741aab70d50303d4dbe1d9969359b3f72e8f752ca4d4bc34f57a3463c7e', 'derivedImages': []}, 'ap-mock-b-q67': {'sha256': '979eae3b55babf9811584f76073c1ab68d5f6d2c42b5c46668ad3d3bff0feebe', 'derivedImages': []}, 'ap-mock-b-q68': {'sha256': '69a3096e3c91d6e61fa3b304838367bc8bb797d9e46138ea2b911273b94866e8', 'derivedImages': []}, 'ap-mock-b-q69': {'sha256': 'ac9c8b60814ccf89017dbf8740022777444a3218ec181c5a0367fe80658e66f0', 'derivedImages': []}, 'ap-mock-b-q70': {'sha256': '4d0b8c5b1eb5d6fd45c3c81e8908ba3208a3a31426c0bd457aba5c007d820e1d', 'derivedImages': []}, 'ap-mock-b-q71': {'sha256': '7b1796a355e0598f0a0964766b46c8362f093f68c7e62e952c4b98f5071caa29', 'derivedImages': []}, 'ap-mock-b-q72': {'sha256': '8c2ae053ef3e6293b42959f79dfbc0c0c1c50ff5e69400e952b0d2cb195bc625', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q72-setup.svg', 'sha256': '8299997b313bfa5a654f69f804c0b30c6812120faf3e406d1ebeea671fc929ed'}]}, 'ap-mock-b-q73': {'sha256': 'da301b27ef25513ff9c3eac33e887324ad862ffe4ce76f0c131a55675c46a089', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q73-bom.svg', 'sha256': 'b6348f42e3c48400aa7666ee21b1fa58defdc7803153cdb8ce0d1144a47fe32d'}]}, 'ap-mock-b-q74': {'sha256': 'ba991af11ad4b62e6daa3cb4545d676cf25eae00fb41b9ffad221437b0e2a8b2', 'derivedImages': []}, 'ap-mock-b-q75': {'sha256': '8fd4e6b554809cd109a71e1e42ab525df4467825efda787bf8117c89ac581ec7', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q75-payoffs.svg', 'sha256': '9fbf1b0795b0fbf9c5dc562541a4fae1fde9d4b3a27448c952463837ef34e5a1'}]}, 'ap-mock-b-q76': {'sha256': 'b18200881d072ce6351cdae7ae5a869460f389e3b9a335095f60ee95403c1e28', 'derivedImages': []}, 'ap-mock-b-q77': {'sha256': '79c6de7574d40ca410779c103a52d5de6f5ab8de2ce2c36a24a744f1dcc5db3f', 'derivedImages': [{'path': 'assets/questions/diagnostic/mock-b-q77-finance.svg', 'sha256': 'f5d107a3f7c3e8fc13bdd8f2776619edfa2868777c073093d59ea2f38b53050a'}]}, 'ap-mock-b-q78': {'sha256': '9a89a3bb42042762d7e0316dff6b51ddabc7424a45ac2cb763d5db56df860cd8', 'derivedImages': []}, 'ap-mock-b-q79': {'sha256': 'e3702ee7a9ae4ce8dfa23f659915d9152c03291598ca4383bccfb148e3ee868c', 'derivedImages': []}, 'ap-mock-b-q80': {'sha256': '1626d22b01eac70bab4f5592f7c52f6eab7383834ed1e72baf3126a9b00f18e9', 'derivedImages': []}}
qpath=args.questions if args.questions.is_absolute() else B/args.questions
corpus=json.loads(qpath.read_text());qs={q['id']:q for q in corpus if q['id'] in REVIEWED_MANIFEST}
assert len(qs)==77,'Missing one or more of the 77 reviewed mock B questions'
for qid,evidence in REVIEWED_MANIFEST.items():
 q=qs[qid];actual=hashlib.sha256(json.dumps(q,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
 assert actual==evidence['sha256'],('completed object changed',qid)
 for img in evidence['derivedImages']:
  assert hashlib.sha256((B/img['path']).read_bytes()).hexdigest()==img['sha256'],('figure changed',qid,img['path'])
 assert q['correctChoiceId'] in {c['id'] for c in q['choices']}
 assert not(q.get('stem') and q.get('sourceImages')),'Figure hidden by stem/sourceImages display contract'
out['completedCorpus']={'path':str(qpath),'questionCount':len(qs),'fullObjectFingerprintsMatch':True,'allDerivedImageFingerprintsMatch':True,'displayMetadataValid':True}
args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Independent numeric/SQL/24-order/game/PDF checks passed:',len(out))
