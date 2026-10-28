"""Bind independently checked legal metadata to exact original question versions.

The source bank and historical lesson approvals remain immutable. Only the
compiled material receives these explicitly reviewed additions.
"""
import hashlib
import json
from material_contracts import validate_legal, validate_source_hashes


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def apply_legal_context(root, config, raw, questions):
    paths = [config.get('legalContextSource'), config.get('legalContextReviewSource')]
    if paths == [None, None]:
        return
    def require(ok, message):
        if not ok:
            raise ValueError('Legal metadata: ' + message)
    require(all(isinstance(p, str) and p for p in paths), 'source and review must be paired')
    resolved = [(root / p).resolve() for p in paths]
    require(all(p.is_relative_to(root.resolve()) for p in resolved), 'source outside repository')
    entries, reviews = [json.loads(p.read_text()) for p in resolved]
    require(isinstance(entries, list) and isinstance(reviews, list), 'expected lists')
    require(all(isinstance(e, dict) and set(e) == {'id', 'sourceRecord', 'legalReview'} for e in entries), 'unexpected fields')
    ids = [e['id'] for e in entries]
    require(all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids), 'duplicate IDs')
    require(all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in reviews), 'invalid reviews')
    approvals = {r['id']: r for r in reviews}
    require(len(approvals) == len(reviews) and set(approvals) == set(ids), 'review coverage mismatch')
    originals = {q['id']: q for q in raw}
    compiled = {q['id']: q for q in questions}
    for entry in entries:
        id = entry['id']
        require(id in originals and id in compiled, 'unknown question ' + id)
        r = approvals[id]
        require(r.get('status') == 'approved' and r.get('issues') == [] and
                isinstance(r.get('author'), str) and r['author'].strip() and
                isinstance(r.get('reviewer'), str) and r['reviewer'].strip() and
                r['author'] != r['reviewer'], 'independent approval missing: ' + id)
        require(r.get('metadataSha256') == digest(entry) and
                r.get('questionSha256') == digest(originals[id]), 'stale approval: ' + id)
        validate_legal(entry, required=True)
        validate_source_hashes(root, entry, r)
        require(not any(k in compiled[id] for k in ('sourceRecord', 'legalReview')), 'existing metadata collision: ' + id)
        compiled[id].update({k: entry[k] for k in ('sourceRecord', 'legalReview')})
