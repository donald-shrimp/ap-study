"""Verify generated content preserves AP material and accepts small other exams."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('content_builder',ROOT/'tools/build-content.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def read(path):return json.loads(path.read_text())
def checked(path,digest):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,path
    return read(path)

manifest=read(ROOT/'data/qualifications/ap/manifest.json')
index=checked(ROOT/'data/qualifications/ap'/manifest['index']['url'],manifest['index']['sha256'])
compiled=[]
for pack in manifest['packs']:
    questions=checked(ROOT/'data/qualifications/ap'/pack['url'],pack['sha256'])
    assert len(questions)==pack['count']
    compiled.extend(questions)
assert len(compiled)==manifest['count']==len(index)==800
assert sum(q['enrichment']=='reviewed' for q in compiled)==manifest['reviewed']==800
raw=read(ROOT/'data/questions.json');by_id={q['id']:q for q in compiled}
for source in raw:
    q=by_id[source['id']]
    for key,value in source.items():
        if key=='choices':assert [{k:v for k,v in c.items() if k!='id'} for c in q[key]]==value
        else:assert q[key]==value,(q['id'],key)
    assert q['choices'][q['answer']]['id']==q['correctChoiceId']
assert not any('hints' in q or 'explanation' in q for q in index)
print('PASS AP 800 questions / 800 explanations / source fields unchanged / pack hashes / lightweight index')

def fixture(count=5,question_id='same-question',pack_id='first'):
    values=[4,5] if count==2 else list(range(1,count+1))
    return {'id':question_id,'packId':pack_id,'packLabel':'検証用パック','number':1,'title':'2＋3','topicId':'basic','source':'検証用の独自問題','stem':'2＋3は幾つですか。','choices':[{'id':f'c{i}','label':str(i+1),'text':str(n)} for i,n in enumerate(values)],'correctChoiceId':f'c{count-1}','enrichment':'reviewed','choiceReasons':['5なので正しい' if n==5 else '5ではないので誤り' for n in values],'hints':[{'title':'最初の操作','text':'2から1ずつ、3回増やしてください。','revealsAnswer':False},{'title':'確かめる','text':'3、4、5と数えられます。','revealsAnswer':True}],'summary':'2＋3＝5','explanation':'2から1を3回足すと5です。','takeaway':'足し算で数を増やす。'}

with tempfile.TemporaryDirectory(prefix='hitomon-content-') as directory:
    root=Path(directory);(root/'templates').mkdir();shutil.copy(ROOT/'templates/study.html',root/'templates/study.html')
    (root/'content').mkdir();(root/'content/qualifications.json').write_text(json.dumps({'qualifications':['one','two']}))
    for id,count in [('one',2),('two',5)]:
        path=root/'content'/id;path.mkdir()
        cfg={'id':id,'name':id,'shortName':id,'questionSource':f'content/{id}/questions.json','topics':[{'id':'basic','name':'基礎'}],'sourceLabel':'検証','sourceDoc':'docs/SOURCES.md','sourceDescription':'検証用'}
        (path/'qualification.json').write_text(json.dumps(cfg));(path/'questions.json').write_text(json.dumps([fixture(count)]))
    builder.build(root)
    assert read(root/'data/qualifications/one/manifest.json')['count']==1
    assert read(root/'data/qualifications/two/manifest.json')['count']==1
    assert 'data-qualification="two"' in (root/'two/index.html').read_text()
    assert '<base href="../">' in (root/'two/index.html').read_text()
    # Add a non-80-question pack without changing any application JavaScript.
    path=root/'content/one/questions.json';path.write_text(json.dumps([fixture(2),fixture(2,'new-question','extra')]))
    builder.build(root);m=read(root/'data/qualifications/one/manifest.json')
    assert m['count']==2 and len(m['packs'])==2
    bad=fixture(2);bad['type']='unknown';path.write_text(json.dumps([bad]))
    try:builder.build(root)
    except ValueError:pass
    else:raise AssertionError('Unknown question type accepted')
print('PASS two qualifications / duplicate ID across qualifications / 2 and 5 choices / small extra pack / unsupported type rejected')
