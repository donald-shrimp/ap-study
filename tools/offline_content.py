"""Build an offline inventory from published, already validated runtime material."""
import hashlib,json,re
from collections import defaultdict
from pathlib import Path

def compile_offline(root,manifest,questions,directory,hashed_json):
    root=root.resolve();assets={}
    def asset(path,sha=None,keep=False):
        path=str(path);file=(root/path).resolve()
        if not file.is_relative_to(root) or not file.is_file():raise ValueError('Offline asset is missing/outside root: '+path)
        data=file.read_bytes();digest=hashlib.sha256(data).hexdigest()
        if sha and sha!=digest:raise ValueError('Offline asset SHA mismatch: '+path)
        row={'url':path,'bytes':len(data),'sha256':digest}
        if keep:row['keep']=True
        assets[path]=row
        return path
    def entry(record,keep=False):return asset((directory/record['url']).relative_to(root),record['sha256'],keep)
    def images(q):
        refs=[] if q.get('stem') else list(q.get('sourceImages',[]))
        if q.get('image'):refs.append(q['image'])
        if q.get('choicePresentation')!='codes':refs.extend(c['image'] for c in q['choices'] if c.get('image'))
        return [asset(p) for p in refs]
    common=[entry(manifest['index'],True)]
    if manifest.get('studyContext'):common.append(entry(manifest['studyContext'],True))
    groups=[]
    def group(id,label,part,unit,ids,files):
        keys=sorted(set(common+files));revision=hashlib.sha256(json.dumps([assets[k] for k in keys],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        groups.append({'id':id,'label':label,'examPartId':part,'unit':unit,'count':len(ids),'itemIds':ids,'files':keys,'bytes':sum(assets[k]['bytes'] for k in keys),'revision':revision})
    for p in manifest['packs']:
        for part in manifest['examParts']:
            qs=[q for q in questions if q['packId']==p['id'] and q['examPartId']==part['id'] and 'practice' in q.get('uses',['practice']) and not q.get('diagnosticOnly')]
            if qs:group('pack-'+p['id']+'-'+part['id'],p['label'],part['id'],'questions',[q['id'] for q in qs],[entry(p)]+[i for q in qs for i in images(q)])
    if manifest.get('cases'):
        bank=manifest['cases'];path=entry(bank,True);cases=json.loads((directory/bank['url']).read_text())['cases'];batches=defaultdict(list)
        for c in cases:
            # Official sessions share source refs. Other future material falls
            # back to its published source label, without assuming 11 cases.
            key=(c['examPartId'],tuple(c.get('sourceRefs',[])))
            batches[key].append(c)
        for n,((part,_),batch) in enumerate(batches.items()):
            source=batch[0].get('source',batch[0]['title']);match=re.search(r'令和(\d+)年度(春期|秋期)',source)
            label=f'{2018+int(match[1])}年 {match[2]}' if match else source
            files=[path]+[asset(f['image']) for c in batch for f in c.get('bodyFigures',[])]
            group('cases-'+batch[0]['id'],label,part,'cases',[c['id'] for c in batch],files)
    if manifest.get('flashcards'):
        record=manifest['flashcards'];part=manifest['defaultExamPartId'];group('flashcards','単語帳',part,'cards',[c['id'] for c in json.loads((directory/record['url']).read_text())['cards']],[entry(record)])
    inventory={'format':'hitomon-offline-inventory','version':1,'qualificationId':manifest['id'],'groups':groups,'assets':assets}
    filename,digest=hashed_json(directory,'offline',inventory)
    return {'url':filename,'sha256':digest,'count':len(groups)}
