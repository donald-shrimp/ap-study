"""Validate and publish display-only revisions against reviewed case snapshots."""

import hashlib
import json
import re

from case_field import normalize_answer_text
from material_contracts import require


def _field_map(case):
    return {item['id'] + '--' + field['id']: field for item in case['items'] for field in item['fields']}


def _effective_case(case, revision):
    if not revision:
        return case
    items = []
    for item in case['items']:
        change = revision['items'].get(item['id'])
        if not change:
            items.append(item)
            continue
        replaced = {key: group for group in change['groups'] for key in group['answerSet']['sourceFieldIds']}
        fields = []
        for field in item['fields']:
            group = replaced.get(field['id'])
            if group is None or group['id'] == field['id']:
                fields.append(group if group is not None else field)
        items.append({**item, 'prompt': change['prompt'], 'fields': fields})
    return {**case, 'version': revision['version'], 'items': items}


def _normalized_prose(text):
    return re.sub(r'[\s、。,.]+', '', normalize_answer_text(text).replace('**', ''))


def _prose(text, limit):
    return isinstance(text, str) and 0 < len(text.strip()) <= limit


def _validate_field(feedback, field, figure_anchors):
    explanation = feedback.get('explanation')
    require(set(feedback) <= {'explanation', 'rubric', 'reviewPoint', 'answerLabels', 'source'}
            and _prose(explanation, 20000), 'Missing or invalid explanation')
    rubric = feedback.get('rubric', [])
    # Numeric inputs can also need self assessment when the input cannot be parsed.
    uses_self = field['type'] != 'singleChoice' and not field.get('choices')
    require(isinstance(rubric, list) and len(rubric) <= 20 and (rubric or not uses_self)
            and all(_prose(point, 2000) for point in rubric), 'Missing or invalid self-assessment criteria')
    point = feedback.get('reviewPoint')
    require('reviewPoint' not in feedback or _prose(point, 2000), 'Invalid review point')
    notes = [_normalized_prose(note) for note in [explanation, *rubric, *([point] if point else [])]]
    require(len(set(notes)) == len(notes) and not any('公式採点・部分点基準ではない' in note for note in notes),
            'Repeated explanation or boilerplate')
    if 'answerLabels' in feedback:
        labels = feedback['answerLabels']
        choices = field.get('choices')
        if choices:
            require(field['type'] == 'singleChoice'
                    and all(choice['text'].strip() in ('', choice['label']) for choice in choices),
                    'Answer labels require symbol-only choices')
            correct_ids = field.get('correctChoiceIds')
            refs = ({choice['label'] for choice in choices if choice['id'] in correct_ids}
                    if correct_ids is not None else set(field['referenceAnswers']))
        else:
            refs = {part.strip() for value in field.get('referenceAnswers', [])
                    for part in re.split(r'[,，、／/]', value)}
        require(isinstance(labels, dict) and bool(labels) and set(labels) == refs
                and all(_prose(label, 500) for label in labels.values()), 'Answer labels do not match the reviewed keys')
    if 'source' in feedback:
        source = feedback['source']
        require(isinstance(source, dict) and set(source) == {'label', 'anchor'}
                and _prose(source['label'], 30) and source['anchor'] in figure_anchors, 'Unmatched source figure')


def compile_case_feedback(root, config, cases, revisions, canonical):
    if not config.get('caseFeedbackSource'):
        return {}
    paths = [(root / config[key]).resolve() for key in ('caseFeedbackSource', 'caseFeedbackReviewSource')]
    require(all(path.is_relative_to(root.resolve()) for path in paths), 'Feedback source outside repository')
    authored, evidence = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
    approvals = {entry['caseId']: entry for entry in evidence}
    material = {case['id']: case for case in cases}
    result = {}
    for entry in authored:
        case_id = entry['caseId']
        require(case_id in material and case_id not in result
                and set(entry) == {'caseId', 'caseHashes', 'fields'}, 'Invalid case feedback entry')
        approved = approvals[case_id]
        require(approved['status'] == 'approved' and approved['author'] != approved['reviewer']
                and bool(approved['author']) and bool(approved['reviewer'])
                and approved['feedbackSHA256'] == hashlib.sha256(canonical(entry)).hexdigest(),
                f'{case_id}: feedback has no matching approval')
        original = material[case_id]
        current = _effective_case(original, revisions.get(case_id))
        versions = {str(case['version']): case for case in (original, current)}
        hashes = entry['caseHashes']
        require(isinstance(hashes, dict) and str(current['version']) in hashes, f'{case_id}: current version missing')
        feedback_fields = entry['fields']
        covered = set()
        for version, digest in hashes.items():
            case = versions.get(version)
            require(case is not None and hashlib.sha256(canonical(case)).hexdigest() == digest, f'{case_id}: source case changed')
            fields = _field_map(case)
            anchors = {fig['anchor'] for fig in case['bodyFigures']}
            require(fields.keys() <= feedback_fields.keys(), f'{case_id}: incomplete answer coverage for version {version}')
            covered.update(fields)
            for key, field in fields.items():
                try:
                    _validate_field(feedback_fields[key], field, anchors)
                except ValueError as error:
                    raise ValueError(f'{case_id}/{key}: {error}') from error
        require(covered == feedback_fields.keys(), f'{case_id}: feedback includes fields outside the reviewed versions')
        result[case_id] = {'versions': [int(version) for version in hashes], 'fields': feedback_fields}
    require(len(approvals) == len(evidence) and set(approvals) == set(result), 'Feedback review coverage differs')
    return result
