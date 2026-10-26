"""Check the PR48 final draft against its actual independent-review seals.

Pass a delivery created by tools/prepare-fp2-delivery.py. A reviewed projection
is checked in a temporary directory; this never promotes the authoring draft.
"""
import argparse, copy, hashlib, importlib.util, json, shutil, sys, tempfile
from pathlib import Path

WORK=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('checker',ROOT/'tools/check-fp2-delivery.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('delivery',type=Path)
args=parser.parse_args()
read=lambda p:json.loads(p.read_text())
digest=checker.builder.diagnostic_digest
qs=read(WORK/'questions.json');cases=read(WORK/'practical-cases.json')
obj=read(WORK/'review/objective-final-review.json')
pr=read(WORK/'review/practical-final-review.json')
assert digest(qs)==obj['questionSetDraftSha256']
assert digest(cases)==pr['draftSetCanonicalSha256']
assert len(qs)==60 and sum(len(q['choices']) for q in qs)==240
assert sum(len(q['hints']) for q in qs)==120
assert len(cases)==40 and sum(len(i['fields']) for c in cases for i in c['items'])==68
assert all(q['enrichment']=='draft' for q in qs) and all(c['status']=='draft' for c in cases)
assert obj['officialAnswersMatch']==60 and pr['allOfficialAnswersMatch']
assert pr['allFirstParagraphsPreserved']
instructions=read(WORK/'review/practical-original-instructions.json')['instructions']
assert len(instructions)==40
for item in instructions:
 c=next(c for c in cases if c['id']==item['caseId'])
 assert item['originalInstruction'] in c['body']
for f in read(WORK/'review/objective-source-corrections.json'):
 assert qs[f['n']-1]['choices'][f['option']-1]['text']==f['original']
for record in read(WORK/'review/learning-figure-crops.json')['crops']:
 assert hashlib.sha256((WORK/record['image']).read_bytes()).hexdigest()==record['sha256']
assert len({f['image'] for c in cases for f in c['bodyFigures']})==8
assert all('/review-v3/' in f['image'] for c in cases for f in c['bodyFigures'])
assert all('【原本図表' not in c['body'] for c in cases)
for src,sha in read(WORK/'source-files.json').items():
 assert hashlib.sha256((args.delivery/src).read_bytes()).hexdigest()==sha
with tempfile.TemporaryDirectory(prefix='pr48-review-projection-') as d:
 root=Path(d);shutil.copytree(args.delivery,root,dirs_exist_ok=True)
 shutil.copytree(WORK/'assets',root/'assets',dirs_exist_ok=True)
 base=root/'content/fp2'
 for q in qs:q['enrichment']='reviewed'
 for c in cases:c['status']='reviewed'
 for name,value in [('questions.json',qs),('practical-cases.json',cases),('question-reviews.json',read(WORK/'review/objective-publication-reviews.json')),('practical-reviews.json',read(WORK/'review/practical-publication-reviews.json')),('case-catalog.json',{'format':'hitomon-case-catalog','version':1,'qualificationId':'fp2','entries':[{'caseId':c['id'],'packId':'202501','packLabel':'2025年1月26日実施','number':n+1} for n,c in enumerate(cases)]})]:
  (base/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 print(checker.check(root,reviewed=True))
print('PASS PR48 / independent final seals / original corrections / 4 PDFs / 8 crops / draft separation')
