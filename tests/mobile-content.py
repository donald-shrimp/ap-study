"""Curated mobile materials must reference the unchanged official-source corpus."""
import json,copy,importlib.util,shutil,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
cfg=json.loads((ROOT/'content/ap/qualification.json').read_text());raw=json.loads((ROOT/cfg['questionSource']).read_text());questions=[builder.normalize(q,cfg) for q in raw]
context=json.loads((ROOT/cfg['studyContextSource']).read_text());deck=json.loads((ROOT/cfg['flashcardSource']).read_text())
paperless=sum(i['mode']=='paperless' for i in context['items'])
assert len(deck['cards'])==20
completed=set(context['completedExamIds'])
assert {q['id'] for q in raw if q['id'].split('-q')[0] in completed}=={i['questionId'] for i in context['items']}
assert completed=={q['id'].split('-q')[0] for q in raw}
assert len(context['items'])==len(raw)==800
assert len({c['id'] for c in deck['cards']})==20
assert len({i['questionId'] for i in context['items']})==800
by_id={i['questionId']:i for i in context['items']}
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
review_dir=ROOT/'content/ap/study-context-reviews'
root_review=json.loads((review_dir/'root.json').read_text())
assert root_review['combinedContextSha256']==digest(context)
assert root_review['preservedR07hItemsSha256']==digest(sorted((i for i in context['items'] if i['questionId'].startswith('r07h-q')),key=lambda i:int(i['questionId'].split('-q')[1])))
for filename,sha in root_review['preservedContentSha256'].items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==sha,filename
for path in review_dir.glob('r*.json'):
 if path.stem=='root':continue
 review=json.loads(path.read_text());exam=review['examId']
 published=sorted((i for i in context['items'] if i['questionId'].startswith(exam+'-q')),key=lambda i:int(i['questionId'].split('-q')[1]))
 assert len(published)==len(review['authorItems'])==80
 assert review['publishedItemsSha256']==digest(published),exam
 assert review['publishedCounts']=={'paperless':sum(i['mode']=='paperless' for i in published),'desk':sum(i['mode']=='desk' for i in published)}
 for image in review['rootAudit']:
  assert hashlib.sha256((ROOT/image['imagePath']).read_bytes()).hexdigest()==image['imageSha256']
 for change in review['rootChanges']:assert by_id[change['questionId']]['mode']==change['to']
assert len(list(review_dir.glob('r0*.json')))==9

assert all(by_id[f'r07h-q{n}']['mode']=='paperless' for n in [7,16,25,26,35,43,47,52,54,56,66,69,74])
assert all(by_id[f'r07h-q{n}']['mode']=='desk' for n in [2,8,11,12,13,21,31,34,55,64,76,77])
with tempfile.TemporaryDirectory() as name:
 root=Path(name);out=root/'out';out.mkdir()
 for key in ['questionSource','studyContextSource','flashcardSource']:
  dest=root/cfg[key];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/cfg[key],dest)
 result=builder.compile_learning_tools(root,cfg,questions,out);assert result['flashcards']['count']==20 and result['studyContext']['paperless']==paperless
 def rejects(key,value):
  path=root/cfg[key];original=path.read_text();path.write_text(json.dumps(value,ensure_ascii=False))
  try:
   try:builder.compile_learning_tools(root,cfg,questions,out)
   except ValueError:pass
   else:raise AssertionError('Invalid sidecar accepted')
  finally:path.write_text(original)
 invalid=copy.deepcopy(context);invalid['items'][0]['sourceHash']='0'*64;rejects('studyContextSource',invalid)
 invalid=copy.deepcopy(context);invalid['items'][0]=None;rejects('studyContextSource',invalid)
 invalid=copy.deepcopy(deck);invalid['cards'][0]['relatedQuestionIds']=['missing'];rejects('flashcardSource',invalid)
 invalid=copy.deepcopy(deck);invalid['cards'][0]['topicId']='database';rejects('flashcardSource',invalid)
 invalid=copy.deepcopy(deck);invalid['cards'][0]['relatedQuestionIds']=[{}];rejects('flashcardSource',invalid)
 invalid=copy.deepcopy(context);invalid['items'].pop();rejects('studyContextSource',invalid)
 invalid=copy.deepcopy(context);invalid['completedExamIds']=['missing'];rejects('studyContextSource',invalid)
 invalid=copy.deepcopy(deck);invalid['cards'].append(invalid['cards'][0]);rejects('flashcardSource',invalid)
print(f'PASS {paperless} paperless / {800-paperless} desk / all 10 exams / 20 authored cards / source hashes / malformed references rejected')
