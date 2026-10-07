"""Show only question and choice text, before consulting author explanations."""
import argparse,json
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
args=parser.parse_args()
batch=json.loads(args.source.read_text())
for q in batch['questions']:
 print(json.dumps({'id':q['id'],'topicId':q['topicId'],'parentQuestionId':q['parentQuestionId'],'stem':q['stem'],'choices':q['choices']},ensure_ascii=False))
