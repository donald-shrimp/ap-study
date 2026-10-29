"""Append-only, content-bound candidate collection; never changes learning material."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
import os
import tempfile
from pathlib import Path
import subprocess
import uuid

WORK = Path('work/ap/hint-foundations')
AXES = ('foundation', 'prerequisites', 'progression')
IMMUTABLE = ('manifest.json', 'inventory.json', 'units.json', 'claims/', 'transfers/', 'records/', 'reviews/')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.pending-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        # Complete bytes become visible atomically; a simultaneous reservation
        # cannot replace an existing file. Remote publication is a separate lease.
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    require(isinstance(value, str), 'Missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'Timestamp needs timezone')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def safe_file(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), 'Missing/unsafe material path')
    return path


def current_bank(root):
    directory = root / 'data/qualifications/ap'
    manifest = read(directory / 'manifest.json')
    result = {}
    for pack in manifest['packs']:
        path = safe_file(root, str((directory / pack['url']).relative_to(root)))
        require(hashlib.sha256(path.read_bytes()).hexdigest() == pack['sha256'], 'Pack SHA mismatch')
        for q in read(path):
            require(q['id'] not in result, 'Duplicate question')
            result[q['id']] = (q, str(path.relative_to(root)))
    return result


def initialize(root, base_commit):
    work = root / WORK
    require(not (work / 'manifest.json').exists(), 'Audit already initialized')
    bank = current_bank(root)
    old = read(root / 'work/ap/objective-quality/manifest.json')
    units, inventory = [], []
    for number, previous in enumerate(old['batchIds'], 1):
        ids = read(root / f'work/ap/objective-quality/batches/{previous}/assignment.json')['questionIds']
        unit = f'unit-{number:02d}'
        units.append({'id': unit, 'previousPartition': previous, 'questionIds': ids})
        for id in ids:
            q, path = bank[id]
            inventory.append({'id': id, 'unitId': unit, 'version': q['version'], 'topicId': q['topicId'],
                              'topic': q['topic'], 'title': q['title'], 'materialSha256': digest(q), 'materialPath': path})
    require(len(inventory) == 800 and len({r['id'] for r in inventory}) == 800 and set(bank) == {r['id'] for r in inventory}, 'Expected exact AP800 partition')
    rubric = root / 'docs/hint-foundations-audit.md'
    manifest = {'formatVersion': 1, 'rubricVersion': 1, 'baseCommit': base_commit, 'qualificationId': 'ap',
                'examPartId': 'objective', 'count': 800, 'unitSize': 20,
                'rubricSha256': hashlib.sha256(rubric.read_bytes()).hexdigest(),
                'inventorySha256': digest(inventory), 'unitsSha256': digest(units)}
    for name, data in [('inventory.json', inventory), ('units.json', units), ('manifest.json', manifest)]:
        write_new(work / name, data)


def load(root):
    work = root / WORK
    manifest, inventory, units = [read(work / name) for name in ('manifest.json', 'inventory.json', 'units.json')]
    require(manifest['formatVersion'] == 1 and manifest['rubricVersion'] == 1, 'Unknown audit/rubric version')
    require(digest(inventory) == manifest['inventorySha256'] and digest(units) == manifest['unitsSha256'], 'Frozen partition changed')
    require(hashlib.sha256((root / 'docs/hint-foundations-audit.md').read_bytes()).hexdigest() == manifest['rubricSha256'], 'Frozen rubric changed; start a new round')
    ids = [r['id'] for r in inventory]
    require(len(ids) == len(set(ids)) == manifest['count'] == 800, 'Invalid inventory coverage')
    flat = [id for u in units for id in u['questionIds']]
    require(len(units) == 40 and all(len(u['questionIds']) == 20 for u in units) and len(flat) == len(set(flat)) and set(flat) == set(ids), 'Invalid work units')
    by_id = {r['id']: r for r in inventory}
    require(all(by_id[id]['unitId'] == u['id'] for u in units for id in u['questionIds']), 'Partition mismatch')
    material = {}
    cache = {}
    for row in inventory:
        path = row['materialPath']
        if path not in cache:
            cache[path] = {q['id']: q for q in read(safe_file(root, path))}
        q = cache[path].get(row['id'])
        require(q is not None and digest(q) == row['materialSha256'] and q['version'] == row['version'], 'Frozen material changed: ' + row['id'])
        material[row['id']] = q
    return manifest, by_id, {u['id']: u for u in units}, material


def evaluate(record, question):
    assessment = record.get('assessment')
    require(assessment in ('clear', 'candidate', 'uncertain'), 'Invalid assessment')
    scores = record.get('scores')
    require(isinstance(scores, dict) and set(scores) == set(AXES), 'Expected all three scores')
    critical = record.get('criticalOverride')
    require(type(critical) is bool, 'criticalOverride must be boolean')
    require(record.get('confidence') in ('high', 'medium', 'low'), 'Missing confidence')
    require(text(record.get('cumulativeReason')), 'Explain cumulative H1-H3 assessment')
    reasons = record.get('axisReasons')
    require(isinstance(reasons, dict) and set(reasons) == set(AXES) and all(text(v) for v in reasons.values()), 'Explain all three axis scores, including zero/uncertain')
    reviewed = record.get('reviewed')
    require(isinstance(reviewed, dict) and set(reviewed) == {'question', 'choices', 'allHints'} and all(type(v) is bool for v in reviewed.values()), 'Record actual context reading')
    require(assessment == 'uncertain' or all(reviewed.values()), 'Full context must actually be read')
    evidence = record.get('evidence')
    require(isinstance(evidence, list), 'Evidence must be a list')
    quotations = set()
    for e in evidence:
        require(set(e) == {'axis', 'hintStep', 'quote', 'missingKnowledge', 'learnerBlock', 'neededExplanation'}, 'Invalid evidence fields')
        require(e['axis'] in AXES and type(e['hintStep']) is int and 1 <= e['hintStep'] <= len(question['hints']), 'Invalid hint locator')
        require(all(text(e[k]) for k in ('quote', 'missingKnowledge', 'learnerBlock', 'neededExplanation')), 'Evidence needs quote, prerequisite, obstacle and repair direction')
        require(e['quote'] in question['hints'][e['hintStep'] - 1]['text'], 'Quote is not in the referenced hint')
        location = (e['hintStep'], e['quote'])
        require(location not in quotations, 'Do not double-score the same quotation')
        quotations.add(location)
    if assessment == 'uncertain':
        require(all(v is None for v in scores.values()) and not critical and text(record.get('missingContext')), 'Uncertain needs null scores and missing context')
        return None, 'unassessed'
    require(all(type(v) is int and 0 <= v <= 2 for v in scores.values()), 'Scores must be integers 0..2')
    total = sum(scores.values())
    require((assessment == 'clear' and total == 0 and not critical and not evidence) or (assessment == 'candidate' and total > 0), 'Assessment disagrees with scores')
    require(all(any(e['axis'] == axis for e in evidence) for axis in AXES if scores[axis]), 'Each positive score needs its own evidence')
    require(all(scores[e['axis']] > 0 for e in evidence), 'Evidence axis must be scored')
    if assessment == 'clear':
        support = record.get('support')
        require(isinstance(support, dict) and set(support) == {'hintStep', 'quote', 'enables'}, 'Clear assessment needs an actual teaching foothold')
        require(type(support['hintStep']) is int and 1 <= support['hintStep'] <= len(question['hints']) and text(support['quote']) and text(support['enables']), 'Invalid support evidence')
        require(support['quote'] in question['hints'][support['hintStep'] - 1]['text'], 'Support quote is not in the referenced hint')
    if critical:
        require(text(record.get('criticalReason')), 'Explain why all cumulative hints leave no learning foothold')
        require((scores['foundation'] == 2 or scores['prerequisites'] == 2) and
                {e['hintStep'] for e in evidence} == set(range(1, len(question['hints']) + 1)), 'Critical requires a blocking deficit and evidence across every hint')
    severity = 'critical' if critical else 'none' if total == 0 else 'low' if total <= 2 else 'medium' if total <= 4 else 'high'
    return total, severity


def inspect(root):
    manifest, inventory, units, material = load(root)
    work = root / WORK
    claims = {}
    for path in sorted((work / 'claims').glob('*.json')):
        c = read(path)
        require(c['unitId'] in units and path.name == c['unitId'] + '.json' and c['unitId'] not in claims and text(c['worker']), 'Invalid/duplicate claim')
        require(c['rubricVersion'] == manifest['rubricVersion'], 'Stale claim rubric')
        timestamp(c['createdAt'])
        claims[c['unitId']] = c
    history = {digest(c): c for c in claims.values()}
    successors = {}
    for path in sorted((work / 'transfers').glob('*.json')):
        t = read(path)
        require(t['unitId'] in units and path.name == t['transferId'] + '.json' and text(t['worker']) and text(t['coordinator']) and text(t['reason']), 'Invalid transfer')
        require(t['rubricVersion'] == manifest['rubricVersion'] and isinstance(t['preservedRecordShas'], list) and len(set(t['preservedRecordShas'])) == len(t['preservedRecordShas']), 'Invalid transfer snapshot')
        timestamp(t['createdAt'])
        parent = t['fromClaimSha256']
        require(parent not in successors, 'Forked ownership transfer')
        successors[parent] = t
        history[digest(t)] = t
    visited = set()
    for unit, c in claims.items():
        seen = set()
        while digest(c) in successors:
            parent = digest(c)
            require(parent not in seen, 'Cyclic transfer')
            seen.add(parent)
            t = successors[parent]
            require(t['unitId'] == unit and t['worker'] != c['worker'], 'Foreign/redundant ownership transfer')
            require(set(c.get('preservedRecordShas', [])) <= set(t['preservedRecordShas']), 'Transfer dropped inherited records')
            visited.add(digest(t))
            c = t
        claims[unit] = c
    require(visited == {digest(t) for t in successors.values()}, 'Disconnected transfer')
    records, latest = {}, {}
    for path in sorted((work / 'records').glob('*/*.json')):
        r = read(path)
        id, unit = r['questionId'], r['unitId']
        require(id in inventory and inventory[id]['unitId'] == unit, 'Foreign question/unit')
        c = history.get(r['claimSha256'])
        require(c is not None and c['unitId'] == unit and c['worker'] == r['worker'], 'Missing or foreign ownership')
        require(path.parent.name == unit and path.name == r['recordId'] + '.json', 'Invalid record path')
        require(r['materialSha256'] == inventory[id]['materialSha256'] and r['questionVersion'] == inventory[id]['version'] and r['rubricVersion'] == manifest['rubricVersion'], 'Stale question/rubric reference')
        require((r['total'], r['severity']) == evaluate(r, material[id]), 'Derived score/severity mismatch')
        timestamp(r['createdAt'])
        sha = digest(r)
        require(sha not in records, 'Duplicate record')
        records[sha] = r
    for sha, r in records.items():
        transition = successors.get(r['claimSha256'])
        require(transition is None or sha in transition['preservedRecordShas'], 'Late submission from transferred owner')
    for t in successors.values():
        require(all(sha in records and records[sha]['unitId'] == t['unitId'] for sha in t['preservedRecordShas']), 'Transfer references missing/foreign records')
    # A correction appends a successor. Forked revisions require adjudication;
    # no timestamp or filename silently wins over a different contribution.
    children = Counter()
    for sha, r in records.items():
        parent = r.get('supersedes')
        if parent is not None:
            require(parent in records and records[parent]['questionId'] == r['questionId'] and parent != sha, 'Missing/foreign predecessor')
            children[parent] += 1
            require(children[parent] == 1, 'Forked result revisions')
    for id in inventory:
        group = {sha: r for sha, r in records.items() if r['questionId'] == id}
        if not group:
            continue
        roots = [sha for sha, r in group.items() if r.get('supersedes') is None]
        leaves = [sha for sha in group if not children[sha]]
        require(len(roots) == len(leaves) == 1, 'Result chain must have exactly one root/leaf')
        cursor, seen = leaves[0], set()
        while cursor is not None:
            require(cursor not in seen, 'Cyclic result revisions')
            seen.add(cursor)
            cursor = group[cursor].get('supersedes')
        require(seen == set(group), 'Disconnected result history')
        latest[id] = (leaves[0], group[leaves[0]])
    reviews = {}
    for path in sorted((work / 'reviews').glob('*.json')):
        r = read(path)
        target = records.get(r['recordSha256'])
        require(target is not None and r['questionId'] == target['questionId'], 'Unknown/stale review target')
        require(text(r['worker']) and r['worker'] != target['worker'] and text(r['reason']), 'Reviewer must differ and explain actual confirmation')
        require(r['decision'] in ('confirmed', 'dismissed', 'needs_more_context') and path.name == r['reviewId'] + '.json', 'Invalid review')
        timestamp(r['createdAt'])
        reviews.setdefault(r['recordSha256'], []).append(r)
    current = current_bank(root)
    require(set(current) == set(inventory), 'Scope changed; initialize a new audit round')
    return manifest, inventory, units, material, claims, latest, reviews, current


def claim(root, unit, worker):
    _, _, units, _, _, _, _, _ = inspect(root)
    require(unit in units and text(worker), 'Unknown unit or worker')
    write_new(root / WORK / 'claims' / (unit + '.json'), {'unitId': unit, 'worker': worker, 'rubricVersion': 1, 'createdAt': now()})


def active_claim_path(claim):
    if 'transferId' in claim:
        return WORK / 'transfers' / (claim['transferId'] + '.json')
    return WORK / 'claims' / (claim['unitId'] + '.json')


def transfer(root, unit, worker, coordinator, reason):
    _, _, _, _, claims, _, _, _ = inspect(root)
    c = claims.get(unit)
    require(c is not None and text(worker) and worker != c['worker'] and text(coordinator) and text(reason), 'Transfer needs an existing owner, new owner and coordinator reason')
    preserved = [digest(read(p)) for p in (root / WORK / 'records' / unit).glob('*.json')]
    t = {'transferId': uuid.uuid4().hex, 'unitId': unit, 'fromClaimSha256': digest(c), 'worker': worker,
         'coordinator': coordinator, 'reason': reason, 'rubricVersion': 1, 'createdAt': now(), 'preservedRecordShas': sorted(preserved)}
    write_new(root / WORK / 'transfers' / (t['transferId'] + '.json'), t)


def submit(root, id, worker, proposal):
    manifest, inventory, _, material, claims, latest, _, current = inspect(root)
    require(id in inventory, 'Unknown question')
    row = inventory[id]
    c = claims.get(row['unitId'])
    require(c is not None and c['worker'] == worker, 'Claim must be published and owned before work')
    require(digest(current[id][0]) == row['materialSha256'], 'Current material changed; do not score stale material')
    allowed = {'assessment', 'scores', 'criticalOverride', 'confidence', 'cumulativeReason', 'reviewed', 'evidence', 'missingContext', 'supersedes', 'axisReasons', 'criticalReason', 'support'}
    require(set(proposal) <= allowed, 'Unexpected submission fields')
    previous = latest.get(id, (None, None))[0]
    require(proposal.get('supersedes') == previous, 'Stale result head: supply exact supersedes SHA')
    total, severity = evaluate(proposal, material[id])
    r = {**proposal, 'supersedes': previous, 'recordId': uuid.uuid4().hex, 'questionId': id, 'unitId': row['unitId'],
         'worker': worker, 'claimSha256': digest(c), 'materialSha256': row['materialSha256'], 'questionVersion': row['version'],
         'rubricVersion': manifest['rubricVersion'], 'createdAt': now(), 'total': total, 'severity': severity}
    write_new(root / WORK / 'records' / row['unitId'] / (r['recordId'] + '.json'), r)
    return digest(r)


def review(root, sha, worker, decision, reason):
    inspect(root)
    records = [read(p) for p in (root / WORK / 'records').glob('*/*.json')]
    target = next((r for r in records if digest(r) == sha), None)
    require(target is not None and text(worker) and worker != target['worker'] and text(reason), 'Actual different reviewer and reason required')
    require(decision in ('confirmed', 'dismissed', 'needs_more_context'), 'Invalid review decision')
    r = {'reviewId': uuid.uuid4().hex, 'recordSha256': sha, 'questionId': target['questionId'], 'worker': worker,
         'decision': decision, 'reason': reason, 'createdAt': now()}
    write_new(root / WORK / 'reviews' / (r['reviewId'] + '.json'), r)


def check_history(root, base):
    # Existing published data is immutable; new files can be appended normally.
    paths = [str(WORK / p) for p in IMMUTABLE]
    diff = subprocess.check_output(['git', 'diff', '--name-status', '--no-renames', base, '--', *paths], cwd=root, text=True)
    require(all(line.startswith('A\t') for line in diff.splitlines()), 'Published audit records cannot be edited/deleted')
    log = subprocess.check_output(['git', 'log', '--format=', '--name-status', '--no-renames', '--diff-filter=MD', base + '..HEAD', '--', *paths], cwd=root, text=True)
    require(not log.strip(), 'Audit history rewrote/deleted an existing immutable file')


def require_published(root, ref, relative):
    """A fetched Git ref must already contain the exact reservation/input."""
    body = subprocess.check_output(['git', 'show', ref + ':' + str(relative)], cwd=root, text=True)
    require(digest(json.loads(body)) == digest(read(root / relative)), 'Published reservation/record differs')


def report(root):
    _, inventory, units, _, claims, latest, reviews, current = inspect(root)
    counts = Counter({'unreviewed': 0, 'clear': 0, 'candidate': 0, 'uncertain': 0, 'stale': 0})
    rows = []
    for id, item in inventory.items():
        record = latest.get(id)
        stale = digest(current[id][0]) != item['materialSha256']
        state = 'stale' if stale else record[1]['assessment'] if record else 'unreviewed'
        counts[state] += 1
        if record:
            sha, r = record
            decisions = {v['decision'] for v in reviews.get(sha, [])}
            confirmation = 'disputed' if len(decisions) > 1 else next(iter(decisions)) if decisions else 'unconfirmed'
            rows.append({'questionId': id, 'unitId': item['unitId'], 'topic': item['topic'], 'title': item['title'],
                         'state': state, 'total': r['total'], 'severity': r['severity'], 'confidence': r['confidence'],
                         'confirmation': confirmation, 'recordSha256': sha, 'worker': r['worker'],
                         'recordPath': str(WORK / 'records' / r['unitId'] / (r['recordId'] + '.json')),
                         'axisReasons': r['axisReasons'],
                         'evidence': r['evidence'], 'support': r.get('support'),
                         'missingContext': r.get('missingContext'), 'cumulativeReason': r['cumulativeReason']})
    order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'none': 4, 'unassessed': 5}
    rows.sort(key=lambda r: (r['state'] != 'candidate', order[r['severity']], -(r['total'] or 0), r['questionId']))
    progress = [{'unitId': u['id'], 'worker': claims.get(u['id'], {}).get('worker'),
                 'submitted': sum(id in latest for id in u['questionIds']),
                 'complete': all(id in latest and latest[id][1]['assessment'] != 'uncertain' and digest(current[id][0]) == inventory[id]['materialSha256'] for id in u['questionIds'])} for u in units.values()]
    inputs = {}
    for relative in IMMUTABLE:
        path = root / WORK / relative
        files = path.rglob('*.json') if relative.endswith('/') else [path]
        inputs.update({str(p.relative_to(root)): digest(read(p)) for p in files if p.is_file()})
    return {'counts': dict(counts), 'claimedUnits': len(claims), 'completeUnits': sum(u['complete'] for u in progress),
            'baseCommit': load(root)[0]['baseCommit'], 'inputDigest': digest(inputs),
            'note': 'Candidates and mechanical checks are not confirmed defects or learner-tested effects.', 'units': progress, 'results': rows}


def markdown(data):
    labels = {'none': '不足なし', 'low': '軽度', 'medium': '中度', 'high': '高度', 'critical': '最優先', 'unassessed': '未確定'}
    states = {'candidate': '候補', 'clear': '足場あり', 'uncertain': '保留', 'stale': '再確認'}
    confirmations = {'unconfirmed': '未確認', 'confirmed': '確認済み', 'dismissed': '見送り', 'needs_more_context': '要追加確認', 'disputed': '意見が分かれている'}
    def cell(value):
        return html.escape(str(value), quote=False).replace('|', '&#124;').replace('\n', ' ')
    c = data['counts']
    lines = ['# 科目A・初学者向けヒントの点検状況', '',
             f"未点検 {c['unreviewed']} / 候補 {c['candidate']} / 足場あり {c['clear']} / 判断保留 {c['uncertain']} / 教材変更後の再確認待ち {c['stale']}", '',
             '候補は編集上の指摘であり、別担当による確認や改稿の承認とは分ける。完了組は20問の一次点検提出を意味する。', '',
             f"固定対象main: `{data['baseCommit']}` · 入力digest: `{data['inputDigest']}`", '',
             'この表は集計時点のスナップショット。個別JSONが正本。最新集計は同じPRの「Hint foundation audit」CI成果物にある。', '',
             '| 問題 | 分野 | 状態 | 得点 | 重大度 | 主な根拠・必要な説明 | 別担当確認 |', '| --- | --- | --- | --- | --- | --- | --- |']
    for r in data['results']:
        topic = cell(r['topic'])
        # REPORT.md lives in WORK; CI artifact keeps a full GitHub branch URL.
        url = 'https://github.com/donald-shrimp/ap-study/blob/audit/ap-a-hint-foundations/' + r['recordPath']
        if r['state'] == 'stale':
            reason = '教材の更新後に再確認が必要'
        elif r['state'] == 'uncertain':
            reason = cell(r['missingContext'])
        elif r['state'] == 'candidate':
            e = r['evidence'][0]
            reason = f"H{e['hintStep']}「{cell(e['quote'])}」：{cell(e['learnerBlock'])}<br>必要：{cell(e['neededExplanation'])}"
        else:
            s = r['support']
            reason = f"H{s['hintStep']}「{cell(s['quote'])}」：{cell(s['enables'])}"
        lines.append(f"| [{cell(r['title'])}]({url}) | {topic} | {states[r['state']]} | {r['total'] if r['total'] is not None else '—'} | {labels[r['severity']]} | {reason} | {confirmations[r['confirmation']]} |")
    if not data['results']:
        lines.append('| まだ実点検なし | — | 未点検 | — | — | — | — |')
    lines += ['', '| 組 | 担当 | 提出数 | 一次点検提出済み |', '| --- | --- | --- | --- |']
    for u in data['units']:
        worker = (u['worker'] or '未予約').replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {u['unitId']} | {worker} | {u['submitted']}/20 | {'はい' if u['complete'] else 'いいえ'} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('--base', required=True)
    p = sub.add_parser('claim'); p.add_argument('unit'); p.add_argument('--worker', required=True)
    p = sub.add_parser('transfer'); p.add_argument('unit'); p.add_argument('--worker', required=True); p.add_argument('--coordinator', required=True); p.add_argument('--reason', required=True); p.add_argument('--published-ref', default='origin/audit/ap-a-hint-foundations')
    p = sub.add_parser('show'); p.add_argument('unit')
    p = sub.add_parser('submit'); p.add_argument('question'); p.add_argument('--worker', required=True); p.add_argument('--file', type=Path, required=True); p.add_argument('--published-ref', default='origin/audit/ap-a-hint-foundations')
    p = sub.add_parser('review'); p.add_argument('sha'); p.add_argument('--worker', required=True); p.add_argument('--decision', required=True); p.add_argument('--reason', required=True); p.add_argument('--published-ref', default='origin/audit/ap-a-hint-foundations')
    p = sub.add_parser('check'); p.add_argument('--against')
    p = sub.add_parser('report'); p.add_argument('--output', type=Path); p.add_argument('--markdown', action='store_true')
    args = parser.parse_args(); root = args.root.resolve()
    if args.command == 'init': initialize(root, args.base)
    elif args.command == 'claim': claim(root, args.unit, args.worker)
    elif args.command == 'transfer':
        claims = inspect(root)[4]
        require(args.unit in claims, 'Unknown unit owner')
        require_published(root, args.published_ref, active_claim_path(claims[args.unit]))
        for path in (root / WORK / 'records' / args.unit).glob('*.json'):
            require_published(root, args.published_ref, path.relative_to(root))
        transfer(root, args.unit, args.worker, args.coordinator, args.reason)
    elif args.command == 'submit':
        _, inventory, _, _ = load(root)
        require(args.question in inventory, 'Unknown question')
        claims = inspect(root)[4]
        require(inventory[args.question]['unitId'] in claims, 'Missing unit reservation')
        require_published(root, args.published_ref, active_claim_path(claims[inventory[args.question]['unitId']]))
        print(submit(root, args.question, args.worker, read(args.file)))
    elif args.command == 'review':
        paths = [p for p in (root / WORK / 'records').glob('*/*.json') if digest(read(p)) == args.sha]
        require(len(paths) == 1, 'Unknown review target')
        require_published(root, args.published_ref, paths[0].relative_to(root))
        review(root, args.sha, args.worker, args.decision, args.reason)
    elif args.command == 'show':
        _, _, units, material = load(root)
        require(args.unit in units, 'Unknown unit')
        print(json.dumps([material[id] for id in units[args.unit]['questionIds']], ensure_ascii=False, indent=2))
    elif args.command == 'check':
        inspect(root)
        if args.against: check_history(root, args.against)
        print('Audit contracts passed (content confirmations are separate)')
    elif args.command == 'report':
        value = report(root)
        data = markdown(value) if args.markdown else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.output: args.output.write_text(data)
        else: print(data, end='')


if __name__ == '__main__':
    main()
