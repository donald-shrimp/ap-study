"""Reject stale or unreviewed legal additions before they reach published packs."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from legal_context_overrides import apply_legal_context
from material_contracts import validate_legal


class LegalOverrides(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'content/ap/qualification.json').read_text())
        self.raw = json.loads((ROOT / 'data/questions.json').read_text())
        self.entries = json.loads((ROOT / self.config['legalContextSource']).read_text())
        self.reviews = json.loads((ROOT / self.config['legalContextReviewSource']).read_text())

    def run_override(self, entries=None, reviews=None, raw=None):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp)
            (path / 'entries.json').write_text(json.dumps(self.entries if entries is None else entries))
            (path / 'reviews.json').write_text(json.dumps(self.reviews if reviews is None else reviews))
            config = dict(self.config, legalContextSource=str(path.relative_to(ROOT) / 'entries.json'),
                          legalContextReviewSource=str(path.relative_to(ROOT) / 'reviews.json'))
            bank = copy.deepcopy(self.raw if raw is None else raw)
            original = copy.deepcopy(bank)
            compiled = copy.deepcopy(bank)
            apply_legal_context(ROOT, config, bank, compiled)
            self.assertEqual(bank, original)
            return compiled

    def test_reviewed_overlay_preserves_original_answer_and_version(self):
        actual = {q['id']: q for q in self.run_override()}
        for q in self.raw:
            if q['id'] == 'r05h-q78':
                self.assertEqual(actual[q['id']]['legalReview']['status'], 'outdated')
                self.assertEqual(actual[q['id']]['answer'], q['answer'])
                self.assertEqual(actual[q['id']]['version'], q['version'])
            else:
                self.assertEqual(actual[q['id']], q)

    def test_reject_unreviewed_stale_duplicate_unknown_and_unauthorized_edits(self):
        mutations = []
        r = copy.deepcopy(self.reviews); r[0]['reviewer'] = r[0]['author']; mutations.append((self.entries, r))
        r = copy.deepcopy(self.reviews); r[0]['issues'] = ['not approved']; mutations.append((self.entries, r))
        e = copy.deepcopy(self.entries); e[0]['legalReview']['note'] += ' changed'; mutations.append((e, self.reviews))
        mutations.append((self.entries * 2, self.reviews))
        e = copy.deepcopy(self.entries); e[0]['id'] = 'unknown'; mutations.append((e, self.reviews))
        e = copy.deepcopy(self.entries); e[0]['answer'] = 0; mutations.append((e, self.reviews))
        r = copy.deepcopy(self.reviews); r[0]['sourceHashes'] = {}; mutations.append((self.entries, r))
        for entries, reviews in mutations:
            with self.subTest(entries=entries[0]['id']), self.assertRaises(ValueError):
                self.run_override(entries, reviews)
        raw = copy.deepcopy(self.raw)
        next(q for q in raw if q['id'] == 'r05h-q78')['version'] += 1
        with self.assertRaises(ValueError):
            self.run_override(raw=raw)

    def test_unknown_basis_date_allows_verified_change_but_not_current_claim(self):
        e = copy.deepcopy(self.entries[0])
        self.assertIsNone(e['sourceRecord']['legalAsOf'])
        validate_legal(e, True)
        e['legalReview']['status'] = 'current'
        with self.assertRaises(ValueError): validate_legal(e, True)
        e['legalReview']['status'] = 'outdated'; e['legalReview']['checkedAt'] = None
        with self.assertRaises(ValueError): validate_legal(e, True)


unittest.main()
