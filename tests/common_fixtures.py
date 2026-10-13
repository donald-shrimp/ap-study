"""Private synthetic data for common contracts. Never publish as exam material."""
import importlib.util,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('common_builder',ROOT/'tools/build-content.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def question(id,topic='a',uses=None):
    q={'id':id,'version':1,'topicId':topic,'stem':'1＋1は幾つですか。','choices':[{'id':'a','label':'A','text':'1'},{'id':'b','label':'B','text':'2'}],'correctChoiceId':'b','enrichment':'reviewed','explanation':'1に1を足すと2。','choiceReasons':['足す前の数。','1を加えた数。'],'sourceKind':'authored','sourceRefs':['https://example.com/learning'],'objectiveIds':['add']}
    if uses is not None:q['uses']=uses
    return q
def review(q):
    cfg={"id":"fixture","topics":[{"id":"a","name":"分野A"},{"id":"b","name":"分野B"}],"language":"ja-JP","defaultSyllabusId":"edition-one","syllabuses":[{"id":"edition-one","label":"テスト第1版","language":"ja-JP"}],"objectives":[{"id":"add","label":"加算","topicId":"a"}]}
    ordinal=int(q["id"].removeprefix("assessment-"))+1 if q["id"].startswith("assessment-") else 1
    try:final_hash=builder.diagnostic_digest(builder.normalize(q,cfg,ordinal))
    except ValueError:final_hash='0'*64  # Negative test: intentionally invalid evidence.
    return {'questionId':q['id'],'version':q.get('version',1),'sha256':builder.diagnostic_digest(q),'normalizedSha256':final_hash,'author':'synthetic-author','reviewer':'synthetic-reviewer','checkedAt':'2026-10-13T00:00:00Z','checks':{k:True for k in ['source','answer','choices','wording']},'notes':'合成テスト用の形式検査記録。実教材の確認ではない。'}
def prepare(root):
    for name in ['src','assets/icons','assets/vendor','templates','schemas']:shutil.copytree(ROOT/name,root/name)
    for name in ['app.js','styles.css','pwa.js','sw.js','manifest.webmanifest']:shutil.copy(ROOT/name,root/name)
    path=root/'content/fixture';path.mkdir(parents=True)
    config={'id':'fixture','name':'非公開の共通テスト','questionSource':'content/fixture/questions.json','questionReviewSource':'content/fixture/reviews.json','assessmentQuestionSource':'content/fixture/assessments.json','assessmentReviewSource':'content/fixture/assessment-reviews.json','mockSetSource':'content/fixture/mocks.json','flashcardSource':'content/fixture/cards.json','topics':[{'id':'a','name':'分野A'},{'id':'b','name':'分野B'}],'language':'ja-JP','syllabuses':[{'id':'edition-one','label':'テスト第1版','language':'ja-JP'}],'defaultSyllabusId':'edition-one','objectives':[{'id':'add','label':'加算','topicId':'a'}],'diagnosticBlueprint':{'size':40,'sampling':'topic-weighted','weights':{'a':3,'b':1}}}
    normal=[question('same-question','a',['practice'])]
    extras=[question('assessment-'+str(i),'a' if i<36 else 'b',['diagnostic','mock']) for i in range(56)]
    mock={'format':'hitomon-mock-sets','version':1,'qualificationId':'fixture','sets':[{'id':'fixed','label':'テスト模試','version':1,'status':'ready','size':40,'slots':[{'number':i+1,'questionId':q['id'],'topicId':q['topicId']} for i,q in enumerate(extras[:40])]}]}
    cards={'format':'hitomon-flashcards','version':1,'qualificationId':'fixture','cards':[{'id':'term','version':1,'topicId':'b','front':'加算とは？','back':'数を足すこと。'}]}
    write(root/'content/qualifications.json',{'qualifications':['fixture']});write(path/'qualification.json',config)
    for name,data in [('questions.json',normal),('reviews.json',[review(q) for q in normal]),('assessments.json',extras),('assessment-reviews.json',[review(q) for q in extras]),('mocks.json',mock),('cards.json',cards)]:write(path/name,data)
    builder.build(root)
    return config,normal,extras
