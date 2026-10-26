"""Synthetic regression coverage: stage actual drafts, never regenerate/approve them."""
import contextlib, copy, hashlib, importlib.util, io, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
spec = importlib.util.spec_from_file_location('prepare_fp', ROOT/'tools/prepare-fp2-delivery.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

class Preparation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fp2-preparation-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.draft, self.cache, self.out = (self.root/name for name in ['draft', 'cache', 'output'])
        self.draft.mkdir()
        q = json.loads((ROOT/'delivery/content/fp2/questions.json').read_text())[0]
        c = json.loads((ROOT/'content/fp2/practical-cases.json').read_text())[0]
        c['status'] = 'draft'
        c['sourceImages'], c['bodyFigures'] = [], []
        self.qs, self.cases, self.sources = [q], [c], {}
        pdf = fitz.open();pdf.new_page(width=600, height=800)
        content = pdf.tobytes();pdf.close()
        for part, materials in [('g2', self.qs), ('j2', self.cases)]:
            for suffix in ['q', 'a']:
                name = f'{part}_209901_{suffix}.pdf';relative = 'sources/fp2/'+name
                target = self.cache/relative;target.parent.mkdir(parents=True, exist_ok=True);target.write_bytes(content)
                self.sources[relative] = hashlib.sha256(content).hexdigest()
                key = 'question' if suffix=='q' else 'answer'
                for m in materials:
                    m['sourceRecord'][key+'Sha256'] = self.sources[relative]
                    m['sourceRecord'][key+'Url'] = tool.BASE+name
        self.write()

    def write(self):
        for name, data in [('questions.json', self.qs), ('practical-cases.json', self.cases), ('source-files.json', self.sources)]:
            (self.draft/name).write_text(json.dumps(data, ensure_ascii=False, indent=1)+'\n')

    def run_prepare(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return tool.prepare(self.draft, self.out, self.cache)

    def reject(self):
        self.write()
        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
            self.run_prepare()
        self.assertFalse(self.out.exists())
        self.assertFalse(list(self.root.glob('fp2-prepare-*')))

    def test_preserves_authored_bytes_and_existing_review_file(self):
        (self.draft/'question-reviews.json').write_text('[{"synthetic":"preserve only; not an approval"}]\n')
        result = self.run_prepare()
        self.assertEqual((result['questions'], result['cases']), (1, 1))
        for file in self.draft.iterdir():
            self.assertEqual(file.read_bytes(), (self.out/'content/fp2'/file.name).read_bytes())
        self.assertEqual(json.loads((self.out/'content/fp2/questions.json').read_text())[0]['enrichment'], 'draft')

    def test_verified_download_path(self):
        def fetch(name): return (self.cache/'sources/fp2'/name).read_bytes()
        with patch.object(tool, 'fetch_pdf', side_effect=fetch) as download:
            tool.prepare(self.draft, self.out)
        self.assertEqual(download.call_count, 4)

    def test_rejects_wrong_pdf_and_does_not_create_output(self):
        next((self.cache/'sources/fp2').iterdir()).write_bytes(b'%PDF-corrupted')
        self.reject()

    def test_rejects_nonnumeric_reference(self):
        f = copy.deepcopy(self.cases[0]['items'][0]['fields'][0])
        f.update(type='numeric', maxLength=100, numeric={'unit':'yen','decimalPlaces':0,'rounding':'none'}, grading={'method':'exactDecimal'}, referenceAnswers=['not-a-number'])
        f.pop('choices', None);self.cases[0]['items'][0]['fields'] = [f]
        self.reject()

    def test_rejects_missing_choice_label(self):
        self.cases[0]['items'][0]['fields'][0]['referenceAnswers'] = ['missing-label']
        self.reject()

    def test_rejects_missing_figure_anchor(self):
        self.cases[0]['bodyFigures'] = [{'image':'assets/written/fp2/209901/q01-p01.png', 'anchor':'absent-anchor', 'alt':'fixture', 'caption':'fixture'}]
        self.reject()

    def test_accepts_supported_legal_statuses_without_promoting_content(self):
        for status in ['current', 'outdated']:
            with self.subTest(status=status):
                self.qs[0]['legalReview'] = {'status':status, 'checkedAt':'2026-10-25', 'sourceRefs':['https://www.nta.go.jp/'], 'note':'Synthetic contract fixture; no real legal determination.'}
                self.write();self.run_prepare()
                q = json.loads((self.out/'content/fp2/questions.json').read_text())[0]
                self.assertEqual(q['legalReview'], self.qs[0]['legalReview']);self.assertEqual(q['enrichment'], 'draft')
                shutil.rmtree(self.out)

    def test_recovers_legacy_crop_and_prefers_authored_image(self):
        relative = 'assets/fp2/209901/q01-p01.png'
        self.qs[0]['sourceImages'] = [relative];self.qs[0]['imageSizes'] = [{'width':750,'height':984}];self.write()
        self.run_prepare()
        evidence = json.loads((self.out/'recovery.json').read_text())['recovered'][0]
        with fitz.open(self.cache/'sources/fp2/g2_209901_q.pdf') as pdf:
            expected = pdf[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=fitz.Rect(52,77,552,733),alpha=False).tobytes('png')
        self.assertEqual((self.out/relative).read_bytes(), expected)
        self.assertEqual(evidence['imageSHA256'], hashlib.sha256(expected).hexdigest())
        shutil.rmtree(self.out);target=self.draft/relative;target.parent.mkdir(parents=True);target.write_bytes(expected)
        self.run_prepare();self.assertEqual(json.loads((self.out/'recovery.json').read_text())['recovered'], [])

    def test_rejects_incomplete_draft_and_existing_output(self):
        (self.draft/'questions.json').unlink()
        with self.assertRaises(FileNotFoundError):self.run_prepare()
        self.write();self.out.mkdir();sentinel=self.out/'keep';sentinel.write_text('keep')
        with self.assertRaises(ValueError):self.run_prepare()
        self.assertEqual(sentinel.read_text(), 'keep')

if __name__ == '__main__':
    unittest.main()
