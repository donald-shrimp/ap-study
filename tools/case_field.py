"""Publication checks for the field contract used by src/domain/case-field.js."""

import re
import unicodedata

from material_contracts import require, validate_numeric


def normalize_answer_text(value):
    # The whitespace set matches String.trim() for reference-answer comparison.
    whitespace = '\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff'
    return unicodedata.normalize('NFKC', value).strip(whitespace)


def safe_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', value)


def text(value, limit):
    return isinstance(value, str) and len(value) <= limit


def require_unique(values, message):
    require(len(set(values)) == len(values), message)


def validate_choices(field):
    choices = field.get('choices')
    method = field['grading']['method']
    single = field['type'] == 'singleChoice'
    require(isinstance(choices, list) and 2 <= len(choices) <= 20, 'Invalid number of choices')
    require(all(isinstance(choice, dict) and safe_id(choice.get('id'))
                and text(choice.get('label'), 50) and text(choice.get('text'), 20000 if single else 2000)
                for choice in choices), 'Invalid choice')
    ids = [choice['id'] for choice in choices]
    require_unique(ids, 'Duplicate choice ID')
    if method == 'exactChoiceSet':
        correct = field.get('correctChoiceIds')
        require('referenceAnswers' not in field and isinstance(correct, list)
                and 1 <= len(correct) <= (1 if single else len(ids))
                and all(id in ids for id in correct), 'Invalid correctChoiceIds')
        require_unique(correct, 'Duplicate correct choice ID')
        return
    labels = [choice['label'] for choice in choices]
    references = field['referenceAnswers']
    require(method == ('exactText' if single else 'unordered')
            and (len(references) == 1 if single else 2 <= len(references) <= len(labels))
            and all(answer in labels for answer in references), 'Invalid legacy choice labels')
    if not single:
        require(all(labels), 'Empty legacy choice label')
        require_unique(labels, 'Duplicate legacy choice label')
        require_unique(list(map(normalize_answer_text, references)), 'Duplicate legacy correct label')


def validate_answer_set(field):
    config = field.get('answerSet')
    require(isinstance(config, dict) and set(config) <= {'slots', 'sourceFieldIds', 'maxLength'},
            'Invalid answerSet configuration')
    answers = field['correctChoiceIds'] if field['grading']['method'] == 'exactChoiceSet' else field['referenceAnswers']
    slots = config.get('slots')
    if 'slots' in config:
        require(isinstance(slots, list) and 2 <= len(slots) == len(answers)
                and all(text(slot, 50) and normalize_answer_text(slot) for slot in slots), 'Invalid answer slots')
        require_unique(slots, 'Duplicate answer slot label')
    if 'sourceFieldIds' in config:
        ids = config['sourceFieldIds']
        require(isinstance(ids, list) and bool(ids) and ids[0] == field['id'] and all(map(safe_id, ids))
                and (len(ids) == 1 or slots and len(ids) == len(slots)), 'Invalid legacy field IDs')
        require_unique(ids, 'Duplicate legacy field ID')
    if 'choices' in field:
        require('maxLength' not in config, 'Choice inputs cannot set a text limit')
        return
    require(field['grading']['method'] == 'unordered', 'Invalid short-answer set grading method')
    limit = config.get('maxLength', 200)
    require('maxLength' not in config or slots and type(limit) is int and 1 <= limit <= 200, 'Invalid answer length')
    terms = list(map(normalize_answer_text, answers))
    require(all(terms) and all(text(answer, limit) for answer in answers), 'Invalid short-answer set reference')
    require_unique(terms, 'Duplicate short-answer set reference')


def validate_case_field(field):
    require(safe_id(field.get('id')) and text(field.get('label'), 100) and text(field.get('explanation'), 20000),
            'Invalid field ID, label or explanation')
    rubric = field.get('rubric')
    require(isinstance(rubric, list) and 1 <= len(rubric) <= 20 and all(text(point, 2000) for point in rubric),
            'Invalid rubric')
    grading = field.get('grading')
    require(isinstance(grading, dict) and set(grading) == {'method'}, 'Invalid grading configuration')
    kind, method = field.get('type'), grading['method']
    answers = field.get('referenceAnswers')
    if method != 'exactChoiceSet':
        require('correctChoiceIds' not in field and isinstance(answers, list) and 1 <= len(answers) <= 20
                and all(text(answer, 2000) for answer in answers), 'Invalid referenceAnswers')
    require(kind == 'answerSet' or 'answerSet' not in field, 'Unexpected answerSet')
    require(kind == 'numeric' or 'numeric' not in field, 'Unexpected numeric configuration')
    if kind == 'singleChoice' or 'choices' in field:
        require(kind in ('singleChoice', 'answerSet'), 'Unexpected choices')
        validate_choices(field)
    if kind == 'singleChoice':
        return
    if kind == 'answerSet':
        require(method != 'exactChoiceSet' or 'choices' in field, 'Missing choice options')
        validate_answer_set(field)
        return
    if kind == 'numeric':
        validate_numeric(field)
        return
    limit = field.get('maxLength')
    require(kind == 'shortText' and method in ('exactText', 'self') or kind == 'freeText' and method == 'self',
            'Unsupported input and grading combination')
    require(type(limit) is int and 1 <= limit <= 2000 and all(text(answer, limit) for answer in answers),
            'Invalid short-answer length')


def validate_case_fields(fields):
    ids = []
    for field in fields:
        validate_case_field(field)
        ids.extend(field.get('answerSet', {}).get('sourceFieldIds', [field['id']]) if field['type'] == 'answerSet'
                   else [field['id']])
    require_unique(ids, 'Conflicting field ID or legacy link')
