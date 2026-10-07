"""Curated mobile materials must reference the unchanged official-source corpus."""
import json,copy,importlib.util,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
cfg=json.loads((ROOT/'content/ap/qualification.json').read_text());raw=json.loads((ROOT/cfg['questionSource']).read_text());questions=[builder.normalize(q,cfg) for q in raw]
context=json.loads((ROOT/cfg['studyContextSource']).read_text());deck=json.loads((ROOT/cfg['flashcardSource']).read_text())
assert len(context['items'])==30 and sum(i['mode']=='paperless' for i in context['items'])==24 and len(deck['cards'])==20
assert len({c['id'] for c in deck['cards']})==20
with tempfile.TemporaryDirectory() as name:
 root=Path(name);out=root/'out';out.mkdir()
 for key in ['questionSource','studyContextSource','flashcardSource']:
  dest=root/cfg[key];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/cfg[key],dest)
 result=builder.compile_learning_tools(root,cfg,questions,out);assert result['flashcards']['count']==20 and result['studyContext']['paperless']==24
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
 invalid=copy.deepcopy(deck);invalid['cards'].append(invalid['cards'][0]);rejects('flashcardSource',invalid)
print('PASS 24 paperless / 6 desk / 20 authored cards / source hashes / stale source and malformed references rejected')
