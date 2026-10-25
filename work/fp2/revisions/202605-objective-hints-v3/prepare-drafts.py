"""Prepare unreviewed snapshots from manually authored per-question hints."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
previous={q['number']:q for q in read(HERE/'review/previous-publication-questions.json')}
name=sys.argv[1];rows=read(HERE/name);questions=[];notes=[]
for row in rows:
 q=json.loads(json.dumps(previous[row['number']]))
 q.update(version=q['version']+1,enrichment='draft',hintStatus='individual',hints=row['hints'])
 questions.append(q)
 notes.append({k:v for k,v in row.items() if k!='hints'}|{'questionId':q['id'],'version':q['version'],'author':'Codex /root'})
batch=name.removeprefix('author-hints-').removesuffix('.json')
write(HERE/'drafts'/f'{batch}.json',questions);write(HERE/f'author-notes-{batch}.json',notes)
p=read(HERE/'progress.json');p['authorReadyBatches']=sorted(set(p['authorReadyBatches']+[batch]));p['questionsAuthored']=sum(len(read(f)) for f in (HERE/'drafts').glob('q*.json'));p['next']='review and next uncreated batch';write(HERE/'progress.json',p)
print('Prepared draft batch',batch,len(questions))
