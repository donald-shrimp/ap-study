"""Read-only structural/evidence checks. Draft validation never approves content."""
import argparse,copy,importlib.util,json,subprocess,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from material_contracts import validate_source_hashes
spec=importlib.util.spec_from_file_location('delivery_builder',ROOT/'tools/build-content.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def check(root,reviewed=False):
    root=root.resolve();base=root/'content/fp2';read=lambda p:json.loads(p.read_text())
    config=read(ROOT/'content/fp2/qualification.json');raw=read(base/'questions.json');cases=read(base/'practical-cases.json');sources=read(base/'source-files.json')
    builder.require(isinstance(raw,list) and isinstance(cases,list) and isinstance(sources,dict),'Arrays and source-file map required')
    builder.require(len({q['id'] for q in raw})==len(raw) and len({c['id'] for c in cases})==len(cases),'Duplicate material IDs')
    normal=copy.deepcopy(raw);draft_cases=copy.deepcopy(cases)
    if reviewed:
        builder.require(all(q.get('enrichment')=='reviewed' for q in raw),'Reviewed delivery requires reviewed questions and independent evidence for every question')
    if not reviewed:
        for q in normal:
            builder.require(q.get('enrichment')=='draft','Draft questions must have enrichment=draft');q['enrichment']='reviewed'
        for c in draft_cases:
            builder.require(c.get('status')=='draft','Draft cases must have status=draft');c['status']='reviewed'
    for q in raw+cases:validate_source_hashes(root,q,{'sourceHashes':sources})
    questions=[builder.normalize(q,config,n+1) for n,q in enumerate(normal)];builder.validate_questions(questions,config,root)
    for q in questions:builder.require(q['examPartId']=='objective','FP question source is for the objective part')
    # Use the same case validator as import and study, without writing temporary approvals.
    script="import {validateCaseMaterial} from './src/domain/case-study.js';let s='';for await(const c of process.stdin)s+=c;const {cases,q}=JSON.parse(s);for(const c of cases)validateCaseMaterial(c,q);"
    subprocess.run(['node','--input-type=module','-e',script],input=json.dumps({'cases':draft_cases,'q':config}),text=True,cwd=ROOT,check=True)
    for c in cases:
        builder.require(c.get('topicId') in {t['id'] for t in config['topics']},'Unknown case topic')
        for path in c['sourceImages']+[f['image'] for f in c['bodyFigures']]:
            file=(root/path).resolve();builder.require(file.is_relative_to(root) and file.is_file(),'Missing/unsafe case asset: '+path)
    if reviewed:
        builder.validate_reviews(raw,read(base/'question-reviews.json'),questions,root)
        with tempfile.TemporaryDirectory(prefix='fp2-review-check-') as output:
            builder.compile_cases(root,config,Path(output),builder.hashed_json)
    return {'questions':len(raw),'cases':len(cases),'fields':sum(len(i['fields']) for c in cases for i in c['items']),'mode':'reviewed evidence' if reviewed else 'draft structure only; not approved'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('delivery',type=Path);parser.add_argument('--reviewed',action='store_true');args=parser.parse_args()
    try:print(json.dumps(check(args.delivery,args.reviewed),ensure_ascii=False))
    except (ValueError,AssertionError,KeyError,TypeError,OSError,subprocess.CalledProcessError) as e:parser.exit(1,f'Invalid FP2 delivery: {e}\n')
