"""Independent authoring data, optional display/link fields, bounds and reviews."""
import copy,json,tempfile
from pathlib import Path
from common_fixtures import prepare,builder,write,review,question
with tempfile.TemporaryDirectory(prefix='hitomon-common-content-') as d:
    root=Path(d);config,normal,extras=prepare(root);path=root/'content/fixture'
    manifest=json.loads((root/'data/qualifications/fixture/manifest.json').read_text())
    compiled=json.loads((root/'data/qualifications/fixture'/manifest['packs'][0]['url']).read_text())[0]
    assert compiled['number']==1 and compiled['title']=='問題1' and compiled['hints']==[] and compiled['related']==[]
    assert compiled['syllabusId']=='edition-one' and compiled['language']=='ja-JP' and compiled['objectiveIds']==['add']
    assert manifest['assessment']['count']==56 and all(q['sourceKind']=='authored' and 'parentQuestionId' not in q for q in manifest['assessment']['index'])
    assert manifest['mockSets']['sets'][0]['size']==40
    deck=json.loads((root/'data/qualifications/fixture'/manifest['flashcards']['url']).read_text())
    assert deck['cards'][0]['relatedQuestionIds']==[] and deck['cards'][0]['sourceNote']==''
    def reject(change,which='normal'):
        altered=copy.deepcopy(normal if which=='normal' else extras);change(altered[0]);qfile='questions.json' if which=='normal' else 'assessments.json';rfile='reviews.json' if which=='normal' else 'assessment-reviews.json'
        write(path/qfile,altered);write(path/rfile,[review(q) for q in altered])
        try:builder.build(root)
        except (ValueError,TypeError):pass
        else:raise AssertionError('Invalid contract accepted')
        write(path/qfile,normal if which=='normal' else extras);write(path/rfile,[review(q) for q in (normal if which=='normal' else extras)])
    for edit in [lambda q:q.update(uses=['mock']),lambda q:q.update(parentQuestionId='fake'),lambda q:q.update(sourceKind='unknown'),lambda q:q.update(syllabusId='missing'),lambda q:q.update(objectiveIds=['missing']),lambda q:q.update(sourceRefs=['javascript:alert(1)'])]:reject(edit)
    for edit in [lambda q:q.update(uses=['practice']),lambda q:q.update(sourceKind='derived',parentQuestionId='fake'),lambda q:q.update(explanation='')]:reject(edit,'assessment')
    # Reviews cannot be bypassed by dropping their source or changing content.
    bad=copy.deepcopy(config);bad.pop('questionReviewSource');write(path/'qualification.json',bad)
    try:builder.build(root)
    except ValueError:pass
    else:raise AssertionError('Reviewed material without evidence accepted')
    write(path/'qualification.json',config)
    changed_scope=copy.deepcopy(config);changed_scope['syllabuses'][0]['label']='未確認の第2版';write(path/'qualification.json',changed_scope)
    try:builder.build(root)
    except ValueError:pass
    else:raise AssertionError('Changed reviewed syllabus context accepted')
    write(path/'qualification.json',config)
    changed=copy.deepcopy(normal);changed[0]['stem']='1＋2は幾つですか。';write(path/'questions.json',changed)
    try:builder.build(root)
    except ValueError:pass
    else:raise AssertionError('Stale ordinary review accepted')
    write(path/'questions.json',normal)
    for size in [10,201,False]:
        bad=copy.deepcopy(config);bad['diagnosticBlueprint']['size']=size;write(path/'qualification.json',bad)
        try:builder.build(root)
        except ValueError:pass
        else:raise AssertionError('Invalid diagnostic size accepted')
    write(path/'qualification.json',config);builder.build(root)
# Fixed sets must use the same resolved families as the published bank.
with tempfile.TemporaryDirectory(prefix='hitomon-common-family-') as d:
    root=Path(d);config,normal,extras=prepare(root);path=root/'content/fixture'
    normal[0]['familyId']='shared-family';normal[0]['uses']=['practice','mock']
    extras[0].update(sourceKind='derived',parentQuestionId=normal[0]['id'],adaptation='合成テストの数値変更')
    write(path/'questions.json',normal);write(path/'reviews.json',[review(q) for q in normal]);write(path/'assessments.json',extras)
    reviews=[review(q) for q in extras];final=builder.normalize(extras[0],config,1);final['familyId']='shared-family';reviews[0]['normalizedSha256']=builder.diagnostic_digest(final);write(path/'assessment-reviews.json',reviews)
    mock=json.loads((path/'mocks.json').read_text());selected=[normal[0],*extras[:39]];mock['sets'][0]['slots']=[{'number':i+1,'questionId':q['id'],'topicId':q['topicId']} for i,q in enumerate(selected)];write(path/'mocks.json',mock)
    try:builder.build(root)
    except ValueError as error:assert 'Mock content families overlap' in str(error),str(error)
    else:raise AssertionError('Shared parent and variant both accepted into a fixed set')
print('PASS minimal question and standalone cards / parentless dedicated bank / 40-question sets / syllabus and references / ordinary review hashes / wrong role, parent, scope, unknown reference and size rejected')
