"""Quality gates tested with synthetic authors/reviewers in an isolated tree.

These approvals are contract fixtures and never certify real material content.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import ap_lesson_quality as quality


class QualityGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='ap-quality-contract-')
        cls.root = Path(cls.temp.name)
        shutil.copytree(ROOT/quality.WORK, cls.root/quality.WORK)
        shutil.copytree(ROOT/'data/lessons', cls.root/'data/lessons')
        shutil.copytree(ROOT/'data/lesson-reviews', cls.root/'data/lesson-reviews')
        for name in ['questions.json', 'answer-keys.json', 'sources.json', 'source-crops.json']:
            shutil.copyfile(ROOT/'data'/name, cls.root/'data'/name)
        work = cls.root/quality.WORK
        manifest = quality.read(work/'manifest.json')
        manifest['baselineFiles'] = {str(p.relative_to(work/'baseline')): quality.file_digest(p) for p in (work/'baseline').rglob('*') if p.is_file()}
        quality.write(work/'manifest.json', manifest)
        inventory = quality.read(work/'inventory.json')
        for row in inventory:
            for relative in row['sourceHashes']:
                dest = cls.root/relative
                if not dest.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT/relative, dest)
        # Start from the immutable source bank even if the real pilot has already
        # been registered by the integration owner during this parallel task.
        quality.write(work/'registrations.json', [])
        quality.write(work/'source-corrections.json', [])
        shutil.copyfile(work/'baseline/questions.json', cls.root/'data/questions.json')
        shutil.copytree(work/'baseline/lessons', cls.root/'data/lessons', dirs_exist_ok=True)
        # Real remaining batches may now be claimed, revised or registered.
        # Contract fixtures start from an unassigned baseline, independent of
        # the live content workflow and its genuine author/reviewer identities.
        baseline_lessons = {row['id']: row for path in (work/'baseline/lessons').glob('*.json') for row in quality.read(path)}
        for folder in (work/'batches').iterdir():
            if not folder.is_dir() or folder.name == 'pilot-00':
                continue
            assignment = quality.read(folder/'assignment.json')
            assignment.update(author=None, reviewer=None)
            quality.write(folder/'assignment.json', assignment)
            drafts = quality.read(folder/'drafts.json')
            for draft in drafts:
                draft.update(author=None, decision='pending', lesson=copy.deepcopy(baseline_lessons[draft['id']]), design=None)
            quality.write(folder/'drafts.json', drafts)
            quality.write(folder/'reviews.json', [])
        cls.base_files = {p.relative_to(cls.root): p.read_bytes() for p in cls.root.rglob('*') if p.is_file()}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        for relative, body in self.base_files.items():
            (self.root/relative).write_bytes(body)
        self.work = self.root/quality.WORK
        self.folder = self.work/'batches/pilot-00'
        self.state = quality.load_workspace(self.root)
        assignment = quality.read(self.folder/'assignment.json')
        assignment['author'] = 'synthetic-author'
        quality.write(self.folder/'assignment.json', assignment)
        self.drafts = quality.read(self.folder/'drafts.json')
        self.reviews = []
        for draft in self.drafts:
            id = draft['id']
            draft.update(author='synthetic-author', decision='keep', lesson=copy.deepcopy(self.state['lessons'][id]))
            draft['design'] = {'obstacle': 'Synthetic contract fixture only.', 'stages': [{'newInformation': 'Synthetic information.', 'remainingWork': 'Synthetic remaining decision.', 'revealsAnswer': h['revealsAnswer'], 'reason': 'Synthetic flag explanation.'} for h in draft['lesson']['hints']], 'changes': [], 'sourceNotes': ['Synthetic, not real content review.']}
            q = self.state['original'][id]
            self.reviews.append({'id': id, 'author': draft['author'], 'reviewer': 'synthetic-reviewer', 'status': 'approved', 'checkedAt': '2026-10-26T00:00:00Z', 'baseLessonSHA256': draft['baseLessonSHA256'], 'reviewedLessonSHA256': quality.digest(draft['lesson']), 'questionSHA256': self.state['inventory'][id]['baselineQuestionSHA256'], 'sourceHashes': self.state['inventory'][id]['sourceHashes'], 'checks': {**{k: True for k in quality.CHECKS}, 'calculation': 'not-applicable'}, 'notes': 'Synthetic contract proof only.', 'officialAnswer': q['choices'][q['answer']]['label'], 'independentResult': 'Synthetic result only.', 'issues': []})
        self.save()

    def save(self):
        quality.write(self.folder/'drafts.json', self.drafts)
        quality.write(self.folder/'reviews.json', self.reviews)

    def rejects(self, fn, text=None):
        with self.assertRaises(ValueError) as error:
            fn()
        if text:
            self.assertIn(text, str(error.exception))

    def test_all800_and39disjoint_handoffs(self):
        state = quality.load_workspace(self.root)
        self.assertEqual(len(state['inventory']), 800)
        assignments = state['assignments']
        self.assertEqual(len(assignments), 40)
        self.assertEqual(len(set(id for a in assignments.values() for id in a['questionIds'])), 800)
        self.assertEqual(sum(len(a['questionIds']) for k,a in assignments.items() if k!='pilot-00'), 780)

    def test_claim_records_owner_and_prevents_overlapping_assignment(self):
        before=(self.root/'data/questions.json').read_bytes()
        result=quality.claim_batch(self.root,'batch-01','synthetic-external-author','synthetic-external-reviewer')
        self.assertFalse(result['materialChanged'])
        self.rejects(lambda: quality.claim_batch(self.root,'batch-01','another-author'), 'already assigned')
        self.assertEqual(before,(self.root/'data/questions.json').read_bytes())

    def test_unregistered_handoff_draft_format_is_checked_separately(self):
        self.assertEqual(quality.check_drafts(self.root)['batches'],40)
        p=self.work/'batches/batch-01/drafts.json';rows=quality.read(p)
        rows[0]['lesson']['hints'][0]['revealsAnswer']='false';quality.write(p,rows)
        self.rejects(lambda:quality.check_drafts(self.root),'Invalid AP hint')

    def test_keep_registration_leaves_versions_and_bank_unchanged(self):
        before = (self.root/'data/questions.json').read_bytes()
        result = quality.accept_batch(self.root, 'pilot-00')
        self.assertTrue(result['registered'])
        self.assertEqual((self.root/'data/questions.json').read_bytes(), before)
        self.assertEqual(quality.validate_workspace(self.root)['reviewedUnderCurrentRules'], 20)

    def test_first_hint_true_allowed_changed_version_exactly_once(self):
        draft = self.drafts[0]
        draft['decision'] = 'revise'
        draft['lesson']['hints'][0]['revealsAnswer'] = not draft['lesson']['hints'][0]['revealsAnswer']
        draft['design']['stages'][0]['revealsAnswer'] = draft['lesson']['hints'][0]['revealsAnswer']
        self.reviews[0]['reviewedLessonSHA256'] = quality.digest(draft['lesson'])
        self.save()
        quality.accept_batch(self.root, 'pilot-00')
        bank = quality.read(self.root/'data/questions.json')
        q = next(q for q in bank if q['id']==draft['id'])
        self.assertEqual(q['version'], draft['baseVersion']+1)
        before = {str(p): p.read_bytes() for p in [self.root/'data/questions.json', self.work/'registrations.json', *list((self.root/'data/lessons').glob('*.json'))]}
        quality.accept_batch(self.root, 'pilot-00')
        self.assertEqual(before, {p: Path(p).read_bytes() for p in before})

    def test_pending_draft_not_approved(self):
        self.drafts[0]['decision'] = 'pending'; self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Unfinished')

    def _compile_context(self, id, source_hash):
        spec=importlib.util.spec_from_file_location('quality_context_builder',ROOT/'tools/build-content.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        path=self.root/'content/context.json';path.parent.mkdir(exist_ok=True)
        quality.write(path,{'format':'hitomon-study-context','version':1,'qualificationId':'ap','items':[{'questionId':id,'mode':'paperless','reason':'Synthetic classification fixture only.','sourceHash':source_hash}]})
        config={'id':'ap','adapter':'ipa-ap','questionSource':'data/questions.json','studyContextSource':'content/context.json','topics':[{'id':'synthetic'}]}
        output=self.root/'generated-context';output.mkdir(exist_ok=True)
        return builder.compile_learning_tools(self.root,config,[{'id':id,'packId':'synthetic'}],output)

    def _register_changed_lesson(self):
        draft=self.drafts[0];draft['decision']='revise';draft['lesson']['explanation']+=' Synthetic reviewed addition.'
        self.reviews[0]['reviewedLessonSHA256']=quality.digest(draft['lesson']);self.save()
        quality.accept_batch(self.root,'pilot-00')
        return draft['id']

    def test_classification_old_hash_survives_only_registered_lesson_revision(self):
        id=self._register_changed_lesson()
        result=self._compile_context(id,self.state['inventory'][id]['baselineQuestionSHA256'])
        self.assertEqual(result['studyContext']['count'],1)

    def test_classification_wrong_old_hash_rejected_after_registration(self):
        id=self._register_changed_lesson()
        self.rejects(lambda:self._compile_context(id,'f'*64),'Classification source changed')

    def test_classification_cannot_hide_unregistered_or_original_question_change(self):
        id=self.drafts[0]['id'];bank=quality.read(self.root/'data/questions.json')
        q=next(q for q in bank if q['id']==id);q['explanation']+=' Unregistered.';quality.write(self.root/'data/questions.json',bank)
        old_hash=self.state['inventory'][id]['baselineQuestionSHA256']
        self.rejects(lambda:self._compile_context(id,old_hash),'AP bank differs')

        quality.write(self.root/'data/questions.json',list(self.state['original'].values()))
        self._register_changed_lesson();bank=quality.read(self.root/'data/questions.json');q=next(q for q in bank if q['id']==id);q['stem']+=' Changed original.';quality.write(self.root/'data/questions.json',bank)
        self.rejects(lambda:self._compile_context(id,old_hash),'AP bank differs')

    def test_registered_answer_integer_cannot_be_replaced_with_equal_boolean(self):
        self._register_changed_lesson()
        id='r07h-q14';bank=quality.read(self.root/'data/questions.json');q=next(q for q in bank if q['id']==id)
        self.assertEqual(q['answer'],1);q['answer']=True;quality.write(self.root/'data/questions.json',bank)
        self.rejects(lambda:self._compile_context(id,self.state['inventory'][id]['baselineQuestionSHA256']),'AP bank differs')

    def test_missing_review_rejected_before_any_write(self):
        before = (self.root/'data/questions.json').read_bytes()
        self.reviews.pop(); self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Missing independent')
        self.assertEqual(before, (self.root/'data/questions.json').read_bytes())
        self.assertEqual(quality.read(self.work/'registrations.json'), [])

    def test_self_review_rejected(self):
        self.reviews[0]['reviewer'] = self.reviews[0]['author']; self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Independent')

    def test_stale_lesson_review_rejected(self):
        self.drafts[0]['decision']='revise'; self.drafts[0]['lesson']['explanation']+=' Changed.'; self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Stale review')

    def test_wrong_question_context_hash_rejected(self):
        self.reviews[0]['questionSHA256']='f'*64; self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Stale review')

    def test_wrong_source_hash_rejected(self):
        self.reviews[0]['sourceHashes']={}; self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'source hashes')

    def test_modified_original_image_rejected(self):
        p=next(p for p in self.state['inventory'][self.drafts[0]['id']]['sourceHashes'] if p.startswith('assets/'))
        (self.root/p).write_bytes(b'modified original')
        self.rejects(lambda: quality.validate_workspace(self.root), 'Original source changed')

    def test_original_recovery_coordinates_rejected(self):
        p=self.root/'data/source-crops.json';rows=quality.read(p)
        # A changed rectangle is not caught by a corpus check of ID/page alone.
        rows[0]['sourceRectangle']=[0,0,1,1]
        quality.write(p,rows)
        self.rejects(lambda: quality.validate_workspace(self.root), 'Original recovery/source metadata')

    def test_immutable_question_change_rejected(self):
        bank=quality.read(self.root/'data/questions.json'); bank[0]['answer']=(bank[0]['answer']+1)%4;quality.write(self.root/'data/questions.json',bank)
        self.rejects(lambda: quality.validate_workspace(self.root), 'immutable original')

    def test_unregistered_lesson_edit_rejected(self):
        p=self.root/self.state['inventory'][self.drafts[0]['id']]['lessonFile'];rows=quality.read(p);rows[0]['explanation']+=' Unreviewed.';quality.write(p,rows)
        self.rejects(lambda: quality.validate_workspace(self.root), 'Current lesson source')

    def test_unregistered_bank_edit_rejected(self):
        rows=quality.read(self.root/'data/questions.json');rows[0]['hints'][0]['revealsAnswer']=not rows[0]['hints'][0]['revealsAnswer'];quality.write(self.root/'data/questions.json',rows)
        self.rejects(lambda: quality.validate_workspace(self.root), 'AP bank differs')

    def test_wrong_annual_lesson_file_rejected(self):
        files=list((self.root/'data/lessons').glob('*.json'))
        first,second=files[:2];a,b=quality.read(first),quality.read(second);a[0],b[0]=b[0],a[0]
        quality.write(first,a);quality.write(second,b)
        self.rejects(lambda: quality.validate_workspace(self.root), 'moved to another exam')

    def test_keep_cannot_hide_change(self):
        self.drafts[0]['lesson']['explanation']+=' Changed.';self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Keep decision')

    def test_duplicate_review_rejected(self):
        self.reviews.append(copy.deepcopy(self.reviews[0]));self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'duplicate IDs')

    def test_foreign_review_rejected(self):
        self.reviews[0]['id']='r03a-q80' if self.reviews[0]['id']!='r03a-q80' else 'r03a-q79';self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Foreign review')

    def test_missing_stage_reason_rejected(self):
        self.drafts[0]['design']['stages'][0]['reason']='';self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'stage design')

    def test_missing_review_check_rejected(self):
        self.reviews[0]['checks']['hints']=False;self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Incomplete')

    def test_naive_review_date_rejected(self):
        self.reviews[0]['checkedAt']='2026-10-26';self.save()
        self.rejects(lambda: quality.accept_batch(self.root,'pilot-00'), 'Invalid review date')

    def test_changed_baseline_archive_rejected(self):
        p=self.work/'baseline/questions.json';rows=quality.read(p);rows[0]['answer']=0;quality.write(p,rows)
        self.rejects(lambda: quality.load_workspace(self.root),'Archived baseline changed')

    def test_unregistered_approval_is_not_publication(self):
        report=quality.progress(self.root)
        self.assertEqual(report['counts']['reviewed'],20)
        self.assertEqual(report['counts']['approved'],0)
        self.assertNotIn('published',report['counts'])
        self.assertEqual(quality.read(self.work/'registrations.json'),[])


if __name__ == '__main__':
    unittest.main()
