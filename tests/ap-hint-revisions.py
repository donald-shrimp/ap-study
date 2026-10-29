"""Follow-up approvals must bind the exact prior lesson, question and final hints."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import ap_lesson_quality as q

class Followup(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.folder=self.root/'work/ap/hint-revisions/one'
        self.folder.mkdir(parents=True); (self.folder/'group-01').mkdir()
        self.lesson={'id':'x','checkedAgainst':'official-question-image-and-answer-key', 'summary':'s','explanation':'e','takeaway':'t','choiceReasons':['a','b','c','d'],'hints':[{'title':'h','text':'before','revealsAnswer':False} for _ in range(3)]}
        self.question={'id':'x','version':3,'choices':[{'label':'ア'}],'answer':0,**{k:copy.deepcopy(self.lesson[k]) for k in q.FIELDS}}
        base={'id':'x','baseLesson':self.lesson,'baseQuestion':self.question,'sourceHashes':{}}
        self.write('baseline.json',[base]); self.write('manifest.json',{'baselineSha256':q.digest([base]),'questionIds':['x'],'groups':['group-01']})
        q.write(self.folder.parent/'registrations.json',['one'])
        lesson=copy.deepcopy(self.lesson);lesson['hints'][0]['text']='after'
        self.d={'id':'x','author':'writer','baseLessonSHA256':q.digest(self.lesson),'questionSHA256':q.digest(self.question),'lesson':lesson,'design':{'obstacle':'term unknown','candidateDecision':'adopt','stages':[{'newInformation':'definition','remainingWork':'apply','reason':'comparison left','revealsAnswer':False} for _ in range(3)]}}
        self.v={'id':'x','author':'writer','reviewer':'reader','status':'approved','issues':[],'checkedAt':datetime.now(timezone.utc).isoformat(),'baseLessonSHA256':self.d['baseLessonSHA256'],'questionSHA256':self.d['questionSHA256'],'reviewedLessonSHA256':q.digest(lesson),'sourceHashes':{},'checks':{**{k:True for k in q.CHECKS},'calculation':'not-applicable'},'officialAnswer':'ア','notes':'read all hints','independentResult':'ア'}
        self.save()
    def write(self,path,data): q.write(self.folder/path,data)
    def save(self): self.write('group-01/drafts.json',[self.d]);self.write('group-01/reviews.json',[self.v])
    def apply(self):
        lessons={'x':copy.deepcopy(self.lesson)}; bank={'x':copy.deepcopy(self.question)}
        q.apply_followup_revisions({'root':self.root,'inventory':{'x':{'sourceHashes':{}}}},lessons,bank)
        return lessons,bank
    def test_approved_revision_increments_once_on_each_rebuild(self):
        self.assertEqual(self.apply()[1]['x']['version'],4)
        self.assertEqual(self.apply(),self.apply())
        self.assertEqual(self.apply()[0]['x'],self.d['lesson'])
    def test_no_change_preserves_version(self):
        self.d['lesson']=copy.deepcopy(self.lesson);self.v['reviewedLessonSHA256']=q.digest(self.lesson);self.save()
        self.assertEqual(self.apply()[1]['x']['version'],3)
    def test_missing_review_rejected(self):
        self.write('group-01/reviews.json',[])
        with self.assertRaises(ValueError): self.apply()
    def test_self_review_rejected(self):
        self.v['reviewer']='writer';self.save()
        with self.assertRaises(ValueError): self.apply()
    def test_changed_hint_invalidates_review(self):
        self.d['lesson']['hints'][0]['text']='unreviewed';self.save()
        with self.assertRaises(ValueError): self.apply()
    def test_stale_prior_lesson_rejected(self):
        self.lesson['summary']='changed'
        with self.assertRaises(ValueError): self.apply()
    def test_unrelated_fields_rejected_even_with_new_hash(self):
        self.d['lesson']['explanation']='unauthorized';self.v['reviewedLessonSHA256']=q.digest(self.d['lesson']);self.save()
        with self.assertRaises(ValueError): self.apply()
    def test_incomplete_checks_rejected(self):
        self.v['checks']['hints']=False;self.save()
        with self.assertRaises(ValueError): self.apply()
    def test_unsafe_registration_rejected(self):
        q.write(self.folder.parent/'registrations.json',['../one'])
        with self.assertRaises(ValueError): self.apply()
    def test_missing_source_set_compared_with_inventory(self):
        with self.assertRaises(ValueError):
            q.apply_followup_revisions({'root':self.root,'inventory':{'x':{'sourceHashes':{'required':'sha'}}}}, {'x':copy.deepcopy(self.lesson)}, {'x':copy.deepcopy(self.question)})
    def test_whitespace_and_nontext_reason_rejected(self):
        for key,value in [('notes',' '),('independentResult',True)]:
            old=self.v[key];self.v[key]=value;self.save()
            with self.assertRaises(ValueError): self.apply()
            self.v[key]=old
        self.d['design']['stages'][0]['reason']=['not text'];self.save()
        with self.assertRaises(ValueError): self.apply()
    def test_transcription_before_and_after_retain_revised_hints(self):
        original=copy.deepcopy(self.question);original['version']=2;original['choices']=[{'label':'ア','text':'old'}]
        state={'root':self.root,'lessons':{'x':copy.deepcopy(self.lesson)},'original':{'x':original},'registrations':[],'sourceCorrections':{'x':{'choices':copy.deepcopy(self.question['choices'])}},'inventory':{'x':{'sourceHashes':{}}}}
        _,before=q.expected_material(state,corrections=False)
        _,after=q.expected_material(state)
        self.assertEqual(before[0]['choices'],original['choices'])
        self.assertEqual(before[0]['hints'],self.d['lesson']['hints'])
        self.assertEqual(before[0]['version'],3)
        self.assertEqual(after[0]['version'],4)
    def test_wrong_source_set_rejected(self):
        self.v['sourceHashes']={'missing':'fake'};self.save()
        with self.assertRaises(ValueError): self.apply()
if __name__=='__main__': unittest.main()
