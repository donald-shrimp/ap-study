"""Independently reproduce retained PNG pixels and permitted missing-content supplements."""
import json,hashlib,fitz,sys
from pathlib import Path
from PIL import Image
root=Path(sys.argv[1]);a=json.loads((root/'review/correction-provenance.json').read_text());check=[]
for f in a['figures']:
 p=root/f['path'];im=Image.open(p).convert('RGB');assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
 if f['sourceKind']=='existing-png':
  src=root/f['sourcePath'];assert hashlib.sha256(src.read_bytes()).hexdigest()==f['sourceSHA256'];expected=Image.open(src).convert('RGB').crop(f['rectanglePixels'])
 else:
  pdf=root/f['pdfPath'];assert hashlib.sha256(pdf.read_bytes()).hexdigest()==f['pdfSHA256'];d=fitz.open(pdf);pix=d[f['page']-1].get_pixmap(matrix=fitz.Matrix(f['scale'],f['scale']),clip=fitz.Rect(f['rectanglePoints']),alpha=False);expected=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
 assert im.size==expected.size and im.tobytes()==expected.tobytes(),f['path'];check.append({'path':f['path'],'sha256':f['sha256'],'pixelEquality':True})
print(json.dumps({'reviewer':'Codex /root','verifiedFigures':len(check),'figures':check},ensure_ascii=False,indent=2))
