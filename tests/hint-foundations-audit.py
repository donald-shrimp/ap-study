"""Synthetic contract tests, never an audit or approval of real AP content.

All questions, evidence, identities and Git remotes below live in temporary
directories. The repository's 800 questions and audit state are never written.
"""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import hint_foundations_audit as audit


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + '\n')


def git(root, *arguments, check=True):
    return subprocess.run(['git', *arguments], cwd=root, text=True,
                          capture_output=True, check=check)


def init_git(root):
    git(root, 'init', '-b', 'audit')
    git(root, 'config', 'user.name', 'Synthetic test')
    git(root, 'config', 'user.email', 'synthetic@example.invalid')
    git(root, 'add', '.')
    git(root, 'commit', '-m', 'Synthetic foundation')
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


def commit(root, message):
    git(root, 'add', '.')
    git(root, 'commit', '-m', message)
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


def clear_proposal():
    return {
        'assessment': 'clear', 'scores': dict.fromkeys(audit.AXES, 0),
        'criticalOverride': False, 'confidence': 'high',
        'axisReasons': {
            'foundation': 'The synthetic example explains the represented relationship.',
            'prerequisites': 'The synthetic operation and variable correspondence are provided.',
            'progression': 'The synthetic hints introduce the operation before application.',
        },
        'cumulativeReason': 'Synthetic H1 identifies quantities, H2 supplies the operation, and H3 lets the reader apply it.',
        'reviewed': {'question': True, 'choices': True, 'allHints': True},
        'evidence': [],
        'support': {'hintStep': 2, 'quote': 'Synthetic step 2',
                    'enables': 'The synthetic relationship makes the next operation identifiable.'},
    }


def evidence(axis='foundation', step=1):
    return {
        'axis': axis, 'hintStep': step, 'quote': f'Synthetic step {step}',
        'missingKnowledge': 'The synthetic relationship is not explained.',
        'learnerBlock': 'The reader cannot determine the first operation.',
        'neededExplanation': 'Explain the synthetic relationship with an example.',
    }


def candidate():
    result = clear_proposal()
    result.update(assessment='candidate', scores={'foundation': 1, 'prerequisites': 0, 'progression': 0},
                  evidence=[evidence()])
    return result


class AuditContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_temp = tempfile.TemporaryDirectory(prefix='hint-audit-synthetic-template-')
        cls.template = Path(cls.template_temp.name)
        old = cls.template / 'work/ap/objective-quality'
        batches = ['pilot-00'] + [f'batch-{i:02d}' for i in range(1, 40)]
        save(old / 'manifest.json', {'batchIds': batches})
        questions = []
        for i, batch in enumerate(batches):
            ids = [f'synthetic-q{j:03d}' for j in range(i * 20 + 1, i * 20 + 21)]
            save(old / 'batches' / batch / 'assignment.json', {'questionIds': ids})
            for id in ids:
                questions.append({'id': id, 'version': 1, 'topicId': 'synthetic',
                                  'topic': 'Synthetic contract fixture', 'title': id,
                                  'stem': 'Synthetic question only.',
                                  'choices': [{'text': 'Synthetic choice'}],
                                  'hints': [{'text': f'Synthetic step {step}: isolated fixture evidence.',
                                             'title': f'H{step}', 'revealsAnswer': False}
                                            for step in range(1, 4)]})
        pack = cls.template / 'data/qualifications/ap/packs/synthetic.json'
        save(pack, questions)
        save(pack.parent.parent / 'manifest.json', {'packs': [
            {'url': 'packs/synthetic.json', 'sha256': hashlib.sha256(pack.read_bytes()).hexdigest()}]})
        rubric = cls.template / 'docs/hint-foundations-audit.md'
        rubric.parent.mkdir(parents=True)
        rubric.write_text('Synthetic rubric fixture only.\n')
        audit.initialize(cls.template, '0' * 40)

    @classmethod
    def tearDownClass(cls):
        cls.template_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='hint-audit-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'fixture'
        shutil.copytree(self.template, self.root)
        self.work = self.root / audit.WORK
        self.id = 'synthetic-q001'
        self.unit = 'unit-01'
        self.worker = 'synthetic-author'

    def claim(self):
        audit.claim(self.root, self.unit, self.worker)

    def submit(self, proposal=None):
        return audit.submit(self.root, self.id, self.worker,
                            clear_proposal() if proposal is None else proposal)

    def record_path(self, sha):
        return next(p for p in (self.work / 'records').glob('*/*.json') if audit.digest(audit.read(p)) == sha)

    def test_initial_state_has_no_real_or_synthetic_findings(self):
        report = audit.report(self.root)
        self.assertEqual(report['counts']['unreviewed'], 800)
        self.assertEqual(report['results'], [])
        self.assertEqual(report['claimedUnits'], 0)
        self.assertEqual(report['completeUnits'], 0)

    def test_exclusive_create_has_one_winner_under_simultaneous_claim_writes(self):
        path = self.work / 'claims' / (self.unit + '.json')
        path.parent.mkdir(parents=True)
        barrier = threading.Barrier(8)

        def reserve(number):
            barrier.wait(timeout=10)
            try:
                audit.write_new(path, {'worker': f'synthetic-{number}'})
                return number
            except FileExistsError:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            winners = [v for v in pool.map(reserve, range(8)) if v is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(audit.read(path)['worker'], f'synthetic-{winners[0]}')

    def test_unclaimed_and_foreign_worker_cannot_submit(self):
        with self.assertRaisesRegex(ValueError, 'Claim'):
            self.submit()
        self.claim()
        with self.assertRaisesRegex(ValueError, 'Claim'):
            audit.submit(self.root, self.id, 'synthetic-outsider', clear_proposal())
        self.assertFalse((self.work / 'records').exists())

    def test_foreign_unit_question_and_record_path_are_rejected(self):
        self.claim()
        sha = self.submit()
        path = self.record_path(sha)
        original = audit.read(path)
        bad = copy.deepcopy(original)
        bad['questionId'] = 'synthetic-q021'
        save(path, bad)
        with self.assertRaisesRegex(ValueError, 'Foreign question/unit'):
            audit.inspect(self.root)
        save(path, original)
        path.rename(path.with_name('wrong-record-id.json'))
        with self.assertRaisesRegex(ValueError, 'record path'):
            audit.inspect(self.root)

    def test_partial_unit_requires_all_distinct_assessed_questions_for_complete(self):
        self.claim()
        self.submit()
        report = audit.report(self.root)
        self.assertEqual(report['units'][0]['submitted'], 1)
        self.assertFalse(report['units'][0]['complete'])
        self.assertEqual(report['counts']['clear'], 1)
        self.assertEqual(report['counts']['unreviewed'], 799)
        for i in range(2, 21):
            audit.submit(self.root, f'synthetic-q{i:03d}', self.worker, clear_proposal())
        report = audit.report(self.root)
        self.assertEqual(report['units'][0]['submitted'], 20)
        self.assertTrue(report['units'][0]['complete'])
        self.assertEqual(report['completeUnits'], 1)

    def test_quote_must_match_exact_referenced_hint_and_each_positive_axis(self):
        question = audit.load(self.root)[3][self.id]
        proposal = candidate()
        self.assertEqual(audit.evaluate(proposal, question), (1, 'low'))
        for quote in ('Not in any synthetic hint', 'synthetic step 1'):
            bad = copy.deepcopy(proposal)
            bad['evidence'][0]['quote'] = quote
            with self.assertRaisesRegex(ValueError, 'Quote'):
                audit.evaluate(bad, question)
        bad = copy.deepcopy(proposal)
        bad['evidence'][0]['hintStep'] = 2
        with self.assertRaisesRegex(ValueError, 'Quote'):
            audit.evaluate(bad, question)
        bad = copy.deepcopy(proposal)
        bad['scores']['prerequisites'] = 1
        with self.assertRaisesRegex(ValueError, 'positive score'):
            audit.evaluate(bad, question)
        bad = copy.deepcopy(proposal)
        bad['scores']['foundation'] = 0
        bad['scores']['prerequisites'] = 1
        bad['evidence'].append(evidence('prerequisites', 2))
        with self.assertRaisesRegex(ValueError, 'axis must be scored'):
            audit.evaluate(bad, question)

    def test_scores_reject_booleans_and_values_outside_rubric(self):
        question = audit.load(self.root)[3][self.id]
        for value in (True, False, -1, 3, 1.0, '1'):
            with self.subTest(value=value):
                proposal = candidate()
                proposal['scores']['foundation'] = value
                with self.assertRaises(ValueError):
                    audit.evaluate(proposal, question)

    def test_zero_score_axes_still_need_reasons_and_clear_requires_full_context(self):
        question = audit.load(self.root)[3][self.id]
        for axis in audit.AXES:
            proposal = clear_proposal()
            proposal['axisReasons'][axis] = ' '
            with self.assertRaisesRegex(ValueError, 'all three axis'):
                audit.evaluate(proposal, question)
        for assessment in ('clear', 'candidate'):
            proposal = clear_proposal() if assessment == 'clear' else candidate()
            proposal['reviewed']['allHints'] = False
            with self.assertRaisesRegex(ValueError, 'Full context'):
                audit.evaluate(proposal, question)

    def test_clear_requires_located_exact_support_quote_and_enabled_judgment(self):
        question = audit.load(self.root)[3][self.id]
        valid = clear_proposal()
        self.assertEqual(audit.evaluate(valid, question), (0, 'none'))
        malformed = []
        missing = copy.deepcopy(valid)
        del missing['support']
        malformed.append(missing)
        for change in ({'quote': 'Invented support quotation'}, {'hintStep': 1},
                       {'hintStep': True}, {'enables': ' '}):
            proposal = copy.deepcopy(valid)
            proposal['support'].update(change)
            malformed.append(proposal)
        for proposal in malformed:
            with self.subTest(support=proposal.get('support')):
                with self.assertRaises(ValueError):
                    audit.evaluate(proposal, question)

    def test_critical_requires_blocking_axis_and_evidence_for_every_step(self):
        question = audit.load(self.root)[3][self.id]
        proposal = candidate()
        proposal.update(criticalOverride=True, scores={'foundation': 2, 'prerequisites': 0, 'progression': 0},
                        criticalReason='After all synthetic hints the relationship and the first operation remain unavailable.')
        with self.assertRaisesRegex(ValueError, 'Critical'):
            audit.evaluate(proposal, question)
        proposal['evidence'] = [evidence('foundation', step) for step in range(1, 4)]
        self.assertEqual(audit.evaluate(proposal, question), (2, 'critical'))
        without_reason = copy.deepcopy(proposal)
        del without_reason['criticalReason']
        with self.assertRaisesRegex(ValueError, 'no learning foothold'):
            audit.evaluate(without_reason, question)
        proposal['scores']['foundation'] = 1
        with self.assertRaisesRegex(ValueError, 'Critical'):
            audit.evaluate(proposal, question)

    def test_uncertain_preserves_null_and_does_not_complete_unit(self):
        self.claim()
        proposal = clear_proposal()
        proposal.update(assessment='uncertain', scores=dict.fromkeys(audit.AXES),
                        missingContext='Synthetic diagram is unavailable.', confidence='low')
        proposal['reviewed']['choices'] = False
        self.submit(proposal)
        report = audit.report(self.root)
        row = report['results'][0]
        self.assertEqual(report['counts']['uncertain'], 1)
        self.assertIsNone(row['total'])
        self.assertEqual(row['severity'], 'unassessed')
        self.assertFalse(report['units'][0]['complete'])
        for i in range(2, 21):
            audit.submit(self.root, f'synthetic-q{i:03d}', self.worker, clear_proposal())
        report = audit.report(self.root)
        self.assertEqual(report['units'][0]['submitted'], 20)
        self.assertFalse(report['units'][0]['complete'], 'Twenty records with one uncertain question are not a completed assessment.')
        proposal['scores']['foundation'] = 0
        with self.assertRaisesRegex(ValueError, 'null scores'):
            audit.evaluate(proposal, audit.load(self.root)[3][self.id])

    def test_supersedes_appends_without_erasing_previous_and_stale_head_fails(self):
        self.claim()
        first = self.submit()
        proposal = candidate()
        proposal['supersedes'] = first
        second = self.submit(proposal)
        self.assertTrue(self.record_path(first).is_file())
        self.assertTrue(self.record_path(second).is_file())
        self.assertEqual(audit.inspect(self.root)[5][self.id][0], second)
        with self.assertRaisesRegex(ValueError, 'Stale result head'):
            self.submit(proposal)

    def test_forked_successors_are_detected_instead_of_timestamp_winning(self):
        self.claim()
        first = self.submit()
        proposal = candidate()
        proposal['supersedes'] = first
        second = self.submit(proposal)
        fork = audit.read(self.record_path(second))
        fork['recordId'] = 'synthetic-fork'
        fork['cumulativeReason'] += ' Competing contribution.'
        save(self.work / 'records' / self.unit / 'synthetic-fork.json', fork)
        with self.assertRaisesRegex(ValueError, 'Forked'):
            audit.inspect(self.root)

    def test_review_requires_different_identity_and_exact_result_hash(self):
        self.claim()
        sha = self.submit(candidate())
        with self.assertRaisesRegex(ValueError, 'different reviewer'):
            audit.review(self.root, sha, self.worker, 'confirmed', 'Synthetic review only.')
        with self.assertRaises(ValueError):
            audit.review(self.root, 'f' * 64, 'synthetic-reviewer', 'confirmed', 'Synthetic review only.')
        audit.review(self.root, sha, 'synthetic-reviewer', 'confirmed', 'Synthetic review only.')
        self.assertEqual(audit.report(self.root)['results'][0]['confirmation'], 'confirmed')
        proposal = clear_proposal()
        proposal['supersedes'] = sha
        self.submit(proposal)
        self.assertEqual(audit.report(self.root)['results'][0]['confirmation'], 'unconfirmed')
        review_path = next((self.work / 'reviews').glob('*.json'))
        review = audit.read(review_path)
        review['recordSha256'] = 'f' * 64
        save(review_path, review)
        with self.assertRaisesRegex(ValueError, 'review target'):
            audit.inspect(self.root)
        del review['recordSha256']
        save(review_path, review)
        with self.assertRaises((ValueError, KeyError)):
            audit.inspect(self.root)

    def test_new_current_material_marks_stale_and_rejects_submission(self):
        self.claim()
        self.submit()
        directory = self.root / 'data/qualifications/ap'
        changed = audit.read(directory / 'packs/synthetic.json')
        changed[0]['hints'][0]['text'] = 'Changed current synthetic material.'
        changed[0]['version'] += 1
        path = directory / 'packs/synthetic-v2.json'
        save(path, changed)
        save(directory / 'manifest.json', {'packs': [{'url': 'packs/synthetic-v2.json',
             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]})
        report = audit.report(self.root)
        self.assertEqual(report['counts']['stale'], 1)
        self.assertEqual(report['results'][0]['state'], 'stale')
        self.assertFalse(report['units'][0]['complete'])
        with self.assertRaisesRegex(ValueError, 'Current material changed'):
            self.submit()

    def test_history_accepts_append_but_rejects_claim_record_overwrite_and_deletion(self):
        self.claim()
        sha = self.submit()
        base = init_git(self.root)
        path = self.record_path(sha)
        original = path.read_bytes()
        audit.review(self.root, sha, 'synthetic-reviewer', 'confirmed', 'Synthetic review only.')
        git(self.root, 'add', '.')
        audit.check_history(self.root, base)
        path.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'edited/deleted'):
            audit.check_history(self.root, base)
        path.write_bytes(original)
        path.unlink()
        with self.assertRaises(ValueError):
            audit.check_history(self.root, base)
        path.write_bytes(original)
        claim_path = self.work / 'claims' / (self.unit + '.json')
        claim_path.write_text(claim_path.read_text() + ' ')
        with self.assertRaises(ValueError):
            audit.check_history(self.root, base)

    def test_history_detects_committed_rewrite_even_after_restoring_final_bytes(self):
        self.claim()
        base = init_git(self.root)
        path = self.work / 'claims' / (self.unit + '.json')
        original = path.read_bytes()
        path.write_bytes(original + b' ')
        commit(self.root, 'Forbidden historical edit')
        path.write_bytes(original)
        commit(self.root, 'Restore original final bytes')
        self.assertFalse(git(self.root, 'diff', base, '--', str(audit.WORK)).stdout)
        with self.assertRaisesRegex(ValueError, 'history'):
            audit.check_history(self.root, base)

    def test_handoff_preserves_previous_results_and_reviews_and_new_owner_continues(self):
        self.claim()
        original_sha = self.submit(candidate())
        audit.review(self.root, original_sha, 'synthetic-reviewer', 'confirmed', 'Synthetic review before handoff.')
        audit.transfer(self.root, self.unit, 'synthetic-successor', 'synthetic-coordinator', 'Previous session stopped.')
        active = audit.inspect(self.root)[4][self.unit]
        self.assertEqual(active['worker'], 'synthetic-successor')
        self.assertEqual(active['preservedRecordShas'], [original_sha])
        self.assertEqual(audit.active_claim_path(active), audit.WORK / 'transfers' / (active['transferId'] + '.json'))
        report = audit.report(self.root)
        self.assertEqual(report['results'][0]['confirmation'], 'confirmed')
        self.assertEqual(report['units'][0]['worker'], 'synthetic-successor')
        next_sha = audit.submit(self.root, 'synthetic-q002', 'synthetic-successor', clear_proposal())
        with self.assertRaisesRegex(ValueError, 'owned'):
            audit.submit(self.root, 'synthetic-q003', self.worker, clear_proposal())
        revision = clear_proposal()
        revision['supersedes'] = original_sha
        revised_sha = audit.submit(self.root, self.id, 'synthetic-successor', revision)
        self.assertTrue(self.record_path(original_sha).is_file())
        self.assertEqual(len(audit.inspect(self.root)[6][original_sha]), 1)
        audit.transfer(self.root, self.unit, 'synthetic-third-session', 'synthetic-coordinator', 'Continue next session.')
        active = audit.inspect(self.root)[4][self.unit]
        self.assertEqual(set(active['preservedRecordShas']), {original_sha, next_sha, revised_sha})
        self.assertEqual(active['worker'], 'synthetic-third-session')

    def test_handoff_rejects_late_old_owner_record_even_with_valid_original_claim(self):
        self.claim()
        self.submit()
        late_sha = audit.submit(self.root, 'synthetic-q002', self.worker, clear_proposal())
        late_path = self.record_path(late_sha)
        late_bytes = late_path.read_bytes()
        late_path.unlink()
        audit.transfer(self.root, self.unit, 'synthetic-successor', 'synthetic-coordinator', 'Stop old session.')
        self.assertNotIn(late_sha, audit.inspect(self.root)[4][self.unit]['preservedRecordShas'])
        late_path.write_bytes(late_bytes)
        with self.assertRaisesRegex(ValueError, 'Late submission'):
            audit.inspect(self.root)

    def test_handoff_rejects_forks_missing_grandfather_and_foreign_snapshot_records(self):
        self.claim()
        old_sha = self.submit()
        audit.claim(self.root, 'unit-02', 'synthetic-other-unit-worker')
        foreign_sha = audit.submit(self.root, 'synthetic-q021', 'synthetic-other-unit-worker', clear_proposal())
        audit.transfer(self.root, self.unit, 'synthetic-successor', 'synthetic-coordinator', 'Stop old session.')
        first_path = next((self.work / 'transfers').glob('*.json'))
        first = audit.read(first_path)
        fork = copy.deepcopy(first)
        fork['transferId'] = 'synthetic-fork'
        fork['worker'] = 'synthetic-competing-successor'
        fork_path = first_path.with_name('synthetic-fork.json')
        save(fork_path, fork)
        with self.assertRaisesRegex(ValueError, 'Forked ownership'):
            audit.inspect(self.root)
        fork_path.unlink()
        missing = copy.deepcopy(first)
        missing['preservedRecordShas'] = []
        save(first_path, missing)
        with self.assertRaisesRegex(ValueError, 'Late submission'):
            audit.inspect(self.root)
        foreign = copy.deepcopy(first)
        foreign['preservedRecordShas'].append(foreign_sha)
        save(first_path, foreign)
        with self.assertRaisesRegex(ValueError, 'foreign records'):
            audit.inspect(self.root)
        save(first_path, first)
        audit.transfer(self.root, self.unit, 'synthetic-third-session', 'synthetic-coordinator', 'Continue next session.')
        second = audit.inspect(self.root)[4][self.unit]
        self.assertIn(old_sha, second['preservedRecordShas'])
        second['preservedRecordShas'] = []
        save(self.root / audit.active_claim_path(second), second)
        with self.assertRaises(ValueError, msg='A later handoff must retain all records grandfathered in earlier handoffs.'):
            audit.inspect(self.root)

    def test_generated_json_report_is_excluded_from_authoritative_input_digest(self):
        first = audit.report(self.root)
        save(self.work / 'report.json', first)
        second = audit.report(self.root)
        self.assertEqual(first, second)
        save(self.work / 'report.json', second)
        self.assertEqual(audit.report(self.root), first)
        self.claim()
        self.assertNotEqual(audit.report(self.root)['inputDigest'], first['inputDigest'])

    def test_cli_requires_claim_and_review_target_in_published_ref(self):
        init_git(self.root)
        ref = 'refs/remotes/origin/audit-fixture'
        git(self.root, 'update-ref', ref, 'HEAD')
        self.claim()
        proposal = Path(self.temp.name) / 'proposal.json'
        save(proposal, clear_proposal())

        def cli(*arguments):
            return subprocess.run([sys.executable, str(ROOT / 'tools/hint_foundations_audit.py'),
                                   '--root', str(self.root), *arguments, '--published-ref', ref],
                                  text=True, capture_output=True)

        result = cli('submit', self.id, '--worker', self.worker, '--file', str(proposal))
        self.assertNotEqual(result.returncode, 0, 'An unpushed local claim must not authorize the CLI.')
        self.assertFalse((self.work / 'records').exists())
        commit(self.root, 'Publish synthetic reservation')
        git(self.root, 'update-ref', ref, 'HEAD')
        result = cli('submit', self.id, '--worker', self.worker, '--file', str(proposal))
        self.assertEqual(result.returncode, 0, result.stderr)
        sha = result.stdout.strip()
        review_args = ('review', sha, '--worker', 'synthetic-reviewer', '--decision', 'confirmed',
                       '--reason', 'Synthetic CLI review only.')
        result = cli(*review_args)
        self.assertNotEqual(result.returncode, 0, 'An unpublished result must not be independently reviewed through the CLI.')
        self.assertFalse((self.work / 'reviews').exists())
        commit(self.root, 'Publish synthetic result')
        git(self.root, 'update-ref', ref, 'HEAD')
        result = cli(*review_args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list((self.work / 'reviews').glob('*.json'))), 1)
        audit.claim(self.root, 'unit-02', 'synthetic-other-author')
        commit(self.root, 'Publish another synthetic reservation')
        git(self.root, 'update-ref', ref, 'HEAD')
        claim_path = self.work / 'claims/unit-02.json'
        changed = audit.read(claim_path)
        changed['worker'] = 'synthetic-impostor'
        save(claim_path, changed)
        result = cli('submit', 'synthetic-q021', '--worker', 'synthetic-impostor', '--file', str(proposal))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Published reservation/record differs', result.stderr)
        self.assertEqual(len(list((self.work / 'records').glob('*/*.json'))), 1)

    def test_two_clones_same_unit_have_one_remote_claim_winner(self):
        base = init_git(self.root)
        remote = Path(self.temp.name) / 'remote.git'
        git(Path(self.temp.name), 'clone', '--bare', str(self.root), str(remote))
        clones = [Path(self.temp.name) / name for name in ('worker-a', 'worker-b')]
        for index, clone in enumerate(clones):
            git(Path(self.temp.name), 'clone', str(remote), str(clone))
            git(clone, 'config', 'user.name', 'Synthetic test')
            git(clone, 'config', 'user.email', 'synthetic@example.invalid')
            audit.claim(clone, self.unit, f'synthetic-worker-{index}')
            commit(clone, 'Reserve same synthetic unit')
            self.assertEqual(git(clone, 'rev-parse', 'HEAD^').stdout.strip(), base)
        first = git(clones[0], 'push', 'origin', 'HEAD:refs/heads/audit', check=False)
        second = git(clones[1], 'push', 'origin', 'HEAD:refs/heads/audit', check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertNotEqual(second.returncode, 0, 'A stale same-unit reservation must lose publication.')
        loser = clones[1]
        git(loser, 'fetch', 'origin')
        git(loser, 'reset', '--hard', 'origin/audit')
        self.assertEqual(audit.inspect(loser)[4][self.unit]['worker'], 'synthetic-worker-0')
        with self.assertRaises(FileExistsError):
            audit.claim(loser, self.unit, 'synthetic-worker-1')


class ReportReadability(unittest.TestCase):
    def test_candidate_score_and_evidence_are_visible_in_report(self):
        row = {'questionId': 'synthetic-q1', 'title': '合成問題1', 'unitId': 'unit-01', 'topic': '合成分野',
               'state': 'candidate', 'total': 2, 'severity': 'low', 'confirmation': 'unconfirmed',
               'recordPath': 'work/ap/hint-foundations/records/unit-01/synthetic.json',
               'evidence': [{'hintStep': 2, 'quote': '式|を使う', 'learnerBlock': '変数の意味で止まる',
                             'neededExplanation': '変数と単位を説明する'}], 'support': None, 'missingContext': None}
        data = {'counts': {'unreviewed': 799, 'candidate': 1, 'clear': 0, 'uncertain': 0, 'stale': 0},
                'baseCommit': 'synthetic', 'inputDigest': 'synthetic', 'results': [row], 'units': []}
        rendered = audit.markdown(data)
        for expected in ('合成問題1', '候補', '| 2 |', 'H2「式&#124;を使う」', '変数の意味で止まる', '変数と単位を説明する', '未確認'):
            self.assertIn(expected, rendered)


if __name__ == '__main__':
    unittest.main(verbosity=2)
