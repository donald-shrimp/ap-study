"""Independently reviewed common-passage cases; no normal-question pool mixing."""
import json,hashlib,re

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def compile_cases(root,config,directory,hashed_json):
    if not config.get('caseSource'):return None
    cases=json.loads((root/config['caseSource']).read_text());reviews=json.loads((root/config['caseReviewSource']).read_text());by_id={r['caseId']:r for r in reviews}
    assert len(by_id)==len(reviews) and len({c['id'] for c in cases})==len(cases)
    for c in cases:
        r=by_id[c['id']]
        assert c['status']=='reviewed' and r['status']=='approved' and r['author']!=r['reviewer'] and r['canonicalCaseSHA256']==hashlib.sha256(canonical(c)).hexdigest()
        assert c['qualificationId']==config['id'] and any(p['id']==c['examPartId'] and p.get('unit')=='cases' for p in config['examParts'])
        keys=[i['id']+'--'+f['id'] for i in c['items'] for f in i['fields']]
        assert len(keys)<=20 and len(set(keys))==len(keys)
        assert c['body'] and c['items'] and len(c['items'])<=30
        assert len({i['id'] for i in c['items']})==len(c['items'])
        for i in c['items']:
            assert i['prompt'] and 1<=len(i['fields'])<=20 and len({f['id'] for f in i['fields']})==len(i['fields'])
            for f in i['fields']:
                assert f['type'] in ('singleChoice','shortText','freeText') and f['referenceAnswers'] and f['explanation'] and f['rubric']
                assert f['grading']['method'] in ('exactText','self')
                assert f['type']!='freeText' or f['grading']['method']=='self'
                if f['type']=='singleChoice':
                    assert len({a['id'] for a in f['choices']})==len(f['choices'])
                    assert len(f['referenceAnswers'])==1 and f['referenceAnswers'][0] in [a['label'] for a in f['choices']]
                else:assert all(len(a)<=f.get('maxLength',2000) for a in f['referenceAnswers'])
        paths=c['sourceImages']+[f['image'] for f in c.get('bodyFigures',[])]
        for path in paths:assert path.startswith('assets/written/') and '..' not in path.split('/') and r['assetHashes'][path]==hashlib.sha256((root/path).read_bytes()).hexdigest()
        for path,digest in {**r['sourceHashes'],**r['assetHashes']}.items():assert digest==hashlib.sha256((root/path).read_bytes()).hexdigest()
    name,digest=hashed_json(directory,'cases',{'format':'hitomon-case-bank','version':2,'qualificationId':config['id'],'cases':cases})
    return {'url':name,'sha256':digest,'count':len(cases),'fields':sum(len(i['fields']) for c in cases for i in c['items'])}
