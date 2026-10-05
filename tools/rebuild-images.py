"""Rebuild or verify lossless question images against their official PDF crops."""
import argparse
import hashlib
import json
from pathlib import Path
import fitz
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pdf-dir',type=Path,required=True)
parser.add_argument('--verify',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
sources=json.loads((root/'data/sources.json').read_text())
for s in sources:
 if s['kind']=='question':
  data=(args.pdf_dir/s['filename']).read_bytes()
  assert hashlib.sha256(data).hexdigest()==s['sha256'],f"Source changed: {s['filename']}"
records=json.loads((root/'data/source-crops.json').read_text());cache={};documents={}
for r in records:
 key=(r['file'],r['page'])
 if key not in cache:
  if r['file'] not in documents:documents[r['file']]=fitz.open(args.pdf_dir/r['file'])
  pix=documents[r['file']][r['page']-1].get_pixmap(matrix=fitz.Matrix(2.5,2.5),colorspace=fitz.csGRAY)
  cache[key]=Image.frombytes('L',(pix.width,pix.height),pix.samples)
 expected=cache[key].crop(tuple(r['sourceRectangle']));path=root/r['image']
 if args.verify:
  actual=Image.open(path).convert('L');assert actual.size==expected.size and actual.tobytes()==expected.tobytes(),r['id']
 else:path.parent.mkdir(parents=True,exist_ok=True);expected.save(path,lossless=True,method=4)
for d in documents.values():d.close()
print(f"{'Verified' if args.verify else 'Rebuilt'} {len(records)} original question images")
