"""Compile qualification settings and source questions into static, hashed packs.

IPA's 80-question/source verification stays in corpus.py and the AP authoring tools.
This compiler has no fixed exam years, question count, choice count, or hint count.
"""
import argparse
from datetime import datetime
from collections import defaultdict
import hashlib
import html as html_tools
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from material_contracts import validate_legal, validate_source_hashes
from written_content import compile_cases
from offline_content import compile_offline
ROOT = Path(__file__).resolve().parents[1]
SAFE_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$')
MAX_ASSESSMENT_SIZE = 200
USES = {'practice', 'diagnostic', 'mock'}


def question_uses(q):
    return q.get('uses', ['diagnostic', 'mock'] if q.get('diagnosticOnly') else ['practice', 'diagnostic'])


def origin(q):
    return q.get('sourceKind', 'derived' if q.get('parentQuestionId') else 'official')


def family(q):
    return q.get('familyId') or q.get('parentQuestionId') or q['id']


def valid_size(size, minimum=1):
    return type(size) is int and minimum <= size <= MAX_ASSESSMENT_SIZE


def safe_refs(refs):
    return isinstance(refs, list) and len(refs) <= 10 and all(isinstance(u, str) and len(u) <= 4000 and urlparse(u).scheme in ['http', 'https'] and urlparse(u).netloc and not re.search(r'[<>\"\x00-\x1f]', u) for u in refs)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    body = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def hashed_json(directory, prefix, value):
    body = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    digest = hashlib.sha256(body).hexdigest()
    name = f'{prefix}.{digest[:16]}.json'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(body)
    return name, digest


def normalize(raw, config, ordinal=1):
    q = dict(raw)
    require('qualificationId' not in q or q['qualificationId'] == config['id'], f"Question qualification mismatch: {q['id']}")
    # Existing IPA authoring records keep their provenance. Published purpose
    # uses one canonical field; a dedicated question is not necessarily derived.
    if 'diagnosticOnly' in q:
        require(q['diagnosticOnly'] is True and 'practice' not in q.get('uses', []), f"Invalid dedicated purpose: {q['id']}")
        q.setdefault('uses', ['diagnostic', 'mock'])
        del q['diagnosticOnly']
    q['qualificationId'] = config['id']
    q.setdefault('examPartId', config.get('defaultExamPartId', 'objective'))
    q.setdefault('type', 'singleChoice')
    require(q['type'] in ['singleChoice','multipleChoice'], f"Unsupported runtime question type (freeText is draft-only): {q['id']}")
    require('referenceAnswer' not in q, f"Reference answer belongs to freeText drafts: {q['id']}")
    if config.get('adapter') == 'ipa-ap':
        q['packId'] = q['id'].split('-q', 1)[0]
        label = config['seasonLabels'][q['season']]
        q['packLabel'] = f"{q['year']}年 {label}"
        q['topicId'] = next(t['id'] for t in config['topics'] if t['name'] == q['topic'])
        q['choices'] = [dict(c, id=f'choice-{i}') for i, c in enumerate(q['choices'])]
        q['correctChoiceId'] = q['choices'][q['answer']]['id']
    else:
        if len(config['topics']) == 1:
            q.setdefault('topicId', config['topics'][0]['id'])
        topic = next(t for t in config['topics'] if t['id'] == q['topicId'])
        q['topic'] = topic['name']
        q.setdefault('packId', 'study')
        q.setdefault('packLabel', '学習問題')
        q.setdefault('number', ordinal)
        q.setdefault('title', f"問題{q['number']}")
        if 'sourceKind' not in q and not q.get('parentQuestionId'):
            q['sourceKind'] = 'authored'
        q['choices'] = [dict(c) for c in q['choices']]
        if q['type']=='multipleChoice':
            require('correctChoiceId' not in q and 'answer' not in raw, f"Mixed answer format: {q['id']}")
            correct=q.get('correctChoiceIds',[])
            require(isinstance(correct,list) and all(isinstance(c,str) for c in correct) and len(set(correct))==len(correct) and all(c in {a['id'] for a in q['choices']} for c in correct), f"Invalid multiple answers: {q['id']}")
            q['correctChoiceIds']=[c['id'] for c in q['choices'] if c['id'] in correct]
            q['answer']=None
            q.setdefault('selection', {'mode':'all'})
            q.setdefault('grading', {'method':'exactChoiceSet'})
        else:
            require('correctChoiceId' in q, f"Missing correct choice ID: {q['id']}")
            q['answer'] = next((i for i, c in enumerate(q['choices']) if c['id'] == q['correctChoiceId']), -1)
    if config.get('defaultSyllabusId'):
        q.setdefault('syllabusId', config['defaultSyllabusId'])
    if config.get('language'):
        q.setdefault('language', config['language'])
    if q.get('syllabusId'):
        scope = next((s for s in config.get('syllabuses', []) if s['id'] == q['syllabusId']), None)
        require(scope is not None, f"Unknown syllabus: {q['id']}")
        q['syllabus'] = dict(scope)
    if q.get('objectiveIds'):
        objectives = {o['id']: o for o in config.get('objectives', [])}
        require(all(i in objectives for i in q['objectiveIds']), f"Unknown objective: {q['id']}")
        q['objectivesSnapshot'] = [dict(objectives[i]) for i in q['objectiveIds']]
    for field, default in {
        'version': 1, 'year': None, 'season': '', 'concept': '', 'topicDescription': '',
        'sourceImages': [], 'imageSizes': [], 'stem': '', 'related': [], 'adaptation': '',
        'searchText': '', 'hintStatus': 'individual', 'page': None,
        'hints': [], 'summary': '', 'explanation': '', 'takeaway': '',
        'choiceReasons': [], 'source': config.get('sourceLabel', ''), 'enrichment': 'topic-guide',
    }.items():
        q.setdefault(field, default)
    return q


def validate_questions(questions, config, root, diagnostic=False, related_ids=None):
    ids = set()
    for q in questions:
        require(not config.get('requiresReviewedContent',False) or q.get('enrichment')=='reviewed', f"Unreviewed content cannot be published: {q['id']}")
        require(SAFE_ID.fullmatch(q['id']) and q['id'] not in ids, f"Duplicate/invalid question ID: {q['id']}")
        ids.add(q['id'])
        uses = question_uses(q)
        require(isinstance(uses, list) and 0 < len(uses) <= 3 and len(set(uses)) == len(uses) and all(u in USES for u in uses), f"Invalid uses: {q['id']}")
        require(('practice' not in uses) if diagnostic else ('practice' in uses and not q.get('diagnosticOnly')), f"Assessment material in ordinary source: {q['id']}")
        require(origin(q) in ['official', 'authored', 'derived'], f"Invalid source kind: {q['id']}")
        require((isinstance(q.get('parentQuestionId'), str) and SAFE_ID.fullmatch(q['parentQuestionId']) and q['parentQuestionId'] != q['id']) if origin(q) == 'derived' else 'parentQuestionId' not in q, f"Invalid parent link: {q['id']}")
        require(('diagnosticOnly' not in q or q['diagnosticOnly'] is True) and (not q.get('diagnosticOnly') or 'practice' not in uses), f"Invalid assessment flag: {q['id']}")
        for key in ['familyId', 'syllabusId']:
            require(key not in q or isinstance(q[key], str) and SAFE_ID.fullmatch(q[key]), f"Invalid {key}: {q['id']}")
        require('language' not in q or isinstance(q['language'], str) and re.fullmatch(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*', q['language']), f"Invalid language: {q['id']}")
        require('sourceRefs' not in q or safe_refs(q['sourceRefs']), f"Invalid source references: {q['id']}")
        require('syllabusId' not in q or q['syllabusId'] in {s['id'] for s in config.get('syllabuses', [])}, f"Unknown syllabus: {q['id']}")
        objectives = q.get('objectiveIds', [])
        require(isinstance(objectives, list) and len(objectives) <= 20 and len(set(objectives)) == len(objectives) and all(isinstance(i, str) and i in {o['id'] for o in config.get('objectives', [])} for i in objectives), f"Unknown objective: {q['id']}")
        validate_legal(q,config.get('requiresLegalContext',False))
        require(q['examPartId'] in {p['id'] for p in config['examParts']}, f"Invalid exam part: {q['id']}")
        require(SAFE_ID.fullmatch(q['packId']), f"Invalid pack ID: {q['id']}")
        require(isinstance(q['title'], str) and q['title'], f"Missing title: {q['id']}")
        require(isinstance(q.get('number'), int) and q['number'] > 0, f"Missing question number: {q['id']}")
        require(type(q['version']) is int and q['version'] > 0, f"Invalid version: {q['id']}")
        require(2 <= len(q['choices']) <= 20, f"Invalid choice count: {q['id']}")
        choice_ids = [c['id'] for c in q['choices']]
        require(len(set(choice_ids)) == len(choice_ids) and all(SAFE_ID.fullmatch(c) for c in choice_ids), f"Invalid choice IDs: {q['id']}")
        require('grading' not in q or q['grading']=={'method':'exactChoiceSet'}, f"Unsupported grading: {q['id']}")
        if q['type']=='multipleChoice':
            correct=q.get('correctChoiceIds');selection=q['selection']
            require(isinstance(correct,list) and 0<len(correct)<=len(choice_ids) and len(set(correct))==len(correct) and all(c in choice_ids for c in correct), f"Invalid multiple answers: {q['id']}")
            q['correctChoiceIds']=[c for c in choice_ids if c in correct]
            require(isinstance(selection,dict) and (selection=={'mode':'all'} or set(selection)=={'mode','count'} and selection['mode']=='exact' and type(selection['count']) is int and selection['count']==len(correct)), f"Invalid selection rule: {q['id']}")
        else:
            require('correctChoiceIds' not in q and 'selection' not in q and q['correctChoiceId'] in choice_ids and q['answer'] >= 0, f"Invalid answer: {q['id']}")
        require(all(set(c) <= {'id','label','text','image'} and isinstance(c.get('label'), str) and 0 < len(c['label']) <= 100 and ('text' not in c or isinstance(c['text'],str) and len(c['text'])<=20000) for c in q['choices']), f"Invalid choice text: {q['id']}")
        require(q['enrichment'] in ['reviewed', 'topic-guide'], f"Invalid lesson state: {q['id']}")
        require(len(q['choiceReasons']) == (len(q['choices']) if q['enrichment'] == 'reviewed' else 0), f"Invalid reasons: {q['id']}")
        require(0 <= len(q['hints']) <= 20 and all(isinstance(h['title'],str) and 0<len(h['title'])<=100 and isinstance(h['text'],str) and 0<len(h['text'])<=10000 and isinstance(h['revealsAnswer'], bool) for h in q['hints']), f"Invalid hints: {q['id']}")
        require(all(isinstance(r,str) and len(r)<=20000 for r in q['choiceReasons']), f"Invalid reason text: {q['id']}")
        require(q['enrichment'] != 'reviewed' or q['explanation'].strip() and all(isinstance(r, str) and r.strip() for r in q['choiceReasons']), f"Missing reviewed explanation: {q['id']}")
        require(all(isinstance(q[f], str) and len(q[f])<=20000 for f in ['summary', 'explanation', 'takeaway', 'source','adaptation']), f"Invalid text: {q['id']}")
        require(isinstance(q['stem'], str) and len(q['stem']) <= 20000 and (q['stem'] or q['sourceImages']), f"Missing/invalid question body: {q['id']}")
        require(q.get('choicePresentation','inline') in ['inline','codes'] and (q.get('choicePresentation')!='codes' or q.get('image')), f"Invalid choice presentation: {q['id']}")
        require(len(q['sourceImages']) == len(q['imageSizes']), f"Missing image sizes: {q['id']}")
        for asset in q['sourceImages'] + [q.get('image')] + [c.get('image') for c in q['choices']]:
            if asset:
                require(not re.search(r'[<>\"\x00-\x1f]', asset) and "'" not in asset and not asset.startswith(('http:', 'https:', '//')) and (root / asset).is_file() and (root / asset).resolve().is_relative_to(root.resolve()), f"Missing/unsafe asset: {q['id']} {asset}")
    for q in questions:
        require(all(ref in (related_ids or ids) for ref in q['related']), f"Missing related question: {q['id']}")
    by_id = {q['id']:q for q in questions}
    if not diagnostic:
        for q in questions:
            if origin(q) == 'derived':
                parent=by_id.get(q.get('parentQuestionId'))
                require(parent is not None and origin(parent) != 'derived' and (q['topicId'],q['examPartId']) == (parent['topicId'],parent['examPartId']) and family(q)==family(parent), f"Derived parent scope mismatch: {q['id']}")
    scopes = {}
    for q in questions:
        key = family(q)
        scope = (q['topicId'], q['examPartId'])
        require(key not in scopes or scopes[key] == scope, f"A content family crosses topics or parts: {q['id']}")
        scopes[key] = scope


def diagnostic_digest(raw):
    """Hash the authored object, including choices and explanations, before defaults."""
    return hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_reviews(raw, reviews, normalized=None, root=None):
    require(isinstance(reviews, list), 'Reviews must be a list')
    by_id = {r['questionId']: r for r in reviews}
    published = [q for q in raw if q.get('enrichment') == 'reviewed']
    require(len(by_id) == len(reviews) and set(by_id) == {q['id'] for q in published}, 'Review set mismatch')
    for q in published:
        r = by_id[q['id']]
        if root is not None:validate_source_hashes(root,q,r)
        require(r.get('version') == q.get('version', 1) and r.get('sha256') == diagnostic_digest(q), f"Stale review: {q['id']}")
        if normalized is not None:
            final = next(item for item in normalized if item['id'] == q['id'])
            require(r.get('normalizedSha256') == diagnostic_digest(final), f"Reviewed context or final record changed: {q['id']}")
        require(all(isinstance(r.get(k), str) and r[k].strip() for k in ['author', 'reviewer', 'notes']) and r['author'] != r['reviewer'], f"Independent review missing: {q['id']}")
        checks = r.get('checks', {})
        require(all(checks.get(k) is True for k in ['source', 'answer', 'choices', 'wording']) and ('calculation' not in checks or checks['calculation'] is True or checks['calculation'] == 'not-applicable'), f"Incomplete review: {q['id']}")
        try:
            checked = datetime.fromisoformat(r['checkedAt'].replace('Z', '+00:00'))
            require(checked.tzinfo is not None, 'Review time needs timezone')
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError(f"Invalid review date: {q['id']}") from error


def compile_assessments(root, config, originals, directory):
    if 'assessmentQuestionSource' not in config:
        return None
    def source(key):
        path=root / config[key]
        require(path.resolve().is_relative_to(root.resolve()), 'Diagnostic source is outside the repository')
        return json.loads(path.read_text())
    raw=source('assessmentQuestionSource');reviews=source('assessmentReviewSource')
    require(isinstance(raw, list) and isinstance(reviews, list), 'Diagnostic sources must be lists')
    by_id={q['id']:q for q in originals};review_by_id={r['questionId']:r for r in reviews}
    require(len(review_by_id)==len(reviews), 'Duplicate diagnostic review')
    require(set(review_by_id)=={q['id'] for q in raw}, 'Diagnostic review set mismatch')
    generic={**config};generic.pop('adapter',None)
    questions=[normalize(q, generic, i+1) for i,q in enumerate(raw)]
    all_by_id = {**by_id, **{q['id']: q for q in questions}}
    for q in questions:
        parent = all_by_id.get(q.get('parentQuestionId'))
        if parent and parent.get('familyId'):
            q.setdefault('familyId', family(parent))
    validate_reviews(raw, reviews, questions if config.get('adapter') != 'ipa-ap' else None, root)
    validate_questions(questions, generic, root, diagnostic=True, related_ids=set(all_by_id))
    for q, authored in zip(questions, raw):
        parent=all_by_id.get(q.get('parentQuestionId'))
        require('practice' not in question_uses(q) and q['id'] not in by_id, f"Invalid assessment pool: {q['id']}")
        require(origin(q) != 'derived' or parent is not None and origin(parent) != 'derived' and q['topicId']==parent['topicId'] and q['examPartId']==parent['examPartId'], f"Derived parent scope mismatch: {q['id']}")
        require(origin(q) != 'derived' or family(q) == family(parent), f"Derived family mismatch: {q['id']}")
        require(any(p['id']==q['examPartId'] and p['practiceAvailable'] for p in config['examParts']), f"Unsupported diagnostic part: {q['id']}")
        require(q['enrichment']=='reviewed' and all(q['choiceReasons']) and q['explanation'].strip() and (origin(q) != 'derived' or q['adaptation'].strip()), f"Incomplete assessment material: {q['id']}")
        review=review_by_id[q['id']]
        require(review.get('version')==q['version'] and review.get('sha256')==diagnostic_digest(authored), f"Stale diagnostic review: {q['id']}")
        require(isinstance(review.get('author'), str) and review['author'].strip() and isinstance(review.get('reviewer'), str) and review['reviewer'].strip() and review['author']!=review['reviewer'], f"Independent diagnostic reviewer missing: {q['id']}")
        checks=review.get('checks',{})
        require(all(checks.get(k) is True for k in ['source','answer','choices','wording']) and checks.get('calculation', 'not-applicable') in [True, 'not-applicable'], f"Incomplete assessment checks: {q['id']}")
        require(isinstance(review.get('notes'), str) and review['notes'].strip(), f"Missing diagnostic review evidence: {q['id']}")
        try:
            checked=datetime.fromisoformat(review['checkedAt'].replace('Z','+00:00'))
            require(checked.tzinfo is not None, 'Review time needs a timezone')
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError(f"Invalid diagnostic review date: {q['id']}") from error
    scopes = {}
    for q in originals + questions:
        scope=(q['topicId'],q['examPartId']);key=family(q)
        require(key not in scopes or scopes[key]==scope, f"A content family crosses topics or parts: {q['id']}")
        scopes[key]=scope
    filename,digest=hashed_json(directory, 'diagnostic', questions)
    fields = ['id', 'qualificationId', 'topicId', 'examPartId', 'enrichment', 'parentQuestionId', 'familyId', 'sourceKind', 'uses', 'sourceRecord', 'legalReview']
    return {'url':filename,'sha256':digest,'count':len(questions),'reviewed':len(questions),'index':[{k: q[k] for k in fields if k in q} for q in questions]}


def compile_mock_sets(root, config, originals, directory):
    if not config.get('mockSetSource'):
        return None
    path=root / config['mockSetSource']
    require(path.resolve().is_relative_to(root.resolve()), 'Mock sets outside repository')
    data=json.loads(path.read_text())
    require(data.get('format')=='hitomon-mock-sets' and data.get('version')==1 and data.get('qualificationId')==config['id'], 'Invalid mock header')
    published={q['id']:q for q in originals}
    if config.get('assessmentQuestionSource'):
        generic={**config};generic.pop('adapter',None)
        published.update({q['id']: normalize(q,generic,i+1) for i,q in enumerate(json.loads((root/config['assessmentQuestionSource']).read_text()))})
    for q in published.values():
        parent=published.get(q.get('parentQuestionId'))
        if parent and parent.get('familyId'):
            q.setdefault('familyId', family(parent))
    sets=[dict(s,version=s.get('version',1)) for s in data['sets'] if s['status']=='ready']
    require(len({s['id'] for s in sets})==len(sets), 'Duplicate mock set')
    for s in sets:
        require(SAFE_ID.fullmatch(s['id']) and isinstance(s['label'],str) and 0<len(s['label'])<=200 and type(s['version']) is int and s['version']>0, 'Invalid mock identity')
        require(valid_size(s['size']) and s['size']==len(s['slots']) and len({slot['questionId'] for slot in s['slots']})==s['size'], 'Mock requires unique fixed questions within bounds')
        require(len({family(published[slot['questionId']]) for slot in s['slots'] if slot['questionId'] in published}) == s['size'], 'Mock content families overlap')
        for i,slot in enumerate(s['slots']):
            q=published.get(slot['questionId'])
            require(slot['number']==i+1 and q and 'mock' in question_uses(q) and q['enrichment']=='reviewed' and ('parentQuestionId' not in slot or q.get('parentQuestionId')==slot['parentQuestionId']) and q['topicId']==slot['topicId'], 'Invalid fixed mock question')
    body={'format':'hitomon-mock-sets','version':1,'qualificationId':config['id'],'sets':sets}
    filename,digest=hashed_json(directory,'mockSets',body)
    return {'url':filename,'sha256':digest,'count':len(sets),'sets':[{**{k:s[k] for k in ['id','label','version','size']}, **({'hasLawChange':True} if any(published[slot['questionId']].get('legalReview',{}).get('status')=='outdated' for slot in s['slots']) else {})} for s in sets]}


def compile_learning_tools(root, config, questions, directory):
    """Optional curated context and cards. Keep ordinary questions immutable."""
    result = {}
    by_id = {q['id']: q for q in questions}
    raw_by_id = {q['id']: q for q in json.loads((root / config['questionSource']).read_text())}
    legacy_hashes = {}
    if config.get('adapter') == 'ipa-ap' and (root / 'work/ap/objective-quality/manifest.json').is_file():
        from ap_lesson_quality import legacy_classification_hashes
        legacy_hashes = legacy_classification_hashes(root)
    topics = {t['id'] for t in config['topics']}
    for key, source_key, format_name in [('studyContext', 'studyContextSource', 'hitomon-study-context'), ('flashcards', 'flashcardSource', 'hitomon-flashcards')]:
        if not config.get(source_key):
            continue
        source = (root / config[source_key]).resolve()
        require(source.is_relative_to(root.resolve()), 'Learning tool source outside repository')
        data = json.loads(source.read_text())
        require(data.get('format') == format_name and data.get('version') == 1 and data.get('qualificationId') == config['id'], 'Invalid learning tool header')
        records = data.get('items' if key == 'studyContext' else 'cards')
        require(isinstance(records, list) and len(records) <= 10000, 'Invalid learning tool records')
        ids = set()
        for item in records:
            require(isinstance(item, dict), 'Invalid learning tool item')
            identifier = item.get('questionId' if key == 'studyContext' else 'id')
            require(isinstance(identifier, str) and SAFE_ID.fullmatch(identifier) and identifier not in ids, 'Duplicate/invalid learning tool ID')
            ids.add(identifier)
            if key == 'studyContext':
                require(identifier in by_id and item.get('mode') in ['paperless', 'desk'] and isinstance(item.get('reason'), str) and 0 < len(item['reason']) <= 500, 'Invalid context classification')
                require(item.get('sourceHash') == diagnostic_digest(raw_by_id[identifier]) or
                        identifier in legacy_hashes and item.get('sourceHash') == legacy_hashes[identifier],
                        'Classification source changed: ' + identifier)
            else:
                require(type(item.get('version')) is int and item['version'] > 0 and item.get('topicId') in topics, 'Invalid card version/topic')
                item.setdefault('sourceNote', '')
                item.setdefault('relatedQuestionIds', [])
                require(all(isinstance(item.get(f), str) and (0 if f == 'sourceNote' else 1) <= len(item[f]) <= limit for f, limit in [('front', 200), ('back', 1000), ('sourceNote', 500)]), 'Invalid card text')
                refs = item['relatedQuestionIds']
                require(isinstance(refs, list) and len(refs) <= 10 and all(isinstance(ref, str) for ref in refs) and len(set(refs)) == len(refs) and all(ref in by_id for ref in refs), 'Invalid card references')
        if key == 'studyContext' and data.get('completedExamIds') is not None:
            completed = data['completedExamIds']
            pack_ids = {q['packId'] for q in questions}
            require(isinstance(completed, list) and all(isinstance(identifier, str) and identifier in pack_ids for identifier in completed) and len(set(completed)) == len(completed), 'Invalid completed classification packs')
            require(all(q['id'] in ids for q in questions if q['packId'] in completed), 'Incomplete classification pack')
        filename, digest = hashed_json(directory, key, data)
        result[key] = {'url': filename, 'sha256': digest, 'count': len(records)}
        if key == 'studyContext':
            result[key]['paperless'] = sum(item['mode'] == 'paperless' for item in records)
    return result


def compile_qualification(root, id):
    require(SAFE_ID.fullmatch(id), f'Invalid qualification ID: {id}')
    config = json.loads((root / 'content' / id / 'qualification.json').read_text())
    config.setdefault('shortName', config['name'])
    config.setdefault('topics', [{'id': 'general', 'name': '全般'}])
    config.setdefault('defaultExamPartId', 'objective')
    config.setdefault('examParts', [{'id': 'objective', 'label': '選択式', 'practiceAvailable': True}])
    require(len({p['id'] for p in config['examParts']}) == len(config['examParts']) and all(SAFE_ID.fullmatch(p['id']) and p.get('label') and isinstance(p.get('practiceAvailable'), bool) for p in config['examParts']), 'Invalid exam parts')
    require(config['defaultExamPartId'] in {p['id'] for p in config['examParts']}, 'Invalid default exam part')
    require(all(all(isinstance(p[k],str) and 0<len(p[k])<=20 for k in ['caseLabel','countLabel'] if k in p) for p in config['examParts']), 'Invalid case unit label')
    require(type(config.get('requiresLegalContext',False)) is bool,'Invalid legal context setting')
    require(type(config.get('requiresReviewedContent',False)) is bool,'Invalid reviewed content setting')
    require(config['id'] == id, 'Qualification ID mismatch')
    require(len({t['id'] for t in config['topics']}) == len(config['topics']), 'Duplicate topic ID')
    require(all(SAFE_ID.fullmatch(t['id']) and isinstance(t['name'], str) and t['name'] for t in config['topics']), 'Invalid topic')
    limits=config.get('diagnosticBlueprint',{}).get('variantLimits',{})
    b = config.get('diagnosticBlueprint', {})
    if b:
        size = b.get('size')
        require(valid_size(size, 30), 'Diagnostic size must be 30..200')
        require(b.get('sampling', 'topic-round-robin') in ['topic-round-robin', 'topic-weighted'] and type(b.get('defaultVariantLimit', 1)) is int and 0 <= b.get('defaultVariantLimit', 1) <= size, 'Invalid diagnostic policy')
        require(isinstance(limits,dict) and all(k in {t['id'] for t in config['topics']} and type(v) is int and 0<=v<=size for k,v in limits.items()), 'Invalid diagnostic variant limits')
        weights=b.get('weights', {})
        require(isinstance(weights, dict) and all(k in {t['id'] for t in config['topics']} and type(v) is int and 0 < v <= 100000 for k,v in weights.items()) and (bool(weights) if b.get('sampling') == 'topic-weighted' else not weights), 'Invalid diagnostic weights')
    syllabuses=config.get('syllabuses', [])
    require(isinstance(syllabuses,list) and len(syllabuses)<=100 and len({s['id'] for s in syllabuses})==len(syllabuses) and all(set(s)<= {'id','label','language','effectiveFrom','effectiveTo'} and SAFE_ID.fullmatch(s['id']) and isinstance(s.get('label'),str) and 0<len(s['label'])<=300 and isinstance(s.get('language'),str) and re.fullmatch(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*', s['language']) for s in syllabuses), 'Invalid syllabuses')
    for scope in syllabuses:
        for key in ['effectiveFrom', 'effectiveTo']:
            if key in scope:
                require(isinstance(scope[key], str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', scope[key]), 'Invalid syllabus date')
                try:datetime.strptime(scope[key], '%Y-%m-%d')
                except ValueError as error:raise ValueError('Invalid syllabus date') from error
        require(not scope.get('effectiveFrom') or not scope.get('effectiveTo') or scope['effectiveFrom']<=scope['effectiveTo'], 'Syllabus date order')
    require('defaultSyllabusId' not in config or config['defaultSyllabusId'] in {s['id'] for s in syllabuses}, 'Unknown default syllabus')
    objectives=config.get('objectives', [])
    require(isinstance(objectives,list) and len(objectives)<=1000 and len({o['id'] for o in objectives})==len(objectives) and all(set(o)<= {'id','label','topicId'} and SAFE_ID.fullmatch(o['id']) and isinstance(o.get('label'),str) and 0<len(o['label'])<=300 and o['topicId'] in {t['id'] for t in config['topics']} for o in objectives), 'Invalid objectives')
    require(len({t['name'] for t in config['topics']}) == len(config['topics']), 'Duplicate topic name')
    source = root / config['questionSource']
    require(source.resolve().is_relative_to(root.resolve()), 'Question source is outside the repository')
    raw = json.loads(source.read_text())
    if config.get('adapter') == 'ipa-ap' and id == 'ap':
        from ap_lesson_quality import validate_workspace
        validate_workspace(root)
    questions = [normalize(q, config, i+1) for i,q in enumerate(raw)]
    by_id = {q['id']:q for q in questions}
    for q in questions:
        parent=by_id.get(q.get('parentQuestionId'))
        if parent and parent.get('familyId'):
            q.setdefault('familyId', family(parent))
    if config.get('adapter') != 'ipa-ap' and any(q['enrichment']=='reviewed' for q in questions):
        require(config.get('questionReviewSource'), 'Reviewed ordinary material needs a review source')
    if config.get('questionReviewSource'):
        review_path=(root/config['questionReviewSource']).resolve()
        require(review_path.is_relative_to(root.resolve()), 'Reviews outside repository')
        validate_reviews(raw,json.loads(review_path.read_text()),questions if config.get('adapter') != 'ipa-ap' else None,root)
    validate_questions(questions, config, root)
    directory = root / 'data' / 'qualifications' / id
    grouped = defaultdict(list)
    for q in questions:
        grouped[q['packId']].append(q)
    packs = []
    index = []
    for pack_id, records in grouped.items():
        filename, digest = hashed_json(directory / 'packs', pack_id, records)
        packs.append({'id': pack_id, 'label': records[0]['packLabel'], 'url': f'packs/{filename}', 'sha256': digest, 'count': len(records), 'reviewed': sum(q['enrichment'] == 'reviewed' for q in records)})
        for q in records:
            # The index supports searching/scoping/offline availability, not lesson rendering.
            fields = ['id','qualificationId','examPartId','packId','packLabel','version','number','title','topic','topicId','topicDescription','concept','searchText','year','season','enrichment','hintStatus','sourceImages','imageSizes','image','imageAlt','related','stem','answer','correctChoiceId','correctChoiceIds','selection','grading','type','choicePresentation','uses','sourceKind','familyId','syllabusId','syllabus','language','objectiveIds','objectivesSnapshot','sourceRefs','sourceRecord','legalReview']
            item = {k: q[k] for k in fields if k in q}
            item['choices'] = [{k: v for k, v in c.items() if k != 'text'} for c in q['choices']]
            item['hintCount'] = len(q['hints'])
            index.append(item)
    filename, digest = hashed_json(directory, 'index', index)
    assessment=compile_assessments(root, config, questions, directory)
    public_config = {k: v for k, v in config.items() if k not in ['adapter', 'questionSource', 'questionReviewSource', 'assessmentQuestionSource', 'assessmentReviewSource', 'studyContextSource', 'flashcardSource', 'mockSetSource', 'caseSource', 'caseReviewSource']}
    manifest = {**public_config, 'count': len(questions), 'reviewed': sum(q['enrichment'] == 'reviewed' for q in questions), 'index': {'url': filename, 'sha256': digest}, 'packs': packs}
    if assessment is not None:
        manifest['assessment']=assessment
    mock_sets=compile_mock_sets(root,config,questions,directory)
    if mock_sets is not None:manifest['mockSets']=mock_sets
    cases=compile_cases(root,config,directory,hashed_json)
    if cases is not None:manifest['cases']=cases
    require(questions or cases and cases['count'], f'Empty qualification: {id}')
    targets=[]
    case_counts=defaultdict(int)
    if cases:
        for case in json.loads((directory / cases['url']).read_text())['cases']:
            case_counts[case['examPartId']]+=1
    for part in config['examParts']:
        if not part['practiceAvailable']:
            continue
        unit=part.get('unit', 'questionAttempts')
        count=case_counts[part['id']] if unit == 'cases' else sum(q['examPartId'] == part['id'] and 'practice' in q.get('uses', ['practice']) and not q.get('diagnosticOnly') for q in questions)
        if count:
            targets.append({'examPartId': part['id'], 'label': part['label'], 'unit': unit, 'count': count, **{k:part[k] for k in ['caseLabel','countLabel'] if k in part}})
    manifest['studyTargets']=targets
    available_parts={t['examPartId'] for t in targets}
    manifest['examParts']=[{**p,'practiceAvailable':p['practiceAvailable'] and p['id'] in available_parts} for p in config['examParts']]
    manifest.update(compile_learning_tools(root, config, questions, directory))
    manifest['offline']=compile_offline(root,manifest,questions,directory,hashed_json)
    write_json(directory / 'manifest.json', manifest)
    return {'id': id, 'name': config['name'], 'shortName': config['shortName'], 'url': f'{id}/manifest.json', 'count': len(questions), 'defaultExamPartId': config['defaultExamPartId'], 'studyTargets': targets}, config


def build(root):
    settings = json.loads((root / 'content' / 'qualifications.json').read_text())
    require(len(set(settings['qualifications'])) == len(settings['qualifications']), 'Duplicate qualification')
    results = [compile_qualification(root, id) for id in settings['qualifications']]
    write_json(root / 'data' / 'qualifications' / 'catalog.json', {'qualifications': [record for record, _ in results]})
    template = (root / 'templates' / 'study.html').read_text()
    for record, config in results:
        html = template.replace('<html lang="ja">', f'<html lang="ja" data-qualification="{record["id"]}">').replace('<head>', '<head>\n  <base href="../">', 1)
        html = html.replace('ひと問｜応用情報の過去問学習', f'ひと問｜{html_tools.escape(config["shortName"])}の学習')
        description=html_tools.escape(config.get('description', f'{config["name"]}を1問ずつ。段階ヒント、解説、学習記録、解き直し。'), quote=True)
        html=re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">', html)
        destination = root / record['id'] / 'index.html'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(html)
    # One qualification keeps the existing immediate start. The shared controller
    # displays a chooser at the root when the catalog has multiple qualifications.
    (root / 'index.html').write_text(template)
    print('Built', ', '.join(f"{r['id']}: {r['count']} questions" for r, _ in results))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    build(parser.parse_args().root.resolve())
