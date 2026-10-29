"""Correction integration and negative gates in an isolated, reviewed source tree."""
import copy,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import ap_lesson_quality as quality
spec=importlib.util.spec_from_file_location('transcriptions',ROOT/'tools/apply-transcriptions.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
ID='r04a-q13'
class SourceCorrections(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='ap-source-correction-contract-');cls.root=Path(cls.temp.name)
  for folder in [str(quality.WORK),'work/ap/hint-revisions','data/lessons','data/lesson-reviews','data/transcriptions','data/transcription-reviews','data/transcription-context-revisions','content/ap/study-context-reviews']:
   shutil.copytree(ROOT/folder,cls.root/folder)
  for name in ['data/questions.json','data/answer-keys.json','data/sources.json','data/source-crops.json','data/transcription-image-retentions.json','data/transcription-progress.json','content/ap/study-context.json']:
   dest=cls.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
  paths={name for row in quality.read(ROOT/quality.WORK/'inventory.json') for name in row['sourceHashes']}
  for file in (ROOT/'data/transcriptions').glob('*.json'):
   for record in quality.read(file):paths.update(p['path'] for p in record.get('sourceEvidence',[]))
  paths.update(r['priorReview'] for r in quality.read(ROOT/'data/transcription-image-retentions.json') if r.get('priorReview'))
  for name in paths:
   dest=cls.root/name
   if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
  cls.files={p.relative_to(cls.root):p.read_bytes() for p in cls.root.rglob('*.json')}
  journals=[quality.read(p) for p in (cls.root/'data/transcription-context-revisions').glob('*.json')]
  cls.journal=next(j for j in journals if any(i['id']==ID and i.get('afterQuestion',{}).get('version')==4 for i in j['items']))
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def setUp(self):
  for p in self.root.rglob('*.json'):
   if p.relative_to(self.root) not in self.files:p.unlink()
  for p,body in self.files.items():(self.root/p).write_bytes(body)
  self.work=self.root/quality.WORK;self.bank=quality.read(self.root/'data/questions.json')
 def correction(self):return quality.read(self.work/'source-corrections.json')[0]
 def save_correction(self,c):quality.write(self.work/'source-corrections.json',[c])
 def target(self):return next(q for q in self.bank if q['id']==ID)
 def test_current_version_and_exact_approved_composition(self):
  self.assertEqual(quality.validate_workspace(self.root)['reviewedUnderCurrentRules'],800);q=self.target();self.assertEqual(q['version'],4)
  self.assertTrue(q['choices'][0]['text'].startswith('フェールセーフ'));self.assertTrue(q['choices'][1]['text'].startswith('フェールソフト'))
  self.assertNotIn(ID,quality.legacy_classification_hashes(self.root))
 def test_reapplication_and_lesson_acceptance_do_not_undo_or_increment(self):
  names=['data/questions.json','content/ap/study-context.json','content/ap/study-context-reviews/root.json','content/ap/study-context-reviews/r04a.json']
  before={p:(self.root/p).read_bytes() for p in names};module.apply(self.root);quality.accept_batch(self.root,'batch-06')
  self.assertEqual(before,{p:(self.root/p).read_bytes() for p in names})
 def test_exact_before_object_transitions_once_and_archives_both_audits(self):
  item=next(i for i in self.journal['items'] if i['id']==ID);self.bank=[item['beforeQuestion'] if q['id']==ID else q for q in self.bank];quality.write(self.root/'data/questions.json',self.bank)
  context=quality.read(self.root/'content/ap/study-context.json');context['items']=[item['beforeContextItem'] if x['questionId']==ID else x for x in context['items']];quality.write(self.root/'content/ap/study-context.json',context)
  quality.write(self.root/'content/ap/study-context-reviews/root.json',self.journal['beforeRootReview'])
  for exam,audit in self.journal['beforeExamReviews'].items():quality.write(self.root/f'content/ap/study-context-reviews/{exam}.json',audit)
  module.apply(self.root);quality.validate_workspace(self.root)
  self.assertEqual((self.root/'data/questions.json').read_bytes(),self.files[Path('data/questions.json')])
  self.assertEqual(quality.read(self.root/'content/ap/study-context.json'),quality.read(ROOT/'content/ap/study-context.json'))
 def test_unregistered_original_edit_is_rejected_before_bank_write(self):
  self.bank[0]['stem']+=' unauthorized';quality.write(self.root/'data/questions.json',self.bank);before=(self.root/'data/questions.json').read_bytes()
  with self.assertRaises(ValueError):module.apply(self.root)
  self.assertEqual(before,(self.root/'data/questions.json').read_bytes())
 def test_equal_boolean_answer_is_not_accepted(self):
  q=next(q for q in self.bank if q['id']=='r07h-q14');self.assertEqual(q['answer'],1);q['answer']=True
  with self.assertRaises(ValueError):quality.transcription_transition(self.root,self.bank)
 def test_stale_transcription_cannot_use_old_review(self):
  path=self.root/'data/transcriptions/r04a.json';rows=quality.read(path);next(r for r in rows if r['id']==ID)['choices'][0]['text']+=' arbitrary';quality.write(path,rows)
  with self.assertRaises(ValueError):quality.validate_workspace(self.root)
 def test_self_review_cannot_be_registered(self):
  path=self.root/'data/transcription-reviews/r04a.json';rows=quality.read(path);r=next(r for r in rows if r['id']==ID);r['reviewer']=next(r for r in quality.read(self.root/'data/transcriptions/r04a.json') if r['id']==ID)['author'];quality.write(path,rows);c=self.correction();c['reviewSHA256']=quality.digest(r);self.save_correction(c)
  with self.assertRaises(ValueError):quality.validate_workspace(self.root)
 def test_unresolved_current_review_cannot_be_registered(self):
  path=self.root/'data/transcription-reviews/r04a.json';rows=quality.read(path);r=next(r for r in rows if r['id']==ID);r['issues']=['unresolved'];quality.write(path,rows);c=self.correction();c['reviewSHA256']=quality.digest(r);self.save_correction(c)
  with self.assertRaises(ValueError):quality.validate_workspace(self.root)
 def test_independent_evidence_and_old_archive_are_hash_bound(self):
  c=self.correction();path=self.root/c['independentApproval'];v=quality.read(path);v['evidence']+=' changed';quality.write(path,v)
  with self.assertRaises(ValueError):quality.validate_workspace(self.root)
 def test_old_history_cannot_be_rewritten(self):
  c=self.correction();c['originalReview']['evidence']+=' changed';self.save_correction(c)
  with self.assertRaises(ValueError):quality.validate_workspace(self.root)
 def test_boolean_choice_index_rejected_even_if_integer_equal(self):
  c=self.correction();c['replacements'][0]['index']=False;self.save_correction(c)
  with self.assertRaises(ValueError):quality.validate_workspace(self.root)
 def test_corrected_question_requires_exact_current_classification_hash(self):
  for bad in [None,self.correction()['originalQuestionSHA256']]:
   context=quality.read(self.root/'content/ap/study-context.json');next(x for x in context['items'] if x['questionId']==ID)['sourceHash']=bad;quality.write(self.root/'content/ap/study-context.json',context)
   before=(self.root/'data/questions.json').read_bytes()
   with self.assertRaises(ValueError):module.apply(self.root)
   self.assertEqual(before,(self.root/'data/questions.json').read_bytes())
if __name__=='__main__':unittest.main()
