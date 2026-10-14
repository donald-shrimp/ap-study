"""Synthetic static HTML; no supplied question receives a content review here."""
import importlib.util,json,tempfile,copy
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('intake',ROOT/'tools/import-question-drafts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
schema=json.loads((ROOT/'schemas/question-format.v1.json').read_text())
def html(code='Q1',kind='checkbox',correct='0,2',stem='正しいものを2つ選んでください。',choices=None):
    return '<script>throw Error("Never execute")</script><article class="question" data-correct="'+correct+'"><div class="qhead"><small>'+code+'</small></div><p class="stem">'+stem+'</p><div class="choices">'+''.join('<label class="choice"><input type="'+kind+'"><span>'+c+'</span></label>' for c in (choices or ['A','B','C']))+'</div><details class="answer"><p>正答：A、C</p><p>説明<br>2行目</p></details></article>'
with tempfile.TemporaryDirectory() as d:
    root=Path(d);out=root/'output';f=root/'one.html';f.write_text(html());result=m.import_files([f],out,'fixture','originals');assert result['newQuestions']==1
    manifest=json.loads((out/'manifest.json').read_text());row=next(iter(manifest['questions'].values()));draft=json.loads((out/row['revisions'][0]['path']).read_text());q=draft['question'];assert q['type']=='multipleChoice' and q['selection']=={'mode':'exact','count':2} and q['correctChoiceIds']==['choice-0','choice-2'];assert q['explanation']=='説明\n2行目';jsonschema.validate(q,schema);assert not draft['contentReviewComplete'] and not draft['publishedToApp'];assert not draft['issues']
    original=(out/'manifest.json').read_bytes();assert m.import_files([f],out,'fixture','originals')['skippedSources']==1;assert (out/'manifest.json').read_bytes()==original
    f.write_text(html(stem='内容を変更。2つ選んでください。'));res=m.import_files([f],out,'fixture','originals');assert res['newRevisions']==1 and len(res['revisionConflicts'])==1
    f2=root/'two.html';f2.write_text(html(code='Q2',stem='内容を変更。2つ選んでください。',choices=['C','A','B']));res=m.import_files([f2],out,'fixture','originals');assert res['newQuestions']==1 and len(res['duplicateCandidates'])==1
    for params in [('other','originals'),('fixture','different')]:
        try:m.import_files([f2],out,*params)
        except ValueError:pass
        else:raise AssertionError('Wrong collection accepted')
    try:m.import_files([f,f],out,'fixture','originals')
    except ValueError:pass
    else:raise AssertionError('Duplicate file argument accepted')
    # Atomic preflight: malformed second file must leave existing ledger unchanged.
    before=(out/'manifest.json').read_bytes();f.write_text(html(code='Q3'));bad=root/'bad.html';bad.write_text('<div>Unsupported</div>')
    try:m.import_files([f,bad],out,'fixture','originals')
    except ValueError:pass
    else:raise AssertionError('Malformed HTML accepted')
    assert (out/'manifest.json').read_bytes()==before
manual='<article class="question"><div class="qhead"><small>MANUAL</small></div><p class="stem">選んでください。</p><div class="manual"><ol><li> A </li><li>B</li></ol></div><details class="answer"><p>正答：A</p><p>説明</p></details></article>'
r=m.extract(manual,'fixture','originals','manual.html')[0];assert r['question']['type']=='singleChoice' and r['question']['correctChoiceId']=='choice-0';jsonschema.validate(r['question'],schema)
r=m.extract(html(choices=['正解はそれぞれ完全なソリューションを示します。','A','B','C'],correct='1,3'),'fixture','originals','move.html')[0];assert len(r['question']['choices'])==3 and r['question']['correctChoiceIds']==['choice-0','choice-2'];assert '完全なソリューション' in r['question']['stem'];assert len(r['formatChanges'])==1
free='<article class="question" data-type="freeText"><p class="stem">説明してください。</p><details class="answer"><p>正答：参考解答</p></details></article>'
r=m.extract(free,'fixture','originals','free.html')[0];jsonschema.validate(r['question'],schema);assert r['question']['grading']=={'method':'deferred'} and 'choices' not in r['question']
unknown=m.extract('<article class="question" data-type="ranking"><p class="stem">並べよ</p></article>','fixture','originals','other.html')[0];assert unknown['issues'] and unknown['question']['type']=='ranking'
# Added notes do not obscure an otherwise exact duplicate candidate.
base=m.extract(html(),'fixture','originals','base.html')[0];noted=m.extract(html(choices=['正解はそれぞれ完全なソリューションを示します。','A','B','C'],correct='1,3'),'fixture','originals','noted.html')[0];assert base['fingerprint']==noted['fingerprint']
one=m.extract(html(correct='0',stem='当てはまるものをすべて選んでください。'),'fixture','originals','one-answer.html')[0];assert one['question']['type']=='multipleChoice' and one['question']['selection']['mode']=='all'
print('PASS static extraction / multi and exact count / manual 4-option recovery / preserved lines / mixed instructions / explicit freeText draft / unknown format guard / idempotence / revisions without overwrites / order-independent duplicate candidates / collection isolation / failed batch unchanged')
