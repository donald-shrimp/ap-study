"""Private synthetic cases for the FP-compatible engine, never exam content."""
import base64,copy,hashlib,json,shutil
from pathlib import Path
from common_fixtures import prepare as prepare_common,builder,write,ROOT

def prepare(root,draft=False,cases_only=False):
    prepare_common(root)
    cfg=json.loads((ROOT/'content/fp2/qualification.json').read_text());base=root/'content/fp2';base.mkdir(exist_ok=True)
    # Two populated practical subjects, all other parts deliberately empty.
    for part in cfg['examParts']:
        if part['id']=='jafp-practical':part['label']='合成実技A'
        elif part['id']=='kinzai-personal':part['label']='合成実技B'
    source=root/'sources/fp2';source.mkdir(parents=True);hashes={}
    for kind in ['question','answer']:
        path=source/f'synthetic-{kind}.pdf';path.write_bytes(('%PDF-1.4\nSynthetic '+kind+' for contract tests only.\n%%EOF\n').encode());hashes[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    record={'publisher':'合成テスト','publishedAt':'2026-05-01','legalAsOf':'2026-04-01','questionUrl':'https://example.com/question.pdf','questionSha256':hashes['sources/fp2/synthetic-question.pdf'],'answerUrl':'https://example.com/answer.pdf','answerSha256':hashes['sources/fp2/synthetic-answer.pdf'],'modifiedFromOriginal':False,'modificationNote':''}
    legal={'status':'unverified','checkedAt':None,'sourceRefs':[],'note':''}
    normal={'id':'synthetic-objective','version':1,'examPartId':'objective','topicId':'financial-assets','title':'合成の選択問題','stem':'2となる式を選ぶ。','choices':[{'id':'a','label':'ア','text':'1＋1'},{'id':'b','label':'イ','text':'1＋2'}],'correctChoiceId':'a','explanation':'形式検査用の合成解説。','choiceReasons':['1＋1は2。','1＋2は3。'],'enrichment':'draft' if draft else 'reviewed','sourceRecord':record,'legalReview':legal,'sourceKind':'authored'}
    def numeric(id,answer,unit='円',places=0):return {'id':id,'label':id,'type':'numeric','maxLength':100,'numeric':{'unit':unit,'decimalPlaces':places,'rounding':'none'},'grading':{'method':'exactDecimal'},'referenceAnswers':[answer],'explanation':'形式検査用の数値解説。','rubric':['値と単位を確認する。']}
    def case(id,part,fields):return {'id':id,'qualificationId':'fp2','examPartId':part,'topicId':'financial-assets','version':1,'status':'draft' if draft else 'reviewed','title':id,'source':'合成教材・実問題ではない','body':'合成の共通本文。[fig]','sourceImages':[],'bodyFigures':[],'sourceRecord':copy.deepcopy(record),'legalReview':copy.deepcopy(legal),'items':[{'id':'q1','label':'問1','prompt':'合成の入力欄。','fields':fields}]}
    booleans=[{'id':'b'+str(n),'label':'判定'+str(n),'type':'singleChoice','choices':[{'id':'true','label':'○','text':'正しい'},{'id':'false','label':'×','text':'誤り'}],'grading':{'method':'exactText'},'referenceAnswers':['○'],'explanation':'合成の判定欄。','rubric':['登録した判定。']} for n in range(4)]
    cases=[case('synthetic-a','jafp-practical',booleans+[numeric('amount','1490000'),numeric('ratio','0.435','倍',3)]),case('synthetic-b','kinzai-personal',[numeric('amount','7')])]
    asset=root/'assets/written/fp2-fixture/figure.png';asset.parent.mkdir(parents=True);asset.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4p8AAAAASUVORK5CYII='))
    cases[0]['bodyFigures']=[{'image':str(asset.relative_to(root)),'anchor':'[fig]','alt':'合成図','caption':'合成図'}]
    cases[0]['legalReview']={'status':'current','checkedAt':'2026-10-24','sourceRefs':['https://example.com/law'],'note':'合成テストの確認記録。'}
    reviews=[]
    for c in cases:
        ah={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in c['sourceImages']+[f['image'] for f in c['bodyFigures']]}
        reviews.append({'caseId':c['id'],'status':'approved','author':'synthetic-author','reviewer':'synthetic-reviewer','canonicalCaseSHA256':builder.diagnostic_digest(c),'sourceHashes':hashes,'assetHashes':ah})
    normal_review={'questionId':normal['id'],'version':1,'sha256':builder.diagnostic_digest(normal),'normalizedSha256':builder.diagnostic_digest(builder.normalize(normal,cfg)),'author':'synthetic-author','reviewer':'synthetic-reviewer','checkedAt':'2026-10-24T00:00:00Z','checks':{k:True for k in ['source','answer','choices','wording']},'notes':'Synthetic evidence only.','sourceHashes':hashes} if not draft else None
    write(root/'content/qualifications.json',{'qualifications':['fp2']});write(base/'qualification.json',cfg)
    for name,value in [('questions.json',[] if cases_only else [normal]),('practical-cases.json',cases),('source-files.json',hashes),('question-reviews.json',[] if cases_only or draft else [normal_review]),('practical-reviews.json',[] if draft else reviews)]:write(base/name,value)
    if not draft:builder.build(root)
    return cfg,normal,cases
