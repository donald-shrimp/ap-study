"""Check completeness, official answer correspondence, and published assets."""
import json, hashlib
from collections import Counter
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
bank=json.loads((root/'data/questions.json').read_text());keys=json.loads((root/'data/answer-keys.json').read_text());crops=json.loads((root/'data/source-crops.json').read_text());sources=json.loads((root/'data/sources.json').read_text())
assert len(bank)==800 and len({q['id'] for q in bank})==800
assert Counter((q['year'],q['season']) for q in bank)==Counter({(y,s):80 for y in range(2021,2026) for s in ['spring','autumn']})
assert len(keys)==10 and len(crops)==800 and len(sources)==20
by_key={(x['year'],x['season']):x for x in keys};by_crop={r['id']:r for r in crops};ids={q['id'] for q in bank}
for q in bank:
 assert q['answer'] in range(4) and len(q['choices'])==4
 assert q['choices'][q['answer']]['label']==by_key[q['year'],q['season']]['answers'][q['number']-1],q['id']
 assert len(q['hints'])==3 and all(h['text'] and isinstance(h['revealsAnswer'],bool) for h in q['hints'])
 assert q['enrichment'] in ['reviewed','topic-guide']
 assert len(q['choiceReasons'])==(4 if q['enrichment']=='reviewed' else 0)
 assert all(id in ids for id in q['related'])
 assert q['questionUrl'].startswith('https://www.ipa.go.jp/') and q['answerUrl'].startswith('https://www.ipa.go.jp/')
 assert by_crop[q['id']]['page']==q['page']
 for src,size in zip(q['sourceImages'],q['imageSizes']):
  with Image.open(root/src) as im:assert im.size==(size['width'],size['height']) and im.width>500 and im.height>80,q['id'];im.verify()
 for src in [q.get('image'),*[c.get('image') for c in q['choices']]]:
  if src:assert (root/src).exists()
for exam in by_key:
 assert sorted(q['number'] for q in bank if (q['year'],q['season'])==exam)==list(range(1,81))
reviewed={q['id'] for q in bank if q['enrichment']=='reviewed'}
assert all(q['hintStatus']=='individual' for q in bank)
# Every added hint has an explicit authoring record; repeated IDs are rejected.
assigned={}
for file in (root/'data/hint-authoring').glob('*.txt'):
 for lineno,line in enumerate(file.read_text().splitlines(),1):
  if not line.strip() or line.startswith('#'):continue
  fields=line.split('|');assert len(fields) in [5,6],(file,lineno)
  question_ids,concept,*content=fields;flags=content[3] if len(content)==4 else '000'
  assert len(flags)==3 and set(flags)<={'0','1'},(file,lineno)
  assert all(len(text)>=15 for text in content[:3]),(file,lineno)
  for id in question_ids.split():
   assert id in ids and id not in assigned,(file,lineno,id)
   assigned[id]=(f'{file.name}:{lineno}',concept,content[:3],flags)
assert len(assigned)==791
lessons={}
complete_exams=set()
for file in (root/'data/lessons').glob('*.json'):
 records=json.loads(file.read_text())
 assert {r['id'] for r in records}=={f'{file.stem}-q{n}' for n in range(1,81)},file
 complete_exams.add(file.stem)
 for lesson in records:
  assert lesson['id'] in ids and lesson['id'] not in lessons
  assert lesson['checkedAgainst']=='official-question-image-and-answer-key'
  assert len(lesson['choiceReasons'])==4 and all(lesson['choiceReasons'])
  assert len(lesson['hints'])==3 and all(len(h['text'])>=15 for h in lesson['hints'])
  lessons[lesson['id']]=(f'lessons/{file.name}:{lesson["id"]}',lesson)
assert 'r07h' in complete_exams
# Two original 2021 autumn explanations have no complete-exam lesson source.
assert reviewed==set(lessons)|{'r03a-q3','r03a-q4'}
# These three new exams must retain a separate review tied to exact lesson bytes.
for exam in complete_exams-{'r07h'}:
 records=json.loads((root/f'data/lesson-reviews/{exam}.json').read_text())
 assert {r['id'] for r in records}=={f'{exam}-q{n}' for n in range(1,81)} and len(records)==80
 for record in records:
  id=record['id'];lesson=lessons[id][1];q=next(q for q in bank if q['id']==id)
  assert record['status']=='confirmed' and record['independentResult'] and isinstance(record['issues'],list),id
  assert record['officialAnswer']==q['choices'][q['answer']]['label'],id
  digest=hashlib.sha256(json.dumps(lesson,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
  assert record['reviewedLessonSHA256']==digest,id
for q in bank:
 if q['id'] in lessons:
  source,lesson=lessons[q['id']]
  assert q['hintSource']==q['lessonSource']==source and q['enrichment']=='reviewed',q['id']
  assert all(q[f]==lesson[f] for f in ['summary','explanation','choiceReasons','takeaway','hints']),q['id']
 elif q['id'] in assigned:
  source,concept,texts,flags=assigned[q['id']]
  assert q['hintSource']==source and q['concept']==concept,q['id']
  assert [h['text'] for h in q['hints']]==texts,q['id']
  assert [h['revealsAnswer'] for h in q['hints']]==[c=='1' for c in flags],q['id']
 else:
  assert q['enrichment']=='reviewed' and q['hintSource']=='existing-reviewed',q['id']
assert next(q for q in bank if q['id']=='r05a-q18')['hints'][1]['revealsAnswer']
assert bank[0]['id']=='r07h-q1' and bank[0]['answer']==3
assert next(q for q in bank if q['id']=='r04h-q80')['answer']==3
print(f'PASS 800 questions / official keys / 800 images / hint and lesson provenance / {len(complete_exams)} complete exams / {len(reviewed)} individual explanations / independent reviews')
