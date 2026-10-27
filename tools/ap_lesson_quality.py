"""Exact-hash gates for the AP objective lesson quality revision.

The existing AP material format stays unchanged. Author notes and independent
approval live in the workspace; registration is the sole publication boundary.
"""
from collections import Counter
from datetime import datetime
import copy
import hashlib
import json
from pathlib import Path
import re

WORK = Path('work/ap/objective-quality')
FIELDS = ('summary', 'explanation', 'choiceReasons', 'takeaway', 'hints')
LESSON_KEYS = {'id', *FIELDS, 'checkedAgainst'}
TEXT_KEYS = ('summary', 'explanation', 'takeaway')
DECISIONS = {'pending', 'keep', 'revise', 'rewrite'}
CHECKS = ('source', 'answer', 'choices', 'hints', 'explanation', 'revealFlags')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _list_by_id(rows, label):
    require(isinstance(rows, list) and all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in rows), label + ': records must have IDs')
    by_id = {r['id']: r for r in rows}
    require(len(by_id) == len(rows), label + ': duplicate IDs')
    return by_id


def _safe_file(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root) and path.is_file(), 'Missing/unsafe source: ' + str(relative))
    return path


def load_workspace(root):
    root = Path(root).resolve()
    work = root / WORK
    manifest = read(work / 'manifest.json')
    require(manifest.get('formatVersion') == 1 and re.fullmatch('[0-9a-f]{40}', manifest.get('baselineCommit', '')), 'Invalid quality manifest')
    hashes = manifest.get('baselineFiles')
    require(isinstance(hashes, dict) and hashes, 'Missing immutable baseline file hashes')
    actual_paths = {str(p.relative_to(work / 'baseline')) for p in (work / 'baseline').rglob('*') if p.is_file()}
    require(set(hashes) == actual_paths, 'Baseline file set mismatch')
    for path, expected in hashes.items():
        require(file_digest(_safe_file((work / 'baseline').resolve(), path)) == expected, 'Archived baseline changed: ' + path)
    for name in ['answer-keys.json', 'sources.json', 'source-crops.json']:
        require((root/'data'/name).read_bytes() == (work/'baseline'/name).read_bytes(), 'Original recovery/source metadata changed: ' + name)
    original = _list_by_id(read(work / 'baseline/questions.json'), 'Baseline bank')
    lessons = {}
    for path in sorted((work / 'baseline/lessons').glob('*.json')):
        rows = _list_by_id(read(path), 'Baseline lessons')
        require(not (set(lessons) & set(rows)), 'Duplicate baseline lesson')
        lessons.update(rows)
    inventory = _list_by_id(read(work / 'inventory.json'), 'Inventory')
    total = manifest.get('total')
    require(type(total) is int and total > 0 and len(original) == len(lessons) == len(inventory) == total and set(original) == set(lessons) == set(inventory), 'Inventory/baseline coverage mismatch')
    batch_ids = manifest.get('batchIds')
    require(isinstance(batch_ids, list) and batch_ids and len(set(batch_ids)) == len(batch_ids) and all(re.fullmatch(r'(?:pilot-00|batch-[0-9]{2})', b) for b in batch_ids), 'Invalid batch IDs')
    assignments = {}
    assigned = []
    for batch_id in batch_ids:
        a = read(work / 'batches' / batch_id / 'assignment.json')
        require(a.get('id') == batch_id and isinstance(a.get('questionIds'), list) and len(a['questionIds']) == 20 and len(set(a['questionIds'])) == 20, 'Batch must contain20 distinct questions: ' + batch_id)
        require(all(id in inventory and inventory[id].get('batchId') == batch_id for id in a['questionIds']), 'Batch assignment differs from inventory: ' + batch_id)
        require(a.get('author') is None or isinstance(a['author'], str) and a['author'].strip(), 'Invalid assigned author: ' + batch_id)
        assignments[batch_id] = a
        assigned += a['questionIds']
    require(len(assigned) == total and len(set(assigned)) == total and set(assigned) == set(original), 'Overlapping/incomplete assignments')
    source_cache = {}
    for id, entry in inventory.items():
        require(entry.get('baseVersion') == original[id].get('version') and entry.get('baselineQuestionSHA256') == digest(original[id]) and entry.get('baselineLessonSHA256') == digest(lessons[id]), 'Inventory baseline mismatch: ' + id)
        require(entry.get('lessonFile') == 'data/lessons/' + id.split('-q')[0] + '.json', 'Invalid lesson destination: ' + id)
        expected_sources = set(original[id]['sourceImages']) | {p for p in [original[id].get('image'), *[c.get('image') for c in original[id]['choices']]] if p} | {'data/answer-keys.json', 'data/sources.json'}
        require(isinstance(entry.get('sourceHashes'), dict) and set(entry['sourceHashes']) == expected_sources, 'Source coverage mismatch: ' + id)
        for path, expected in entry['sourceHashes'].items():
            if path not in source_cache:
                source_cache[path] = file_digest(_safe_file(root, path))
            require(source_cache[path] == expected, 'Original source changed: ' + path)
    registrations = read(work / 'registrations.json')
    require(isinstance(registrations, list) and len(set(registrations)) == len(registrations) and all(b in assignments for b in registrations), 'Invalid registered batches')
    return {'root': root, 'work': work, 'manifest': manifest, 'original': original, 'lessons': lessons, 'inventory': inventory, 'assignments': assignments, 'registrations': registrations}


def _lesson(lesson, id):
    require(isinstance(lesson, dict) and set(lesson) == LESSON_KEYS and lesson.get('id') == id, 'Lesson fields changed: ' + id)
    require(lesson.get('checkedAgainst') == 'official-question-image-and-answer-key', 'Missing original-source check: ' + id)
    require(all(isinstance(lesson[k], str) and lesson[k].strip() and len(lesson[k]) <= 20000 for k in TEXT_KEYS), 'Missing AP explanation fields: ' + id)
    require(isinstance(lesson['choiceReasons'], list) and len(lesson['choiceReasons']) == 4 and all(isinstance(r, str) and r.strip() for r in lesson['choiceReasons']), 'Four choice reasons required: ' + id)
    require(isinstance(lesson['hints'], list) and len(lesson['hints']) == 3, 'Three AP hints required: ' + id)
    for hint in lesson['hints']:
        require(isinstance(hint, dict) and set(hint) == {'title', 'text', 'revealsAnswer'} and isinstance(hint['title'], str) and hint['title'].strip() and len(hint['title']) <= 100 and isinstance(hint['text'], str) and hint['text'].strip() and len(hint['text']) <= 10000 and type(hint['revealsAnswer']) is bool, 'Invalid AP hint: ' + id)


def _check_batch(state, batch_id, require_reviews=False):
    require(batch_id in state['assignments'], 'Unknown batch: ' + batch_id)
    assignment = state['assignments'][batch_id]
    folder = state['work'] / 'batches' / batch_id
    drafts = _list_by_id(read(folder / 'drafts.json'), 'Drafts')
    ids = assignment['questionIds']
    require(set(drafts) == set(ids) and len(drafts) == 20, 'Draft assignment coverage mismatch: ' + batch_id)
    for id in ids:
        draft = drafts[id]
        require(set(draft) == {'id','baseVersion','baseLessonSHA256','author','decision','lesson','design'}, 'Unexpected draft fields: ' + id)
        entry = state['inventory'][id]
        require(draft.get('baseVersion') == entry['baseVersion'] and draft.get('baseLessonSHA256') == entry['baselineLessonSHA256'], 'Stale author baseline: ' + id)
        require(draft.get('decision') in DECISIONS, 'Invalid author decision: ' + id)
        _lesson(draft.get('lesson'), id)
        if draft['decision'] == 'pending':
            require(not require_reviews, 'Unfinished author draft: ' + id)
            continue
        require(isinstance(draft.get('author'), str) and draft['author'].strip() and draft['author'] == assignment.get('author'), 'Draft author differs from assignment: ' + id)
        if draft['decision'] == 'keep':
            require(draft['lesson'] == state['lessons'][id], 'Keep decision changes lesson: ' + id)
        else:
            require(draft['lesson'] != state['lessons'][id], 'Changed decision has no lesson change: ' + id)
        design = draft.get('design')
        require(isinstance(design, dict) and isinstance(design.get('obstacle'), str) and design['obstacle'].strip(), 'Missing learning obstacle: ' + id)
        require(isinstance(design.get('changes'), list) and isinstance(design.get('sourceNotes'), list), 'Invalid author notes: ' + id)
        stages = design.get('stages')
        require(isinstance(stages, list) and len(stages) == 3, 'Three stage-design notes required: ' + id)
        for stage, hint in zip(stages, draft['lesson']['hints']):
            require(isinstance(stage, dict) and all(isinstance(stage.get(k), str) and stage[k].strip() for k in ['newInformation', 'remainingWork', 'reason']) and stage.get('revealsAnswer') is hint['revealsAnswer'], 'Missing/inconsistent stage design: ' + id)
    review_rows = read(folder / 'reviews.json')
    reviews = _list_by_id(review_rows, 'Independent reviews')
    require(set(reviews) <= set(ids), 'Foreign review in batch: ' + batch_id)
    if require_reviews:
        require(set(reviews) == set(ids), 'Missing independent review: ' + batch_id)
    for id, review in reviews.items():
        draft = drafts[id]
        entry = state['inventory'][id]
        require(draft['decision'] != 'pending', 'Review of unfinished draft: ' + id)
        require(review.get('status') == 'approved', 'Review not approved: ' + id)
        require(review.get('author') == draft.get('author') and isinstance(review.get('reviewer'), str) and review['reviewer'].strip() and review['reviewer'] != review['author'], 'Independent reviewer required: ' + id)
        try:
            stamp = datetime.fromisoformat(review['checkedAt'].replace('Z', '+00:00'))
            require(stamp.tzinfo is not None and stamp.utcoffset() is not None, 'Timezone required in review date: ' + id)
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError('Invalid review date: ' + id) from error
        require(review.get('baseLessonSHA256') == entry['baselineLessonSHA256'] and review.get('reviewedLessonSHA256') == digest(draft['lesson']) and review.get('questionSHA256') == entry['baselineQuestionSHA256'], 'Stale review hash: ' + id)
        require(review.get('sourceHashes') == entry['sourceHashes'], 'Review source hashes differ: ' + id)
        for path, expected in entry['sourceHashes'].items():
            require(file_digest(_safe_file(state['root'], path)) == expected, 'Reviewed source changed: ' + path)
        checks = review.get('checks', {})
        require(isinstance(checks, dict) and all(checks.get(k) is True for k in CHECKS) and (checks.get('calculation') is True or checks.get('calculation') == 'not-applicable'), 'Incomplete independent checks: ' + id)
        original = state['original'][id]
        require(review.get('officialAnswer') == original['choices'][original['answer']]['label'], 'Official answer mismatch: ' + id)
        require(isinstance(review.get('notes'), str) and review['notes'].strip() and isinstance(review.get('independentResult'), (str, dict)) and bool(review['independentResult']) and review.get('issues') == [], 'Unresolved/incomplete content review: ' + id)
    return {'assignment': assignment, 'drafts': drafts, 'reviews': reviews}


def check_batch(root, batch_id, require_reviews=False):
    state = load_workspace(root)
    result = _check_batch(state, batch_id, require_reviews)
    return {'batchId': batch_id, 'questions': len(result['drafts']), 'reviewed': len(result['reviews']), 'approvedForRegistration': require_reviews}


def check_drafts(root):
    """Check every delegated handoff without certifying its content."""
    state = load_workspace(root)
    for batch_id in state['assignments']:
        _check_batch(state, batch_id)
    return {'batches': len(state['assignments']), 'questions': len(state['inventory']),
            'scope': 'draft structure and any submitted review hashes, not content approval'}


def expected_material(state, registrations=None):
    registrations = state['registrations'] if registrations is None else registrations
    lessons = copy.deepcopy(state['lessons'])
    bank = copy.deepcopy(list(state['original'].values()))
    by_id = {q['id']: q for q in bank}
    for batch_id in registrations:
        batch = _check_batch(state, batch_id, True)
        for id, draft in batch['drafts'].items():
            lesson = draft['lesson']
            lessons[id] = copy.deepcopy(lesson)
            q = by_id[id]
            for field in FIELDS:
                q[field] = copy.deepcopy(lesson[field])
            q['version'] = state['original'][id]['version'] + (lesson != state['lessons'][id])
            source = 'lessons/' + id.split('-q')[0] + '.json:' + id
            q.update(enrichment='reviewed', hintStatus='individual', hintSource=source, lessonSource=source)
    return lessons, bank


def validate_workspace(root, check_bank=True):
    state = load_workspace(root)
    lessons, bank = expected_material(state)
    actual_lessons = {}
    current_files = sorted((state['root'] / 'data/lessons').glob('*.json'))
    baseline_files = sorted((state['work'] / 'baseline/lessons').glob('*.json'))
    require({p.name for p in current_files} == {p.name for p in baseline_files}, 'Current lesson file set differs from baseline')
    for path in current_files:
        rows = _list_by_id(read(path), 'Current lessons')
        baseline_ids = {row['id'] for row in read(state['work'] / 'baseline/lessons' / path.name)}
        require(set(rows) == baseline_ids, 'Current lesson moved to another exam file: ' + path.name)
        require(not (set(actual_lessons) & set(rows)), 'Duplicate current lesson')
        actual_lessons.update(rows)
    require(digest(actual_lessons) == digest(lessons), 'Current lesson source differs from independently registered composition')
    for path in (state['work'] / 'baseline/lesson-reviews').glob('*.json'):
        require((state['root'] / 'data/lesson-reviews' / path.name).read_bytes() == path.read_bytes(), 'Historical review archive changed: ' + path.name)
    if check_bank:
        require(digest(read(state['root'] / 'data/questions.json')) == digest(bank), 'AP bank differs from registered lessons/versions or immutable original fields')
    return {'questions': len(bank), 'registeredBatches': len(state['registrations']), 'reviewedUnderCurrentRules': len(state['registrations']) * 20}


def legacy_classification_hashes(root):
    """Keep old context reviews valid only for proven lesson-only revisions.

    Classification concerns the original problem, not the revised teaching text.
    Validate the entire current composition before allowing any old question hash.
    """
    validate_workspace(root)
    state = load_workspace(root)
    return {id: digest(state['original'][id])
            for batch in state['registrations']
            for id in state['assignments'][batch]['questionIds']}


def progress(root):
    validate_workspace(root)
    state = load_workspace(root)
    rows = []
    for batch_id, assignment in state['assignments'].items():
        folder = state['work'] / 'batches' / batch_id
        drafts = _list_by_id(read(folder / 'drafts.json'), 'Progress drafts')
        review_rows = read(folder / 'reviews.json')
        try:
            _check_batch(state, batch_id)
            valid_reviews = True
        except ValueError:
            valid_reviews = False
        for id in assignment['questionIds']:
            draft = drafts[id]
            status = ('authoring' if draft.get('author') else 'unstarted') if draft.get('decision') == 'pending' else 'awaitingReview'
            if batch_id in state['registrations']:
                status = 'approved'
            else:
                matching = [r for r in review_rows if r.get('id') == id]
                if matching and any(r.get('status') != 'approved' or r.get('issues') for r in matching):
                    status = 'held'
                elif matching:
                    status = 'reviewed' if valid_reviews else 'awaitingReview'
            rows.append({'id': id, 'batchId': batch_id, 'topicId': state['inventory'][id]['topicId'], 'baseVersion': state['inventory'][id]['baseVersion'], 'author': assignment.get('author'), 'reviewer': next((r.get('reviewer') for r in review_rows if r.get('id') == id), None), 'status': status, 'decision': draft.get('decision')})
    counts = Counter(row['status'] for row in rows)
    return {'status': 'in_progress', 'counts': {s: counts[s] for s in ['unstarted', 'authoring', 'awaitingReview', 'reviewed', 'approved', 'held']}, 'registeredBatches': state['registrations'], 'questions': rows, 'note': 'Approved means independently reviewed and registered; publication is verified separately, not inferred from draft or review files.'}


def accept_batch(root, batch_id):
    state = load_workspace(root)
    validate_workspace(root)
    _check_batch(state, batch_id, True)
    registrations = list(state['registrations'])
    if batch_id not in registrations:
        registrations.append(batch_id)
    lessons, bank = expected_material(state, registrations)
    # All checks above precede the first write. The source bank is derived from
    # exact baseline + approved registrations, so repeated acceptance is stable.
    for path in sorted((state['root'] / 'data/lessons').glob('*.json')):
        old = read(path)
        new = [lessons[row['id']] for row in old]
        if old != new:
            write(path, new)
    if read(state['root'] / 'data/questions.json') != bank:
        write(state['root'] / 'data/questions.json', bank)
    write(state['work'] / 'registrations.json', registrations)
    validate_workspace(root)
    return {'batchId': batch_id, 'questions': 20, 'registered': True}


def claim_batch(root, batch_id, author, reviewer=None):
    """Record a coordinator's assignment without altering any material or review."""
    state = load_workspace(root)
    require(batch_id in state['assignments'], 'Unknown batch: ' + batch_id)
    require(isinstance(author, str) and author.strip(), 'Author name required')
    require(reviewer is None or isinstance(reviewer, str) and reviewer.strip() and reviewer != author, 'Independent reviewer required')
    assignment = state['assignments'][batch_id]
    require(assignment.get('author') in (None, author), 'Batch already assigned to another author: ' + batch_id)
    require(reviewer is None or assignment.get('reviewer') in (None, reviewer), 'Batch already assigned to another reviewer: ' + batch_id)
    assignment['author'] = author
    if reviewer is not None:
        assignment['reviewer'] = reviewer
    write(state['work']/'batches'/batch_id/'assignment.json', assignment)
    return {'batchId': batch_id, 'author': author, 'reviewer': assignment.get('reviewer'), 'materialChanged': False}
