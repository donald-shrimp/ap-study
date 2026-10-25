"""Independently reviewed common-passage cases; no normal-question pool mixing."""
import json,hashlib,re
from material_contracts import validate_legal,validate_numeric,validate_source_hashes,validate_case_figures

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def compile_cases(root,config,directory,hashed_json):
    if not config.get('caseSource'):return None
    cases=json.loads((root/config['caseSource']).read_text());reviews=json.loads((root/config['caseReviewSource']).read_text());by_id={r['caseId']:r for r in reviews}
    assert len(by_id)==len(reviews) and len({c['id'] for c in cases})==len(cases) and set(by_id)=={c['id'] for c in cases}
    for c in cases:
        r=by_id[c['id']]
        validate_legal(c,config.get('requiresLegalContext',False))
        validate_case_figures(c)
        validate_source_hashes(root,c,r)
        assert c['status']=='reviewed' and r['status']=='approved' and r['author']!=r['reviewer'] and r['canonicalCaseSHA256']==hashlib.sha256(canonical(c)).hexdigest()
        assert c['qualificationId']==config['id'] and any(p['id']==c['examPartId'] and p.get('unit')=='cases' for p in config['examParts'])
        keys=[i['id']+'--'+f['id'] for i in c['items'] for f in i['fields']]
        assert len(keys)<=20 and len(set(keys))==len(keys)
        assert c['body'] and c['items'] and len(c['items'])<=30
        assert len({i['id'] for i in c['items']})==len(c['items'])
        for i in c['items']:
            assert i['prompt'] and 1<=len(i['fields'])<=20 and len({f['id'] for f in i['fields']})==len(i['fields'])
            for f in i['fields']:
                assert f['type'] in ('singleChoice','shortText','freeText','numeric') and f['referenceAnswers'] and f['explanation'] and f['rubric']
                assert f['grading']['method'] in ('exactText','self','exactDecimal')
                assert f['type']!='freeText' or f['grading']['method']=='self'
                assert f['type']=='numeric' or f['grading']['method']!='exactDecimal'
                if f['type']=='numeric':validate_numeric(f)
                elif f['type']=='singleChoice':
                    assert 2<=len(f['choices'])<=20 and len({a['id'] for a in f['choices']})==len(f['choices']) and f['grading']['method']=='exactText'
                    assert len(f['referenceAnswers'])==1 and f['referenceAnswers'][0] in [a['label'] for a in f['choices']]
                else:assert all(len(a)<=f.get('maxLength',2000) for a in f['referenceAnswers'])
        paths=c['sourceImages']+[f['image'] for f in c.get('bodyFigures',[])]
        for path in paths:assert path.startswith('assets/written/') and '..' not in path.split('/') and r['assetHashes'][path]==hashlib.sha256((root/path).read_bytes()).hexdigest()
        for path,digest in {**r['sourceHashes'],**r['assetHashes']}.items():assert digest==hashlib.sha256((root/path).read_bytes()).hexdigest()
    name,digest=hashed_json(directory,'cases',{'format':'hitomon-case-bank','version':2,'qualificationId':config['id'],'cases':cases})
    result={'url':name,'sha256':digest,'count':len(cases),'fields':sum(len(i['fields']) for c in cases for i in c['items'])}
    if config.get('caseCatalogSource'):
        path=(root/config['caseCatalogSource']).resolve()
        assert path.is_relative_to(root.resolve())
        catalog=json.loads(path.read_text())
        assert catalog['format']=='hitomon-case-catalog' and catalog['version']==1 and catalog['qualificationId']==config['id']
        entries=catalog['entries'];known={c['id']:c for c in cases};packs={};numbers=set()
        assert isinstance(entries,list) and len(entries)==len(known) and {e['caseId'] for e in entries}==set(known)
        for e in entries:
            assert {'caseId','packId','packLabel','number'}<=set(e)<={'caseId','packId','packLabel','number','referenceTargets'} and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,99}',e['packId'])
            assert isinstance(e['packLabel'],str) and 0<len(e['packLabel'])<=200 and type(e['number']) is int and e['number']>0
            c=known[e['caseId']];refs=c.get('bodyRefs',{});targets=e.get('referenceTargets',{})
            assert isinstance(targets,dict) and len(targets)<=len(refs),'Invalid image reference targets'
            for source,target in targets.items():
                assert isinstance(target,str) and source in refs and target in refs and source!=target,'Unknown image reference'
                assert any(f['caption'].strip()==(refs[target].get('text') or refs[target].get('anchor') or '').strip() for f in c.get('bodyFigures',[])),'Reference target is not a figure'
                assert set(refs[source].get('sourcePages',[])) & set(refs[target].get('sourcePages',[])),'Image reference pages disagree'
            key=(known[e['caseId']]['examPartId'],e['packId']);assert packs.setdefault(key,e['packLabel'])==e['packLabel']
            position=(*key,e['number']);assert position not in numbers;numbers.add(position)
        result['index']=entries
        result['referenceTargetsVersion']=1
    return result
