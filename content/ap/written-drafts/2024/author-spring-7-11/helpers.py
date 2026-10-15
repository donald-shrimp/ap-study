from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path('.')
OUT=Path('content/ap/written-drafts/2024/author-spring-7-11')
AUTHOR='/root/author_2024_spring_7_11'
evidence=[]
def base(n,title,topic,pages,body):
 cid=f'ap-r06h-pm{n}'
 paths=[f'assets/written/{cid}/question-p{p:02}.png' for p in pages]
 return dict(id=cid,qualificationId='ap',examPartId='written',version=1,topicId=topic,title=title,status='draft',sourceKind='official',body=body,sourceImages=paths,sourceRefs=['https://www.ipa.go.jp/shiken/mondai-kaiotu/2024r06.html']+[s['url'] for s in json.load(open('content/ap/written-drafts/2024/sources/sources.json')) if '2024r06h' in s['path']],items=[],bodyFormat='hitomon-markdown-math-v1',source=f'IPA 令和6年度春期 応用情報技術者試験 午後 問{n}',sourcePages=pages,imageSizes={p:dict(zip(['width','height'],Image.open(p).size)) for p in paths},bodyFigures=[],bodyRefs={},rubricNotice='確認ポイントは学習用に独自作成したものです。IPAの公式配点・部分点基準ではありません。',author=AUTHOR,authoringStatus='awaiting-independent-review')
def field(id,label,answer,explanation,limit=2000,typ='shortText',constraints=None,method=None,rubric=None,choices=None):
 f=dict(id=id,label=label,type=typ,referenceAnswers=answer if isinstance(answer,list) else [answer],grading={'method':method or ('self' if typ=='freeText' else 'exactText')},explanation=explanation,rubric=rubric or [explanation.split('。')[0]+'。'])
 if typ!='singleChoice':
  f['maxLength']=limit
  f['constraints']=constraints or ([] if limit!=2000 else ['原問に字数指定なし。入力上限2000字はアプリ上の制約。'])
 else:
  f['choices']=[dict(id=chr(97+i),label=k,text=v) for i,(k,v) in enumerate(choices)]
  f['selection']={'mode':'exact','count':1}
 return f
def item(c,id,label,prompt,fields,pages,refs=None):
 c['items'].append(dict(id=id,label=label,prompt=prompt,fields=fields,sourcePages=pages,bodyRefs=refs or []))
def crop(c,name,page,box,caption,alt):
 cid=c['id']; src=f'assets/written/{cid}/question-p{page:02}.png';dest=f'assets/written/{cid}/{name}.png'
 Image.open(src).crop(box).save(dest)
 anchor=caption
 c['bodyFigures'].append(dict(id=name,image=dest,caption=caption,sourcePage=page,placement='replace-caption',anchor=anchor,alt=alt))
 c['bodyRefs'][name]={'sourcePages':[page],'anchor':anchor}
 evidence.append(dict(caseId=cid,image=dest,source=src,box=box,sha256=hashlib.sha256(Path(dest).read_bytes()).hexdigest()))
def ref(c,k,pages,text):c['bodyRefs'][k]={'sourcePages':pages,'text':text}
def save(c):
 # assign source-answer page by question range; actual fields traced to original pages in item
 ans=4 if int(c['id'].split('pm')[1])<=8 else 5 if int(c['id'].split('pm')[1])<=10 else 6
 cmnt=2 if ans==4 else 3
 for i in c['items']:
  for f in i['fields']:f['evidence']={'questionPages':i['sourcePages'],'bodyRefs':i['bodyRefs'],'officialAnswerPage':ans,'officialCommentaryPage':cmnt}
 (OUT/(c['id']+'.json')).write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
