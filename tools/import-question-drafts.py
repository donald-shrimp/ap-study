#!/usr/bin/env python3
"""Static HTML intake. Never executes scripts or marks supplied answers reviewed."""
import argparse,hashlib,json,re,tempfile,os
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ident(value):return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}',value))
class Node:
    def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.children=[];self.parent=parent
    def find(self,test):
        found=[]
        for child in self.children:
            if isinstance(child,Node):
                if test(child):found.append(child)
                found.extend(child.find(test))
        return found
    def has(self,cls):return cls in self.attrs.get('class','').split()
    def text(self):
        if self.tag in ['script','style'] or self.has('importance-note'):return ''
        if self.tag=='br':return '\n'
        result=''.join(c.text() if isinstance(c,Node) else c for c in self.children)
        return result+('\n' if self.tag in ['p','li','div'] else '')
class Parser(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.current=self.root
    def handle_starttag(self,tag,attrs):
        node=Node(tag,attrs,self.current);self.current.children.append(node)
        if tag not in ['br','input','img','meta','link','hr','wbr','source','area','base','embed']:self.current=node
    def handle_endtag(self,tag):
        node=self.current
        while node.parent:
            if node.tag==tag:self.current=node.parent;return
            node=node.parent
    def handle_data(self,data):self.current.children.append(data)
def text(node):return '\n'.join(re.sub(r'[ \t\r]+',' ',s).strip() for s in node.text().split('\n') if s.strip())
def one(nodes):return nodes[0] if nodes else Node()
def compact(s):return re.sub(r'\s+','',s)
def extract(raw,qualification,collection,filename):
    parser=Parser();parser.feed(raw);articles=parser.root.find(lambda n:n.tag=='article' and n.has('question'))
    if not articles:raise ValueError(f'{filename}: article.question が見つかりません。未対応のHTML形式です。')
    records=[]
    for number,article in enumerate(articles,1):
        changes=[];issues=[]
        stem=text(one(article.find(lambda n:n.has('stem'))))
        head=one(article.find(lambda n:n.has('qhead')))
        code=text(one(head.find(lambda n:n.tag=='small'))) or article.attrs.get('data-question-id')
        if not code:code=Path(filename).stem+'-'+(article.attrs.get('id') or str(number));issues.append('問題コードがないためファイル名を識別に使用。改名時は重複候補を確認する。')
        labels=article.find(lambda n:n.tag=='label' and n.has('choice'))
        choices=[text(one(n.find(lambda c:c.tag=='span'))) or text(n) for n in labels]
        inputs=[one(n.find(lambda c:c.tag=='input')).attrs.get('type','') for n in labels]
        explicit=article.attrs.get('data-type')
        kind=explicit or ('multipleChoice' if inputs and all(t=='checkbox' for t in inputs) else 'singleChoice' if inputs and all(t=='radio' for t in inputs) else None)
        answer_node=one(article.find(lambda n:n.tag=='details' and n.has('answer')))
        answer_ps=answer_node.find(lambda n:n.tag=='p');reference=text(one(answer_ps)).removeprefix('正答：').removeprefix('正解：')
        answer_raw=article.attrs.get('data-correct','')
        try:answers=[int(v.strip()) for v in answer_raw.split(',') if v.strip()]
        except ValueError:answers=[];issues.append('data-correct が整数の選択肢位置ではない。')
        manual=one(article.find(lambda n:n.has('manual')))
        if not choices and manual.children:
            choices=[text(li) for li in one(manual.find(lambda n:n.tag=='ol')).find(lambda n:n.tag=='li')]
            matches=[i for i,c in enumerate(choices) if compact(c)==compact(reference)]
            if len(choices)>=2 and len(matches)==1 and not explicit:
                answers=matches;kind='singleChoice';changes.append('手動表示の選択肢と提供正答の文字照合で単一選択へ復元。内容の正しさは未確認。')
        removed=[]
        for i,c in enumerate(choices):
            if re.match(r'正解はそれぞれ|正しい回答はそれぞれ|同僚とそのページで共同作業を開始する方法.*[2２]つ選',c):removed.append(i);stem+='\n'+c
        if removed:
            if any(i in removed for i in answers):issues.append('注意書きとして除外する行が提供正答に含まれる。')
            answers=[i-sum(j<i for j in removed) for i in answers if i not in removed];choices=[c for i,c in enumerate(choices) if i not in removed];changes.append('選択肢へ混入した設問の注意書きを本文へ移動し正答位置を再計算。')
        q={'id':collection+'-'+hashlib.sha256(code.encode()).hexdigest()[:20],'version':1,'qualificationId':qualification,'type':kind or 'unknown','stem':stem,'sourceKind':'authored'}
        if not stem:issues.append('本文を抽出できない。')
        if article.find(lambda n:n.tag in ['img','table','math','svg']):issues.append('図・表・数式が含まれる。画像と全セルを確認し、公開用形式へ手動で変換する。')
        if kind=='freeText':
            q['grading']={'method':'deferred'};q['referenceAnswer']=reference
            if not reference:issues.append('記述式の参考解答がない。')
            if choices:issues.append('記述式と選択肢が混在している。')
        else:
            q['choices']=[{'id':'choice-'+str(i),'label':('アイウエオカキクケコ'[i] if i<10 else str(i+1)),'text':c} for i,c in enumerate(choices)]
            if not 2<=len(choices)<=20 or any(not c for c in choices):issues.append('選択肢数または空の選択肢を確認する。')
            if not answers or len(set(answers))!=len(answers) or any(i<0 or i>=len(choices) for i in answers):issues.append('提供正答の位置を確認する。')
            valid=[i for i in range(len(choices)) if i in answers]
            q['grading']={'method':'exactChoiceSet'}
            if kind=='singleChoice':
                if len(valid)!=1:issues.append('単一選択なのに提供正答が1個でない。')
                if len(valid)==1:q['correctChoiceId']='choice-'+str(valid[0])
            elif kind=='multipleChoice':
                q['correctChoiceIds']=['choice-'+str(i) for i in valid]
                counts=re.findall(r'(?:([0-9０-９]+)\s*つ|([0-9０-９]+)\s*個)\s*選',stem)
                numbers=[int(a or b) for a,b in counts]
                q['selection']={'mode':'exact','count':numbers[-1]} if numbers else {'mode':'all'}
                if numbers and numbers[-1]!=len(valid):issues.append('指定された選択数と提供正答の個数が不一致。')
            else:issues.append('未対応の問題形式。形式を推測して公開しない。')
        q['explanation']='\n\n'.join(text(p) for p in answer_ps[1:])
        refs=[n.attrs.get('href','') for n in answer_node.find(lambda n:n.tag=='a')]
        if any(not re.match(r'^https?://[^\s<>]+$',url) for url in refs):issues.append('不正な参照URLを確認する。')
        # Order-independent exact duplicates are candidates, not automatic deletions.
        fingerprint=digest({'stem':compact(re.sub(r'正解はそれぞれ[^。]*。|正しい回答はそれぞれ[^。]*。','',stem)),'choices':sorted(compact(c) for c in choices)})
        records.append({'sourceCode':code,'sourceOrdinal':number,'question':q,'providedSourceRefs':refs,'formatChanges':changes,'issues':issues,'fingerprint':fingerprint,'status':'unreviewed','contentReviewComplete':False,'publishedToApp':False})
    if len({r['question']['id'] for r in records})!=len(records):raise ValueError(f'{filename}: 同じ問題コードが複数あります。出典を修正してください。')
    return records

def import_files(paths,output,qualification,collection):
    if not ident(qualification) or not ident(collection) or len(collection)>70:raise ValueError('資格IDとcollectionは安定した英数字IDを指定（collectionは70文字以下）。')
    if len({p.resolve() for p in paths})!=len(paths):raise ValueError('同じファイルを複数指定しています。')
    manifest_path=output/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'format':'hitomon-question-intake','version':1,'qualificationId':qualification,'collection':collection,'sources':{},'questions':{}}
    if manifest.get('format')!='hitomon-question-intake' or manifest['qualificationId']!=qualification or manifest['collection']!=collection:raise ValueError('取り込み先の資格またはcollectionが一致しません。')
    changes={'newQuestions':0,'newRevisions':0,'skippedSources':0};staged={}
    for path in paths:
        data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
        if sha in manifest['sources']:changes['skippedSources']+=1;continue
        records=extract(data.decode('utf-8-sig'),qualification,collection,path.name)
        manifest['sources'][sha]={'filename':path.name,'sha256':sha,'archive':'sources/'+sha+'.html.txt','questionCount':len(records)};staged['sources/'+sha+'.html.txt']=data
        for record in records:
            qid=record['question']['id'];record['sourceSha256']=sha;record['sourceFile']=path.name
            revision_hash=digest({k:record[k] for k in ['question','providedSourceRefs','formatChanges','issues']})
            row=manifest['questions'].setdefault(qid,{'sourceCode':record['sourceCode'],'revisions':[]})
            if any(rev['sha256']==revision_hash for rev in row['revisions']):continue
            if row['revisions']:changes['newRevisions']+=1
            else:changes['newQuestions']+=1
            relative=f'drafts/{qid}/{revision_hash}.json';record['revisionSha256']=revision_hash
            row['revisions'].append({'sha256':revision_hash,'path':relative,'fingerprint':record['fingerprint'],'type':record['question']['type'],'issues':record['issues']});staged[relative]=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
    groups={}
    for qid,row in manifest['questions'].items():
        for rev in row['revisions']:groups.setdefault(rev['fingerprint'],set()).add(qid)
    manifest['duplicateCandidates']=[sorted(ids) for ids in groups.values() if len(ids)>1]
    manifest['revisionConflicts']=[qid for qid,row in manifest['questions'].items() if len(row['revisions'])>1]
    manifest['counts']={'questions':len(manifest['questions']),'singleChoice':0,'multipleChoice':0,'freeText':0,'unknown':0,'unreviewed':len(manifest['questions']),'publishedToApp':0}
    for row in manifest['questions'].values():manifest['counts'][row['revisions'][0]['type'] if row['revisions'][0]['type'] in ['singleChoice','multipleChoice','freeText'] else 'unknown']+=1
    if staged:
        # Manifest commits last; interrupted staging is harmless and retryable.
        output.mkdir(parents=True,exist_ok=True)
        for relative,data in staged.items():
            target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
            fd,temp=tempfile.mkstemp(dir=target.parent)
            try:
                with os.fdopen(fd,'wb') as stream:stream.write(data)
                os.replace(temp,target)
            finally:
                if os.path.exists(temp):os.unlink(temp)
        manifest['importedAt']=datetime.now(timezone.utc).isoformat()
        fd,temp=tempfile.mkstemp(dir=output)
        with os.fdopen(fd,'w') as stream:stream.write(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        os.replace(temp,manifest_path)
    return {**changes,'counts':manifest['counts'],'duplicateCandidates':manifest['duplicateCandidates'],'revisionConflicts':manifest['revisionConflicts']}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('files',type=Path,nargs='+');cli.add_argument('--qualification',required=True);cli.add_argument('--collection',required=True);cli.add_argument('--output',type=Path,required=True);args=cli.parse_args()
    try:print(json.dumps(import_files(args.files,args.output,args.qualification,args.collection),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error:cli.exit(1,str(error)+'\n')
