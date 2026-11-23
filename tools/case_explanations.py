"""Compile selected, version-pinned whole-case explanations for the app."""

import hashlib
import json
import re
from collections import defaultdict

from written_content import canonical


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_markdown(text, case_id, links):
    title, _, body = text.partition('\n')
    require(title.startswith('# ') and title[2:].strip(), f'{case_id}: missing title')
    introduction = []
    sections = []
    lines = introduction
    fence = None
    for line in body.splitlines():
        stripped = line.strip()
        if fence:
            lines.append(line)
            if stripped == fence:
                fence = None
            continue
        if stripped.startswith('```') or stripped == '$$':
            fence = '```' if stripped.startswith('```') else '$$'
        heading = re.fullmatch(r'(#{2,3}) (\S.*)', line)
        if heading:
            level, label = heading.groups()
            lines = []
            sections.append({'level': len(level), 'heading': label.rstrip(), 'lines': lines})
        else:
            lines.append(line)
    require(fence is None, f'{case_id}: unclosed code or math block')
    require(sections, f'{case_id}: no sections')
    by_heading = defaultdict(list)
    for link in links:
        by_heading[link['heading']].append({k: link[k] for k in ('id', 'itemId', 'fieldIds')})
    for heading in by_heading:
        require(sum(s['heading'] == heading for s in sections) == 1, f'{case_id}: missing or ambiguous heading {heading}')
    require(all(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', link['id']) for link in links), f'{case_id}: invalid link id')

    # A linked section keeps its primary anchor. Each additional link keeps its
    # own reference to that section and its exact subset of answer fields.
    seen_link = False
    for index, section in enumerate(sections):
        refs = by_heading[section['heading']]
        seen_link = seen_link or bool(refs)
        section.update(id=refs[0]['id'] if refs else f'heading-{index + 1}', links=refs,
                       openByDefault=not seen_link, text='\n'.join(section.pop('lines')).strip())
    require(len({s['id'] for s in sections}) == len(sections), f'{case_id}: duplicate section id')
    return {'title': title[2:].strip(), 'introduction': '\n'.join(introduction).strip(), 'sections': sections}


def compile_case_explanations(root, config, case_bank, directory, hashed_json):
    if not config.get('caseExplanationSource'):
        return None
    plan = json.loads((root / config['caseExplanationSource']).read_text(encoding='utf-8'))
    require(plan['format'] == 'hitomon-case-explanation-selection' and plan['version'] == 1, 'Unknown explanation selection format')
    library = root / 'work/ap/case-explanations'
    batches = json.loads((library / 'catalog.json').read_text(encoding='utf-8'))['batches']
    sources = {c['id']: (c, c.get('draftDirectory', batch['directory'])) for batch in batches for c in batch['cases']}
    require(len(sources) == sum(len(b['cases']) for b in batches), 'Duplicate explanation source')
    cases = {c['id']: c for c in json.loads((directory / case_bank['url']).read_text(encoding='utf-8'))['cases']}
    packs = {e['caseId']: e['packId'] for e in case_bank['index']}
    grouped = defaultdict(list)
    selected = set()
    for entry in plan['cases']:
        case_id = entry['caseId']
        require(case_id not in selected and case_id in sources and case_id in cases, f'{case_id}: invalid selection')
        selected.add(case_id)
        case = cases[case_id]
        require(entry['caseVersion'] == case['version'] and entry['caseSHA256'] == digest(canonical(case)), f'{case_id}: case material changed')
        source, folder = sources[case_id]
        source_dir = (library / folder).resolve()
        draft = (source_dir / source.get('file', f'{case_id}.md')).resolve()
        require(draft.is_relative_to(library.resolve()) and source_dir.is_relative_to(library.resolve()), f'{case_id}: source outside library')
        raw = draft.read_bytes().replace(b'\r\n', b'\n')
        links = json.loads((source_dir / 'explanation-links.json').read_text(encoding='utf-8'))[case_id]
        require(entry['markdownSHA256'] == digest(raw) and entry['linksSHA256'] == digest(canonical(links)), f'{case_id}: selected explanation changed')
        expected = [(item['id'], field['id']) for item in case['items'] for field in item['fields']]
        actual = [(link['itemId'], field_id) for link in links for field_id in link['fieldIds']]
        require(sorted(expected) == sorted(actual), f'{case_id}: answer field coverage differs')
        require(all(link['fieldIds'] for link in links) and len({link['id'] for link in links}) == len(links), f'{case_id}: invalid links')
        grouped[packs[case_id]].append({
            'caseId': case_id, 'caseVersion': case['version'],
            'revision': digest(canonical(entry)),
            **parse_markdown(raw.decode('utf-8-sig'), case_id, links),
        })

    records = []
    for pack_id, entries in grouped.items():
        name, sha = hashed_json(directory, f'case-explanations-{pack_id}', {
            'format': 'hitomon-case-explanation-pack', 'version': 1,
            'qualificationId': config['id'], 'packId': pack_id, 'cases': entries,
        })
        records.append({'packId': pack_id, 'url': name, 'sha256': sha,
                        'cases': [{k: c[k] for k in ('caseId', 'caseVersion', 'revision')} for c in entries]})
    return records
