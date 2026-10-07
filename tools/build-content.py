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

ROOT = Path(__file__).resolve().parents[1]
SAFE_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$')


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


def normalize(raw, config):
    q = dict(raw)
    q['qualificationId'] = config['id']
    q.setdefault('examPartId', config.get('defaultExamPartId', 'objective'))
    q.setdefault('type', 'singleChoice')
    require(q['type'] == 'singleChoice', f"Unsupported question type: {q['id']}")
    if config.get('adapter') == 'ipa-ap':
        q['packId'] = q['id'].split('-q', 1)[0]
        label = config['seasonLabels'][q['season']]
        q['packLabel'] = f"{q['year']}年 {label}"
        q['topicId'] = next(t['id'] for t in config['topics'] if t['name'] == q['topic'])
        q['choices'] = [dict(c, id=f'choice-{i}') for i, c in enumerate(q['choices'])]
        q['correctChoiceId'] = q['choices'][q['answer']]['id']
    else:
        topic = next(t for t in config['topics'] if t['id'] == q['topicId'])
        q['topic'] = topic['name']
        require(q.get('packLabel'), f"Missing pack label: {q['id']}")
        q['choices'] = [dict(c) for c in q['choices']]
        require('correctChoiceId' in q, f"Missing correct choice ID: {q['id']}")
        q['answer'] = next((i for i, c in enumerate(q['choices']) if c['id'] == q['correctChoiceId']), -1)
    for field, default in {
        'version': 1, 'year': None, 'season': '', 'concept': '', 'topicDescription': '',
        'sourceImages': [], 'imageSizes': [], 'stem': '', 'related': [], 'adaptation': '',
        'searchText': '', 'hintStatus': 'individual', 'page': None,
    }.items():
        q.setdefault(field, default)
    return q


def validate_questions(questions, config, root, diagnostic=False):
    ids = set()
    for q in questions:
        require(SAFE_ID.fullmatch(q['id']) and q['id'] not in ids, f"Duplicate/invalid question ID: {q['id']}")
        ids.add(q['id'])
        require(diagnostic or 'diagnosticOnly' not in q and 'parentQuestionId' not in q, f"Diagnostic question in ordinary source: {q['id']}")
        require(q['examPartId'] in {p['id'] for p in config['examParts']}, f"Invalid exam part: {q['id']}")
        require(SAFE_ID.fullmatch(q['packId']), f"Invalid pack ID: {q['id']}")
        require(isinstance(q['title'], str) and q['title'], f"Missing title: {q['id']}")
        require(isinstance(q.get('number'), int) and q['number'] > 0, f"Missing question number: {q['id']}")
        require(isinstance(q['version'], int) and q['version'] > 0, f"Invalid version: {q['id']}")
        require(2 <= len(q['choices']) <= 20, f"Invalid choice count: {q['id']}")
        choice_ids = [c['id'] for c in q['choices']]
        require(len(set(choice_ids)) == len(choice_ids) and all(SAFE_ID.fullmatch(c) for c in choice_ids), f"Invalid choice IDs: {q['id']}")
        require(q['correctChoiceId'] in choice_ids and q['answer'] >= 0, f"Invalid answer: {q['id']}")
        require(all(isinstance(c.get('label'), str) and c['label'] for c in q['choices']), f"Missing choice label: {q['id']}")
        require(q['enrichment'] in ['reviewed', 'topic-guide'], f"Invalid lesson state: {q['id']}")
        require(len(q['choiceReasons']) == (len(q['choices']) if q['enrichment'] == 'reviewed' else 0), f"Invalid reasons: {q['id']}")
        require((0 if diagnostic else 1) <= len(q['hints']) <= 20 and all(h['title'] and h['text'] and isinstance(h['revealsAnswer'], bool) for h in q['hints']), f"Invalid hints: {q['id']}")
        require(all(isinstance(q[f], str) for f in ['summary', 'explanation', 'takeaway', 'source']), f"Invalid text: {q['id']}")
        require(q['stem'] or q['sourceImages'], f"Missing question body: {q['id']}")
        require(len(q['sourceImages']) == len(q['imageSizes']), f"Missing image sizes: {q['id']}")
        for asset in q['sourceImages'] + [q.get('image')] + [c.get('image') for c in q['choices']]:
            if asset:
                require(not re.search(r'[<>\"\x00-\x1f]', asset) and "'" not in asset and not asset.startswith(('http:', 'https:', '//')) and (root / asset).is_file() and (root / asset).resolve().is_relative_to(root.resolve()), f"Missing/unsafe asset: {q['id']} {asset}")
    for q in questions:
        require(all(ref in ids for ref in q['related']), f"Missing related question: {q['id']}")


def diagnostic_digest(raw):
    """Hash the authored object, including choices and explanations, before defaults."""
    return hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def compile_diagnostics(root, config, originals, directory):
    if 'diagnosticQuestionSource' not in config:
        return None
    def source(key):
        path=root / config[key]
        require(path.resolve().is_relative_to(root.resolve()), 'Diagnostic source is outside the repository')
        return json.loads(path.read_text())
    raw=source('diagnosticQuestionSource');reviews=source('diagnosticReviewSource')
    require(isinstance(raw, list) and isinstance(reviews, list), 'Diagnostic sources must be lists')
    by_id={q['id']:q for q in originals};review_by_id={r['questionId']:r for r in reviews}
    require(len(review_by_id)==len(reviews), 'Duplicate diagnostic review')
    require(set(review_by_id)=={q['id'] for q in raw}, 'Diagnostic review set mismatch')
    generic={**config};generic.pop('adapter',None)
    questions=[normalize({**q, 'hints':q.get('hints',[])}, generic) for q in raw]
    validate_questions(questions, generic, root, diagnostic=True)
    for q, authored in zip(questions, raw):
        parent=by_id.get(q.get('parentQuestionId'))
        require(q.get('diagnosticOnly') is True and q['id'] not in by_id and parent is not None, f"Invalid diagnostic parent: {q['id']}")
        require(q['topicId']==parent['topicId'] and q['examPartId']==parent['examPartId'], f"Diagnostic parent scope mismatch: {q['id']}")
        require(any(p['id']==q['examPartId'] and p['practiceAvailable'] for p in config['examParts']), f"Unsupported diagnostic part: {q['id']}")
        require(q['enrichment']=='reviewed' and all(q['choiceReasons']) and q['explanation'].strip() and q['summary'].strip() and q['source'].strip() and q['adaptation'].strip(), f"Incomplete diagnostic material: {q['id']}")
        review=review_by_id[q['id']]
        require(review.get('version')==q['version'] and review.get('sha256')==diagnostic_digest(authored), f"Stale diagnostic review: {q['id']}")
        require(isinstance(review.get('author'), str) and review['author'].strip() and isinstance(review.get('reviewer'), str) and review['reviewer'].strip() and review['author']!=review['reviewer'], f"Independent diagnostic reviewer missing: {q['id']}")
        checks=review.get('checks',{})
        require(all(checks.get(k) is True for k in ['source','answer','calculation','choices','wording']), f"Incomplete diagnostic checks: {q['id']}")
        require(isinstance(review.get('notes'), str) and review['notes'].strip(), f"Missing diagnostic review evidence: {q['id']}")
        try:
            checked=datetime.fromisoformat(review['checkedAt'].replace('Z','+00:00'))
            require(checked.tzinfo is not None, 'Review time needs a timezone')
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError(f"Invalid diagnostic review date: {q['id']}") from error
    filename,digest=hashed_json(directory, 'diagnostic', questions)
    return {'url':filename,'sha256':digest,'count':len(questions),'reviewed':len(questions)}


def compile_learning_tools(root, config, questions, directory):
    """Optional curated context and cards. Keep ordinary questions immutable."""
    result = {}
    by_id = {q['id']: q for q in questions}
    raw_by_id = {q['id']: q for q in json.loads((root / config['questionSource']).read_text())}
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
                require(item.get('sourceHash') == diagnostic_digest(raw_by_id[identifier]), 'Classification source changed: ' + identifier)
            else:
                require(type(item.get('version')) is int and item['version'] > 0 and item.get('topicId') in topics, 'Invalid card version/topic')
                require(all(isinstance(item.get(f), str) and 0 < len(item[f]) <= limit for f, limit in [('front', 200), ('back', 1000), ('sourceNote', 500)]), 'Invalid card text')
                refs = item.get('relatedQuestionIds')
                require(isinstance(refs, list) and 1 <= len(refs) <= 10 and all(isinstance(ref, str) for ref in refs) and len(set(refs)) == len(refs) and all(ref in by_id and by_id[ref]['topicId'] == item['topicId'] for ref in refs), 'Invalid card references')
        filename, digest = hashed_json(directory, key, data)
        result[key] = {'url': filename, 'sha256': digest, 'count': len(records)}
        if key == 'studyContext':
            result[key]['paperless'] = sum(item['mode'] == 'paperless' for item in records)
    return result


def compile_qualification(root, id):
    require(SAFE_ID.fullmatch(id), f'Invalid qualification ID: {id}')
    config = json.loads((root / 'content' / id / 'qualification.json').read_text())
    config.setdefault('defaultExamPartId', 'objective')
    config.setdefault('examParts', [{'id': 'objective', 'label': '選択式', 'practiceAvailable': True}])
    require(len({p['id'] for p in config['examParts']}) == len(config['examParts']) and all(SAFE_ID.fullmatch(p['id']) and p.get('label') and isinstance(p.get('practiceAvailable'), bool) for p in config['examParts']), 'Invalid exam parts')
    require(config['defaultExamPartId'] in {p['id'] for p in config['examParts']}, 'Invalid default exam part')
    require(config['id'] == id, 'Qualification ID mismatch')
    require(len({t['id'] for t in config['topics']}) == len(config['topics']), 'Duplicate topic ID')
    require(all(SAFE_ID.fullmatch(t['id']) and isinstance(t['name'], str) and t['name'] for t in config['topics']), 'Invalid topic')
    limits=config.get('diagnosticBlueprint',{}).get('variantLimits',{})
    require(isinstance(limits,dict) and all(k in {t['id'] for t in config['topics']} and type(v) is int and 0<=v<=30 for k,v in limits.items()), 'Invalid diagnostic variant limits')
    require(len({t['name'] for t in config['topics']}) == len(config['topics']), 'Duplicate topic name')
    source = root / config['questionSource']
    require(source.resolve().is_relative_to(root.resolve()), 'Question source is outside the repository')
    questions = [normalize(q, config) for q in json.loads(source.read_text())]
    require(questions, f'Empty qualification: {id}')
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
            fields = ['id','qualificationId','examPartId','packId','packLabel','version','number','title','topic','topicId','topicDescription','concept','searchText','year','season','enrichment','hintStatus','sourceImages','imageSizes','image','imageAlt','related','stem','answer','correctChoiceId','type']
            item = {k: q[k] for k in fields if k in q}
            item['choices'] = [{k: v for k, v in c.items() if k != 'text'} for c in q['choices']]
            item['hintCount'] = len(q['hints'])
            index.append(item)
    filename, digest = hashed_json(directory, 'index', index)
    diagnostic=compile_diagnostics(root, config, questions, directory)
    public_config = {k: v for k, v in config.items() if k not in ['adapter', 'questionSource', 'diagnosticQuestionSource', 'diagnosticReviewSource', 'studyContextSource', 'flashcardSource']}
    manifest = {**public_config, 'count': len(questions), 'reviewed': sum(q['enrichment'] == 'reviewed' for q in questions), 'index': {'url': filename, 'sha256': digest}, 'packs': packs}
    if diagnostic is not None:
        manifest['diagnostic']=diagnostic
    manifest.update(compile_learning_tools(root, config, questions, directory))
    write_json(directory / 'manifest.json', manifest)
    return {'id': id, 'name': config['name'], 'shortName': config['shortName'], 'url': f'{id}/manifest.json', 'count': len(questions)}, config


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
