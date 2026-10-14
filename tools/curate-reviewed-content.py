#!/usr/bin/env python3
"""Promote only exact, independently reviewed author drafts; never invent reviews."""
import argparse,importlib.util,json,hashlib,os,tempfile,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('content_builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
def read(p):return json.loads(p.read_text())
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);fd,temporary=tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd,'w') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    os.replace(temporary,path)
def curate(root,qualification,drafts_path,reviews_path,exclusions_path,register=False):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}',qualification):raise ValueError('Invalid qualification ID')
    config=read(root/'content'/qualification/'qualification.json');drafts=read(drafts_path);reviews=read(reviews_path);exclusions=read(exclusions_path)
    if config['id']!=qualification:raise ValueError('Qualification mismatch')
    # Match compile_qualification's generic defaults before normalizing or validating.
    config.setdefault('shortName',config['name'])
    config.setdefault('topics',[{'id':'general','name':'全般'}])
    config.setdefault('defaultExamPartId','objective')
    config.setdefault('examParts',[{'id':'objective','label':'選択式','practiceAvailable':True}])
    by_id={q['id']:q for q in drafts};by_review={r['questionId']:r for r in reviews};excluded={x['questionId']:x for x in exclusions}
    if len(by_id)!=len(drafts) or len(by_review)!=len(reviews) or len(excluded)!=len(exclusions):raise ValueError('Duplicate authoring IDs')
    if not set(excluded)<=set(by_id):raise ValueError('Unknown excluded question')
    selected=[];checked=[]
    eligible=[q for q in drafts if q['id'] not in excluded]
    finals={q['id']:builder.normalize(q,config,i+1) for i,q in enumerate(eligible)}
    for q in finals.values():
        parent=finals.get(q.get('parentQuestionId'))
        if parent and parent.get('familyId'):q.setdefault('familyId',builder.family(parent))
    for q in drafts:
        if q['id'] in excluded:
            if not isinstance(excluded[q['id']].get('reason'),str) or not excluded[q['id']]['reason'].strip():raise ValueError('Missing exclusion reason')
            continue
        review=by_review.get(q['id']);final=finals[q['id']]
        if not review or review.get('status')!='approved' or review.get('sha256')!=builder.diagnostic_digest(q) or review.get('normalizedSha256')!=builder.diagnostic_digest(final):raise ValueError('Missing or stale independent approval: '+q['id'])
        # Existing public builder enforces actual author/reviewer IDs, date, checks and both hashes.
        builder.validate_reviews([q],[review],[final])
        evidence=review.get('evidence',[])
        if not evidence:raise ValueError('Missing reviewed evidence: '+q['id'])
        for item in evidence:
            path=(root/item['archivedPath']).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or item.get('reviewedContent') is not True or hashlib.sha256(path.read_bytes()).hexdigest()!=item.get('contentSha256'):raise ValueError('Changed evidence: '+q['id'])
        selected.append(q);checked.append(review)
    if not selected:raise ValueError('No approved questions')
    published_ids={q['id'] for q in selected}
    for e in exclusions:
        if e.get('canonicalQuestionId') and e['canonicalQuestionId'] not in published_ids:raise ValueError('Duplicate target not approved')
    builder.validate_questions([finals[q['id']] for q in selected],config,root)
    destinations=[(root/config[k]).resolve() for k in ['questionSource','questionReviewSource']]
    if any(not p.is_relative_to(root.resolve()) for p in destinations):raise ValueError('Output outside repository')
    # All checks above finish before any public source/registry write.
    write(root/config['questionSource'],selected);write(root/config['questionReviewSource'],checked)
    if register:
        registry=read(root/'content/qualifications.json')
        if qualification not in registry['qualifications']:registry['qualifications'].append(qualification);write(root/'content/qualifications.json',registry)
    return {'drafts':len(drafts),'published':len(selected),'excluded':len(exclusions),'singleChoice':sum(q.get('type','singleChoice')=='singleChoice' for q in selected),'multipleChoice':sum(q.get('type','singleChoice')=='multipleChoice' for q in selected)}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--root',type=Path,default=ROOT);cli.add_argument('--qualification',required=True);cli.add_argument('--drafts',type=Path,required=True);cli.add_argument('--reviews',type=Path,required=True);cli.add_argument('--exclusions',type=Path,required=True);cli.add_argument('--register',action='store_true');args=cli.parse_args()
    try:print(json.dumps(curate(args.root,args.qualification,args.drafts,args.reviews,args.exclusions,args.register),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError) as error:cli.exit(1,str(error)+'\n')
