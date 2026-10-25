"""Stage existing FP drafts, verified PDFs and legacy crops without rewriting JSON."""
import argparse, hashlib, importlib.util, json, re, shutil, tempfile, urllib.request
from pathlib import Path
import fitz
from material_contracts import require

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.jafp.or.jp/exam/mohan/files/'
PDF = re.compile(r'sources/fp2/([gj]2_[0-9]{6}_[qa]\.pdf)')
CROP = re.compile(r'assets/(written/)?fp2/([0-9]{6})/q[0-9]{2}-p([0-9]{2})\.png')
spec = importlib.util.spec_from_file_location('fp_delivery_check', ROOT/'tools/check-fp2-delivery.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def local_path(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), 'Invalid relative path')
    path = (root/relative).resolve()
    require(path.is_relative_to(root.resolve()), 'Path escapes delivery: '+relative)
    return path

def fetch_pdf(name):
    with urllib.request.urlopen(BASE+name, timeout=90) as response:
        return response.read()

def prepare(draft, output, source_dir=None):
    draft, output = draft.resolve(), output.resolve()
    require(not output.exists(), 'Output already exists; choose a new directory: '+str(output))
    require(not output.is_relative_to(draft), 'Output must be outside the authored draft')
    names = ('questions.json', 'practical-cases.json', 'source-files.json')
    data = {name:json.loads((draft/name).read_text(encoding='utf-8')) for name in names}
    qs, cases, sources = (data[n] for n in names)
    require(isinstance(qs, list) and isinstance(cases, list) and (qs or cases) and isinstance(sources, dict) and sources, 'Incomplete draft arrays/source map')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fp2-prepare-', dir=output.parent) as temp:
        stage = Path(temp)/'delivery'
        base = stage/'content/fp2'
        base.mkdir(parents=True)
        for name in names:
            shutil.copyfile(draft/name, base/name)
        for name in ('question-reviews.json', 'practical-reviews.json'):
            if (draft/name).is_file():
                shutil.copyfile(draft/name, base/name)
            else:
                (base/name).write_text('[]\n')
        for relative, expected in sources.items():
            match = PDF.fullmatch(relative)
            require(match and isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'Invalid source path/SHA: '+relative)
            content = local_path(source_dir, relative).read_bytes() if source_dir else fetch_pdf(match[1])
            require(content.startswith(b'%PDF-') and digest(content)==expected, 'Source SHA mismatch: '+relative)
            target = local_path(stage, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        assets = set()
        for q in qs:
            assets.update(q.get('sourceImages', []))
            assets.update(x for x in [q.get('image'), *(c.get('image') for c in q.get('choices', []))] if x)
        for c in cases:
            assets.update(c.get('sourceImages', []))
            assets.update(f['image'] for f in c.get('bodyFigures', []))
        recovered = []
        for relative in sorted(assets):
            require(relative.startswith(('assets/fp2/', 'assets/written/fp2/')), 'Unsupported asset path: '+relative)
            target = local_path(stage, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            existing = next((local_path(root, relative) for root in [draft, source_dir, ROOT] if root and local_path(root, relative).is_file()), None)
            if existing:
                shutil.copyfile(existing, target)
                continue
            match = CROP.fullmatch(relative)
            require(match, 'Missing asset; provide the authored file: '+relative)
            part, era, page = ('j2' if match[1] else 'g2'), match[2], int(match[3])
            source = f'sources/fp2/{part}_{era}_q.pdf'
            require(source in sources, 'Crop PDF is absent from source map: '+source)
            with fitz.open(stage/source) as pdf:
                require(1 <= page <= len(pdf), 'Invalid crop page: '+relative)
                pg = pdf[page-1]
                clip = [52, 77, pg.rect.width-48, pg.rect.height-67]
                pg.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), clip=fitz.Rect(clip), alpha=False).save(target)
            recovered.append({'image':relative, 'source':source, 'sourceSHA256':sources[source], 'page':page, 'clip':clip, 'scale':1.5, 'imageSHA256':digest(target.read_bytes())})
        result = checker.check(stage)
        (stage/'recovery.json').write_text(json.dumps({'pymupdf':fitz.VersionBind, 'recovered':recovered, 'note':'Legacy page crops only. Original text, figures and educational content require independent review.'}, ensure_ascii=False, indent=2)+'\n')
        stage.rename(output)
    return {**result, 'recoveredImages':len(recovered), 'output':str(output)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('draft', type=Path, help='Directory containing authored questions/practical-cases/source-files JSON')
    parser.add_argument('--output', type=Path, required=True, help='New delivery directory')
    parser.add_argument('--source-dir', type=Path, help='Existing sources/fp2 and assets root; PDF hashes are verified')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.draft, args.output, args.source_dir), ensure_ascii=False))
    except (ValueError, AssertionError, KeyError, TypeError, OSError) as e:
        parser.exit(1, f'Cannot prepare FP2 delivery: {e}\n')
