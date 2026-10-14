"""Synthetic promotion gate, not proof of a real content review."""
import copy,importlib.util,json,tempfile,hashlib
from pathlib import Path
from common_fixtures import prepare,write,review
ROOT=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('curator',ROOT/'tools/curate-reviewed-content.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
    root=Path(d);cfg,normal,_=prepare(root);path=root/'content/fixture';evidence=path/'synthetic-evidence.txt';evidence.write_text('非公開の合成テスト証跡。実教材の確認ではありません。')
    r={**review(normal[0]),'status':'approved','evidence':[{'archivedPath':'content/fixture/synthetic-evidence.txt','reviewedContent':True,'contentSha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}]};drafts=path/'drafts.json';reviews=path/'approval.json';exclude=path/'exclude.json';write(drafts,normal);write(reviews,[r]);write(exclude,[])
    result=m.curate(root,'fixture',drafts,reviews,exclude,True);assert result['published']==1
    before=(path/'questions.json').read_bytes();original_r=copy.deepcopy(r)
    for patch in [{'sha256':'0'*64},{'normalizedSha256':'0'*64},{'author':r['reviewer']},{'status':'pending'},{'checks':{'source':True,'answer':False,'choices':True,'wording':True}},{'evidence':[]}]:
        write(reviews,[{**original_r,**patch}])
        try:m.curate(root,'fixture',drafts,reviews,exclude)
        except ValueError:pass
        else:raise AssertionError('Bad review promoted: '+str(patch))
        assert (path/'questions.json').read_bytes()==before
    write(reviews,[original_r]);evidence.write_text('証跡を変更')
    try:m.curate(root,'fixture',drafts,reviews,exclude)
    except ValueError:pass
    else:raise AssertionError('Stale evidence accepted')
    assert (path/'questions.json').read_bytes()==before
print('PASS exact raw/normalized review hashes / different author / required checks / actual archived evidence hash / failures leave published source unchanged')
