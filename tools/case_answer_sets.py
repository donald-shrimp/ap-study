"""Compile answer controls from reviewed cases without changing the source cases."""

import hashlib
import json
import re
from collections import defaultdict


from case_field import normalize_answer_text, validate_case_field


def choices_from_prompt(prompt):
    start = re.search(r'(?m)^ *(?:解答群[：:]?\s*|(?=ア[ \t　]))', prompt)
    assert start, 'Missing choice group in the reviewed prompt'
    entries = re.split(r'(?:^|[\s／])([ア-ン])[ \t　]+', prompt[start.end():].strip())
    assert not entries[0] and len(entries) >= 5, 'Invalid choice group in the reviewed prompt'
    choices = list(zip(entries[1::2], map(str.strip, entries[2::2])))
    assert all(text for _, text in choices) and len({label for label, _ in choices}) == len(choices)
    return prompt[:start.start()].rstrip(), choices


def choices_from_table(body, caption):
    _, found, rows = body.partition(caption+'\n')
    assert found, 'Missing choice table in the reviewed passage'
    lines = rows.lstrip('\n').splitlines()
    assert all(line.startswith('|') for line in lines[:3]), 'Invalid choice table'
    result = []
    for line in lines[2:]:
        if not line.startswith('|'):
            break
        result.append((line.split('|')[1].strip(), ''))
    return result


def compile_answer_sets(root, config, cases, canonical):
    source = config.get('caseAnswerSetSource')
    if not source:
        return {}
    path = (root / source).resolve()
    assert path.is_relative_to(root.resolve())
    authored = json.loads(path.read_text(encoding='utf-8'))
    originals = {case['id']: case for case in cases}
    result = {}
    for entry in authored:
        case_id = entry['caseId']
        assert case_id not in result and set(entry) == {'caseId', 'caseVersion', 'baseSHA256', 'groups'}
        case = originals[case_id]
        assert type(entry['caseVersion']) is int and entry['caseVersion'] > case['version']
        assert entry['baseSHA256'] == hashlib.sha256(canonical(case)).hexdigest(), (case_id, 'Answer sets require a matching source case')
        items = {item['id']: item for item in case['items']}
        used = defaultdict(set)
        changes = {}
        for group in entry['groups']:
            assert {'itemId', 'fieldIds', 'answers'} <= group.keys() <= {'itemId', 'fieldIds', 'answers', 'slots', 'choiceSource', 'maxLength', 'copyEdits'}
            item = items[group['itemId']]
            ids = group['fieldIds']
            assert ids and len(set(ids)) == len(ids) and not used[item['id']].intersection(ids)
            before = [field for field in item['fields'] if field['id'] in ids]
            assert [field['id'] for field in before] == ids and all(field['grading']['method'] == 'self' for field in before)
            answers = group['answers']
            assert 2 <= len(answers) <= 20 and all(isinstance(value, str) and value.strip() for value in answers)
            assert len(set(map(normalize_answer_text, answers))) == len(answers)
            if len(before) > 1:
                assert set(answers) == {value for field in before for value in field['referenceAnswers']}
            else:
                original, = before[0]['referenceAnswers']
                original = re.sub(r'(^|／)[a-z]：', r'\1', original)
                squash = lambda value: re.sub(r'[,/“”\s]', '', normalize_answer_text(value))
                assert squash(original) == squash(''.join(answers)), (case_id, item['id'], original)
            slots = group.get('slots')
            limit = group.get('maxLength')
            field = {k: before[0][k] for k in ('id', 'label', 'explanation', 'rubric')}
            for before_text, after_text in group.get('copyEdits', []):
                assert before_text and any(before_text in text for text in [field['explanation'], *field['rubric']])
                field['explanation'] = field['explanation'].replace(before_text, after_text)
                field['rubric'] = [text.replace(before_text, after_text) for text in field['rubric']]
            assert field['explanation'] and all(field['rubric'])
            field.update(type='answerSet', grading={'method': 'unordered'}, referenceAnswers=answers)
            settings = field['answerSet'] = {'sourceFieldIds': ids}
            if slots:
                assert len(slots) == len(answers) and len(set(slots)) == len(slots) and all(isinstance(label, str) and 0 < len(label) <= 50 for label in slots)
                settings['slots'] = slots
                if len(ids) > 1:
                    field['label'] = '・'.join(slots)
            if limit:
                assert slots and type(limit) is int and 1 <= limit <= 200 and all(len(value) <= limit for value in answers)
                settings['maxLength'] = limit
            change = changes.setdefault(item['id'], {'prompt': item['prompt'], 'groups': []})
            choice_source = group.get('choiceSource')
            if choice_source:
                assert not limit
                if choice_source == 'prompt':
                    question, choices = choices_from_prompt(item['prompt'])
                    # One ordinary choice field may already use the same group.
                    # The new choice controls still carry the full original options.
                    change['prompt'] = question
                else:
                    choices = choices_from_table(case['body'], choice_source)
                assert 2 <= len(choices) <= 20 and set(answers) <= {label for label, _ in choices}
                field['choices'] = [{'id': f'choice-{n}', 'label': label, 'text': text} for n, (label, text) in enumerate(choices, 1)]
            validate_case_field(field)
            used[item['id']].update(ids)
            change['groups'].append(field)
        assert changes
        result[case_id] = {'version': entry['caseVersion'], 'items': changes}
    return result
