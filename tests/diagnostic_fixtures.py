"""Synthetic assessment content, never used in the published qualification."""
import importlib.util
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('diagnostic_builder',ROOT/'tools/build-content.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def question(i,variant=False):
    a,b=(20+i,3) if variant else (2+i,3)
    answer=a+b
    q={'id':f'v{i}' if variant else f'q{i}','version':1,'packId':'variants' if variant else 'originals','packLabel':'診断専用検証' if variant else '通常検証','number':i+1,'title':f'{a}＋{b}','topicId':['one','two','three'][i%3],'source':'公開しないテスト用の独自問題','stem':f'{a}＋{b}は幾つですか。','choices':[{'id':'wrong','label':'ア','text':str(answer-1)},{'id':'right','label':'イ','text':str(answer)}],'correctChoiceId':'right','enrichment':'reviewed','choiceReasons':[f'{a}に{b-1}を足した値で、1不足する。',f'{a}に{b}を足すと{answer}。'],'hints':[] if variant else [{'title':'足す','text':f'{a}から1ずつ{b}回増やす。','revealsAnswer':False}],'summary':f'{a}＋{b}＝{answer}','explanation':f'{a}に{b}を足した結果は{answer}。','takeaway':'足し算'}
    if variant:q.update(diagnosticOnly=True,parentQuestionId=f'q{i}',adaptation='検証用の元問題から最初の数を18増やした。')
    return q

def review(q):
    return {'questionId':q['id'],'version':q['version'],'sha256':builder.diagnostic_digest(q),'author':'synthetic-author','reviewer':'synthetic-reviewer','checkedAt':'2026-10-07T00:00:00Z','checks':{k:True for k in ['source','answer','calculation','choices','wording']},'notes':'テスト専用の合成確認記録。公開教材の確認実績ではない。'}

def prepare(root):
    for name in ['src','assets/icons','assets/vendor','templates','schemas']:
        shutil.copytree(ROOT/name,root/name)
    for name in ['app.js','styles.css','pwa.js','sw.js','manifest.webmanifest']:
        shutil.copy(ROOT/name,root/name)
    path=root/'content'/'fixture';path.mkdir(parents=True)
    write(root/'content/qualifications.json',{'qualifications':['fixture']})
    config={'id':'fixture','name':'診断専用の検証資格','shortName':'検証','questionSource':'content/fixture/questions.json','diagnosticQuestionSource':'content/fixture/diagnostic-questions.json','diagnosticReviewSource':'content/fixture/diagnostic-reviews.json','topics':[{'id':id,'name':f'分野{i+1}'} for i,id in enumerate(['one','two','three'])],'sourceLabel':'検証','sourceDoc':'docs/SOURCES.md','sourceDescription':'公開しない検証用教材','diagnosticBlueprint':{'version':2,'size':30,'sampling':'topic-round-robin','assistance':'none','variantLimits':{}}}
    write(path/'qualification.json',config)
    write(path/'questions.json',[question(i) for i in range(40)])
    variants=[question(i,True) for i in range(12)]
    write(path/'diagnostic-questions.json',variants);write(path/'diagnostic-reviews.json',[review(q) for q in variants])
    builder.build(root)
    return config,variants
