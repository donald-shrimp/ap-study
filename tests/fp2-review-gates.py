"""Regression checks for unreviewed deliveries and missing/misordered figures."""
import copy,importlib.util,json,subprocess,tempfile
from pathlib import Path
from fp2_fixtures import prepare,builder,write,ROOT
spec=importlib.util.spec_from_file_location('fp2_check',ROOT/'tools/check-fp2-delivery.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
def rejected(action,label):
 try:action()
 except (ValueError,AssertionError,subprocess.CalledProcessError):return
 raise AssertionError(label+' was accepted')
with tempfile.TemporaryDirectory(prefix='fp2-review-gates-') as d:
 root=Path(d);cfg,normal,cases=prepare(root);base=root/'content/fp2';read=lambda name:json.loads((base/name).read_text());qr=read('question-reviews.json');cr=read('practical-reviews.json')
 assert delivery.check(root,True)['questions']==1
 for mode in ['topic-guide','omitted','mixed']:
  bad=copy.deepcopy(normal);bad['enrichment']='topic-guide';bad['choiceReasons']=[];bad['explanation']=''
  if mode=='omitted':bad.pop('enrichment')
  if mode=='mixed':bad['id']='unreviewed-extra';raw=[normal,bad];reviews=qr
  else:raw=[bad];reviews=[]
  write(base/'questions.json',raw);write(base/'question-reviews.json',reviews)
  rejected(lambda:delivery.check(root,True),'reviewed delivery '+mode)
  rejected(lambda:builder.compile_qualification(root,'fp2'),'publication '+mode)
 write(base/'questions.json',[normal]);write(base/'question-reviews.json',[])
 rejected(lambda:delivery.check(root,True),'reviewed label without review evidence')
 write(base/'question-reviews.json',qr)
 figure=cases[0]['bodyFigures'][0]
 variants=[('missing',[{**figure,'anchor':'ABSENT'}],cases[0]['body']),('empty',[{**figure,'anchor':''}],cases[0]['body']),('ambiguous',[figure],cases[0]['body']+'[fig]'),('reversed',[{**figure,'anchor':'[one]'},{**figure,'anchor':'[two]'}],'[two] then [one]'),('duplicate',[figure,figure],cases[0]['body'])]
 for label,figures,body in variants:
  bad=copy.deepcopy(cases);bad[0]['bodyFigures']=figures;bad[0]['body']=body;reviews=copy.deepcopy(cr);reviews[0]['canonicalCaseSHA256']=builder.diagnostic_digest(bad[0])
  write(base/'practical-cases.json',bad);write(base/'practical-reviews.json',reviews)
  rejected(lambda:delivery.check(root,True),'reviewed figure '+label)
  rejected(lambda:builder.compile_qualification(root,'fp2'),'published figure '+label)
  draft=copy.deepcopy(bad)
  for c in draft:c['status']='draft'
  draft_q=copy.deepcopy(normal);draft_q['enrichment']='draft';write(base/'questions.json',[draft_q]);write(base/'practical-cases.json',draft)
  rejected(lambda:delivery.check(root),'draft figure '+label)
  write(base/'questions.json',[normal])
 good=copy.deepcopy(cases);good[0]['body']='Before [one] between [two] after';good[0]['bodyFigures']=[{**figure,'anchor':'[one]'},{**figure,'anchor':'[two]'}];reviews=copy.deepcopy(cr);reviews[0]['canonicalCaseSHA256']=builder.diagnostic_digest(good[0]);write(base/'practical-cases.json',good);write(base/'practical-reviews.json',reviews)
 assert delivery.check(root,True)['cases']==2;builder.compile_qualification(root,'fp2')
print('PASS reviewed-only checks and publishing reject topic-guide, omitted status, mixed rows and missing evidence / draft, reviewed and publishing reject bad figure anchors / valid multi-figure case accepted')
