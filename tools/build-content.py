"""Compile qualification settings and source questions into static, hashed packs.

IPA's 80-question/source verification stays in corpus.py and the AP authoring tools.
This compiler has no fixed exam years, question count, choice count, or hint count.
"""
import argparse
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


def validate_questions(questions, config, root):
    ids = set()
    for q in questions:
        require(SAFE_ID.fullmatch(q['id']) and q['id'] not in ids, f"Duplicate/invalid question ID: {q['id']}")
        ids.add(q['id'])
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
        require(1 <= len(q['hints']) <= 20 and all(h['title'] and h['text'] and isinstance(h['revealsAnswer'], bool) for h in q['hints']), f"Invalid hints: {q['id']}")
        require(all(isinstance(q[f], str) for f in ['summary', 'explanation', 'takeaway', 'source']), f"Invalid text: {q['id']}")
        require(q['stem'] or q['sourceImages'], f"Missing question body: {q['id']}")
        require(len(q['sourceImages']) == len(q['imageSizes']), f"Missing image sizes: {q['id']}")
        for asset in q['sourceImages'] + [q.get('image')] + [c.get('image') for c in q['choices']]:
            if asset:
                require(not re.search(r'[<>\"\x00-\x1f]', asset) and "'" not in asset and not asset.startswith(('http:', 'https:', '//')) and (root / asset).is_file() and (root / asset).resolve().is_relative_to(root.resolve()), f"Missing/unsafe asset: {q['id']} {asset}")
    for q in questions:
        require(all(ref in ids for ref in q['related']), f"Missing related question: {q['id']}")


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
    public_config = {k: v for k, v in config.items() if k not in ['adapter', 'questionSource']}
    manifest = {**public_config, 'count': len(questions), 'reviewed': sum(q['enrichment'] == 'reviewed' for q in questions), 'index': {'url': filename, 'sha256': digest}, 'packs': packs}
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
