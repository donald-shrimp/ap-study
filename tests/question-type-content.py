"""Nonpublic typed authoring contract and normalized review hashes."""
import copy,json,tempfile
from pathlib import Path
import jsonschema
from common_fixtures import prepare,builder,write,review
ROOT=Path(__file__).resolve().parents[1]
schema=json.loads((ROOT/'schemas/question-format.v1.json').read_text())
text_question={'id':'text-and-empty-images','version':1,'type':'singleChoice','stem':'本文がある問題。','sourceImages':[],'choices':[{'id':'a','label':'A'},{'id':'b','label':'B'}],'correctChoiceId':'a'}
jsonschema.validate(text_question,schema)
image_question={**text_question,'sourceImages':['assets/question.png']};image_question.pop('stem');jsonschema.validate(image_question,schema)
for missing in [{k:v for k,v in text_question.items() if k!='stem'},{**text_question,'stem':''}]:
    try:jsonschema.validate(missing,schema)
    except jsonschema.ValidationError:pass
    else:raise AssertionError('Neither text nor a source image is available')
def as_multi(q):
    q=copy.deepcopy(q);q['choices']+=[{'id':'c','label':'C','text':'3'}];q.pop('correctChoiceId');q.update(type='multipleChoice',correctChoiceIds=['c','a'],selection={'mode':'exact','count':2},grading={'method':'exactChoiceSet'},choiceReasons=['奇数','偶数','奇数'],stem='奇数を2つ選んでください。',explanation='1と3が奇数。');return q
with tempfile.TemporaryDirectory() as d:
    root=Path(d);config,normal,extras=prepare(root);path=root/'content/fixture'
    normal=[as_multi(normal[0])];extras=[as_multi(q) for q in extras]
    def publish():
        for name,data in [('questions.json',normal),('reviews.json',[review(q) for q in normal]),('assessments.json',extras),('assessment-reviews.json',[review(q) for q in extras])]:write(path/name,data)
        builder.build(root)
    publish();jsonschema.validate(normal[0],schema)
    manifest=json.loads((root/'data/qualifications/fixture/manifest.json').read_text());compiled=json.loads((root/'data/qualifications/fixture'/manifest['packs'][0]['url']).read_text())[0];assert compiled['answer'] is None and 'correctChoiceId' not in compiled and compiled['correctChoiceIds']==['a','c'];assert json.loads((root/'data/qualifications/fixture'/manifest['index']['url']).read_text())[0]['type']=='multipleChoice' and compiled['selection']['count']==2
    original=copy.deepcopy(normal[0])
    for patch in [{'correctChoiceIds':[]},{'correctChoiceIds':['a','a']},{'correctChoiceIds':['unknown']},{'correctChoiceId':'a'},{'answer':0},{'selection':{'mode':'exact','count':1}},{'selection':{'mode':'all','count':2}},{'grading':{'method':'deferred'}},{'type':'freeText','referenceAnswer':'参考解答'}]:
        normal[0]={**copy.deepcopy(original),**patch}
        try:publish()
        except ValueError:pass
        else:raise AssertionError('Invalid authoring accepted: '+str(patch))
    normal[0]=original;publish()
    normal[0]['selection']={'mode':'all'};publish();assert builder.normalize(normal[0],config,1)['grading']['method']=='exactChoiceSet'
print('PASS generic multiple normal and assessment banks / normalized canonical correct IDs / lightweight index / raw and normalized review hashes / invalid IDs, grading, counts, mixed answer fields and runtime freeText rejected')
