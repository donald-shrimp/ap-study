from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path('/workspace/ap-study-written-2024'); DEST=ROOT/'content/ap/written-drafts/2024/author-spring-1-6'; AUTHOR='/root/author_2024_spring_1_6'
def digest(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def save(c):
 c['author']=AUTHOR;c['authoringStatus']='awaiting-independent-review';c['status']='draft';c['qualificationId']='ap';c['examPartId']='written';c['version']=1;c['sourceKind']='official';c['bodyFormat']='hitomon-markdown-math-v1';c['rubricNotice']='確認ポイントは学習用に独自作成したものです。IPAの公式配点・部分点基準ではありません。'
 c['sourceImages']=[f"assets/written/{c['id']}/question-p{n:02}.png" for n in c['sourcePages']]
 c['imageSizes']={p:dict(zip(['width','height'],Image.open(ROOT/p).size)) for p in c['sourceImages']}
 c['source']=f"IPA 令和6年度春期 応用情報技術者試験 午後 問{c['id'].split('pm')[-1]}"
 c['sourceRefs']=['https://www.ipa.go.jp/shiken/mondai-kaiotu/2024r06.html']+[f'https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_ap_pm_{k}.pdf' for k in ['qs','ans','cmnt']]
 c.setdefault('bodyFigures',[]);c.setdefault('bodyRefs',{})
 for i in c['items']:
  i.setdefault('bodyRefs',[]);i.setdefault('sourcePages',c['sourcePages'])
  for f in i['fields']:
   if f['type']!='singleChoice':
    f.setdefault('maxLength',2000)
    if f['maxLength']==2000:f.setdefault('constraints',[]).append('原問に字数指定なし。2000字はアプリ入力上限。')
   f.setdefault('evidence',{'questionPages':i['sourcePages'],'officialAnswerPage':1 if int(c['id'][-1])<3 else 2 if int(c['id'][-1])<5 else 3,'officialCommentaryPage':1 if int(c['id'][-1])<5 else 2})
 (DEST/(c['id']+'.json')).write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
 return c

def field(id,label,answer,explanation,rubric,type='shortText',maxLength=None,choices=None,constraints=None,method=None):
 f=dict(id=id,label=label,type=type,referenceAnswers=answer if isinstance(answer,list) else [answer],explanation=explanation,rubric=rubric if isinstance(rubric,list) else [rubric],grading={'method':method or ('self' if type=='freeText' else 'exactText')})
 if maxLength is not None:f['maxLength']=maxLength
 if constraints:f['constraints']=constraints
 if choices is not None:
  f['choices']=[dict(id=chr(97+n),label=label,text=text) for n,(label,text) in enumerate(choices)];f['selection']={'mode':'exact','count':1}
 return f

def item(id,label,prompt,fields,pages=None,refs=None):
 i=dict(id=id,label=label,prompt=prompt,fields=fields)
 if pages:i['sourcePages']=pages
 if refs:i['bodyRefs']=refs
 return i

def crop(case,n,name,box,caption,anchor=None):
 src=f'assets/written/{case}/question-p{n:02}.png';dest=f'assets/written/{case}/{name}.png';Image.open(ROOT/src).crop(box).save(ROOT/dest)
 evidence_path=DEST/'crops.json';e=json.loads(evidence_path.read_text()) if evidence_path.exists() else {};e[dest]={'source':src,'rectangle':list(box),'sha256':digest(dest),'sourceSHA256':digest(src)};evidence_path.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
 return dict(id=name,image=dest,caption=caption,sourcePage=n,placement='replace-caption',anchor=anchor or caption,alt=caption+'。原本の図形・結線・ラベル・注記を保持。')
