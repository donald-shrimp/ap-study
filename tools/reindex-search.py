"""Update approximate search text from Tesseract TSV; never change canonical images."""
import argparse,csv,json
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--ocr-dir',type=Path,required=True);args=parser.parse_args()
root=Path(__file__).resolve().parents[1];bank=json.loads((root/'data/questions.json').read_text());crops=json.loads((root/'data/source-crops.json').read_text());by_crop={x['id']:x for x in crops};cache={}
for q in bank:
 r=by_crop[q['id']];key=(r['file'],r['page'])
 if key not in cache:
  path=args.ocr_dir/r['file'].removesuffix('.pdf')/f"p{r['page']:02}.tsv"
  # Tesseract text can contain literal quotation marks; TSV has no CSV quoting.
  with path.open() as f:rows=list(csv.DictReader(f,delimiter='\t',quoting=csv.QUOTE_NONE))
  groups={}
  for x in rows:
   if x['text'] and x['text'].strip():groups.setdefault((x['block_num'],x['par_num'],x['line_num']),[]).append(x)
  lines=[]
  for words in groups.values():
   words.sort(key=lambda w:int(w['left']));lines.append((min(int(w['top']) for w in words),''.join(w['text'] for w in words)))
  cache[key]=sorted(lines)
 top,bottom=r['sourceRectangle'][1],r['sourceRectangle'][3];q['searchText']='\n'.join(text for y,text in cache[key] if top-10<=y<bottom)
(root/'data/questions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n')
print(f'Reindexed {len(bank)} questions; canonical questions and answers unchanged')
