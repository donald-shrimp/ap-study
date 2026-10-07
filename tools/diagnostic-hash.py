"""Print reviewed-object hashes. This never creates or approves review records."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
args=parser.parse_args()
questions=json.loads(args.source.read_text())
if not isinstance(questions,list):raise ValueError('問題の配列を指定してください。')
for q in questions:
 digest=hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 print(json.dumps({'questionId':q['id'],'version':q.get('version',1),'sha256':digest},ensure_ascii=False))
