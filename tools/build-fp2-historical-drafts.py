#!/usr/bin/env python3
"""Create unreviewed FP2 academic and practical draft records for historical paper exams."""
import hashlib, json, re, shutil, subprocess, unicodedata
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
ERAS={'202501':('2025年1月26日','2024-10-01'),'202409':('2024年9月8日','2024-04-01'),'202405':('2024年5月26日','2023-10-01')}
TOPICS=['life-planning']*10+['risk-management']*10+['financial-assets']*10+['tax']*10+['real-estate']*10+['inheritance']*10
BASE='https://www.jafp.or.jp/exam/mohan/files/'
N=lambda t:unicodedata.normalize('NFKC',t)
def tidy(s):
    s=s.replace('\f','\n')
    s=re.sub(r'(?m)^\s*－\s*\d+\s*－.*$','',s)
    s=re.sub(r'(?m)^\s*２級\s*(?:学科|実技)試験.*$','',s)
    return '\n'.join(line.rstrip() for line in s.splitlines()).strip()
def topic(n):
    if n in (3,4,5,6):return 'financial-assets'
    if n in (7,8,9,10,35):return 'real-estate'
    if 11<=n<=16:return 'risk-management'
    if 17<=n<=20:return 'tax'
    if 21<=n<=26:return 'inheritance'
    return 'life-planning'
def saveimage(pdf,rel,output,page):
    pg=pdf[page]
    pix=pg.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=fitz.Rect(52,77,pg.rect.width-48,pg.rect.height-67),alpha=False)
    fn=output/rel;fn.parent.mkdir(parents=True,exist_ok=True);pix.save(fn)
    return pix.width,pix.height
def source(era,kind,hashes):
    fq=f'{kind}_{era}_q.pdf';fa=f'{kind}_{era}_a.pdf';label,date=ERAS[era]
    return {'publisher':'日本FP協会','publishedAt':None,'legalAsOf':date,
      'questionUrl':BASE+fq,'questionSha256':hashes['sources/fp2/'+fq],
      'answerUrl':BASE+fa,'answerSha256':hashes['sources/fp2/'+fa],
      'modifiedFromOriginal':True,'modificationNote':'原本問題・模範解答を文字起こしし、画像と解説草稿を追加。別担当の独立レビュー待ち。'}
def legal(era):
    return {'status':'unverified','checkedAt':None,'sourceRefs':[],'note':'原本法令基準日 '+ERAS[era][1]+'。現行法令の照合は未実施。'}
def academic_keys(txt):
    lines=[a.rstrip() for a in N(txt).splitlines() if a.strip()];out={}
    for i,line in enumerate(lines[:-1]):
        qs=re.findall(r'問\s*(\d+)',line)
        if len(qs)==10:
            ans=re.findall(r'(?<!\d)\d(?!\d)',lines[i+1])
            if len(ans)==10:out.update({int(q):int(a) for q,a in zip(qs,ans)})
    assert len(out)==60 and sorted(out)==list(range(1,61)),('academic answer mismatch',out)
    return out
def practical_keys(txt):
    out={};last=None
    for line in N(txt).splitlines():
        mt=list(re.finditer(r'問\s*(\d{1,2})\b',line))
        if mt:
            for i,m in enumerate(mt):
                number=int(m.group(1));out[number]=line[m.end():mt[i+1].start() if i+1<len(mt) else len(line)].strip()
                if number<=20:last=number
        elif last is not None and re.match(r'^\s*\([アイウエ]\)',line):
            out[last]+=' '+line.strip()
    assert len(out)==40 and sorted(out)==list(range(1,41)),('practical answer mismatch',out)
    return out
def collect(root,era):
    origin=root/'sources/fp2';origin.mkdir(parents=True,exist_ok=True)
    hashes={}
    for part in ['g2','j2']:
        for suffix in ['q','a']:
            fn=f'{part}_{era}_{suffix}.pdf'
            url=BASE+fn
            data=subprocess.check_output(['curl','--fail','--location','--silent','--show-error','--retry','3','--max-time','90',url])
            if not data.startswith(b'%PDF-'):raise ValueError(fn+' is not PDF')
            path=origin/fn;path.write_bytes(data)
            hashes['sources/fp2/'+fn]=hashlib.sha256(data).hexdigest()
    return hashes
def reasons(options,key,stem):
    unfavorable=any(w in stem for w in ('不適切','誤っている','適当でない'))
    target='不適切' if unfavorable else '適切'
    out=[]
    for i,opt in enumerate(options,1):
        phrase=re.sub(r'\s+','',opt)[:72]
        if i==key:out.append(f'公式解答はこの肢。記述「{phrase}」が設問の求める{target}な肢と判断される。法令・計算根拠は独立レビューで検証する。')
        else:out.append(f'この肢の記述「{phrase}」は公式正答ではない。出題時の制度・例外を含む{target}性の根拠はレビューで検証する。')
    return out
def create(era,output):
    label,legal_day=ERAS[era]
    base=output/'content/fp2';base.mkdir(parents=True,exist_ok=True)
    hashes=collect(output,era)
    (base/'source-files.json').write_text(json.dumps(hashes,indent=2)+'\n')
    docs={key:fitz.open(output/'sources/fp2'/f'{key}_{era}_q.pdf') for key in ['g2','j2']}
    def layout(part,suff):
        return subprocess.check_output(['pdftotext','-layout',str(output/'sources/fp2'/f'{part}_{era}_{suff}.pdf'),'-'],text=True)
    g=layout('g2','q');gm=list(re.finditer(r'(?m)^\s*問題\s*([０-９0-9]{1,2})\s*$',g))
    ga=academic_keys(layout('g2','a'))
    assert len(gm)==60 and [int(N(m.group(1))) for m in gm]==list(range(1,61))
    questions=[]
    for i,m in enumerate(gm):
        n=i+1;end=gm[i+1].start() if i<59 else len(g)
        b=g[m.end():end]
        choices=list(re.finditer(r'(?m)^\s*([１２３４1-4])．\s*',b))
        assert len(choices)==4,(era,n,'academic choices',len(choices))
        stem=tidy(b[:choices[0].start()])
        opts=[' '.join(v.strip() for v in tidy(b[a.end():choices[j+1].start() if j<3 else len(b)]).splitlines() if v.strip()) for j,a in enumerate(choices)]
        source_images=[];sizes=[]
        has_fig=any(t in stem for t in ['下記の表','下表','次の表','以下の表','資料に基づ','資料をもと']) or any(len(v)<12 for v in opts)
        if has_fig:
            startpg=g[:m.start()].count('\f');endpg=g[:end].count('\f')
            for pg in range(startpg,min(endpg+1,len(docs['g2']))):
                rel=f'assets/fp2/{era}/q{n:02}-p{pg+1:02}.png'
                w,h=saveimage(docs['g2'],rel,output,pg);source_images.append(rel);sizes.append({'width':w,'height':h})
            stem+='\n\n表・図は添付した原本画像を参照する。'
        key=ga[n];rs=reasons(opts,key,stem)
        questions.append({'id':f'fp2-{era}-objective-q{n:02}','version':1,'type':'singleChoice','qualificationId':'fp2',
          'examPartId':'objective','topicId':TOPICS[n-1],'packId':era,'packLabel':label+'実施・2級学科',
          'number':n,'title':label+f' 学科 問{n}','stem':stem,
          'choices':[{'id':f'option-{j}','label':str(j),'text':v} for j,v in enumerate(opts,1)],
          'correctChoiceId':f'option-{key}','grading':{'method':'exactChoiceSet'},
          'explanation':f'公式正答は{key}。'+rs[key-1],
          'choiceReasons':rs,'enrichment':'draft','uses':['practice'],'sourceKind':'official',
          'source':'日本FP協会 2級学科試験 '+label+'実施。文字起こし・解説草稿。',
          'questionUrl':BASE+f'g2_{era}_q.pdf','answerUrl':BASE+f'g2_{era}_a.pdf',
          'sourceImages':source_images,'imageSizes':sizes,'sourceRecord':source(era,'g2',hashes),'legalReview':legal(era)})
    (base/'questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    s=layout('j2','q');jm=list(re.finditer(r'(?m)^\s*問\s*([０-９0-9]{1,2})\s*$',s))
    ja=practical_keys(layout('j2','a'))
    assert len(jm)==40 and [int(N(m.group(1))) for m in jm]==list(range(1,41))
    cases=[]
    for i,m in enumerate(jm):
        n=i+1;end=jm[i+1].start() if i<39 else len(s)
        body=tidy(s[m.end():end]);ans=ja[n]
        found=list(re.finditer(r'\(([アイウエ])\)\s*([^\(]*?)(?:\(([^\)]+)\))?(?=\s*\([アイウエ]\)|$)',ans))
        pairs=[(t.group(1),t.group(2).strip(),t.group(3)) for t in found] if found else []
        if not pairs:
            v=re.match(r'\s*(.+?)(?:\((.+?)\))?\s*$',ans)
            assert v,(era,n,ans);pairs=[('回答',v.group(1),v.group(2))]
        fields=[]
        for letter,v,unit in pairs:
            value=N(v.strip()).replace(' ','')
            unit=N(unit or '').replace('m2','㎡').replace('%','％')
            lab='回答' if letter=='回答' else '（'+letter+'）'
            fid='answer' if letter=='回答' else 'field-'+{'ア':'a','イ':'i','ウ':'u','エ':'e'}[letter]
            if value in ('○','×'):
                f={'id':fid,'label':lab,'type':'singleChoice','grading':{'method':'exactText'},'referenceAnswers':[value],
                 'choices':[{'id':'yes','label':'○','text':'適切'},{'id':'no','label':'×','text':'不適切'}],
                 'explanation':f'{lab}の公式正誤は{value}。記述の適用要件や例外は独立レビューで確認する。',
                 'rubric':['記述の全条件と公式解答を比較する。']}
            elif unit:
                number=value.replace(',','');assert re.fullmatch(r'-?\d+(?:\.\d+)?',number),(era,n,value)
                dp=len(number.split('.')[1]) if '.' in number else 0
                rounding='floor' if re.search(r'切り捨て|切捨て',body) else ('halfUp' if '四捨五入' in body else 'none')
                f={'id':fid,'label':lab,'type':'numeric','maxLength':100,'numeric':{'unit':unit,'decimalPlaces':dp,'rounding':rounding},
                  'grading':{'method':'exactDecimal'},'referenceAnswers':[number],
                  'explanation':f'公式正答は{number}{unit}。資料中の数値と原本の端数処理・単位を用いて計算する。式の精査は独立レビューで行う。',
                  'rubric':['出題時の制度・資料・端数処理を再計算して照合する。']}
            else:
                assert value.isdigit() and 1<=int(value)<=20,(era,n,value)
                matches=list(re.finditer(r'(?m)^\s*([１２３４５６７８９1-9])\s*[．.]\s*',body))
                opts={}
                for t,a in enumerate(matches):
                    z=int(N(a.group(1)))
                    if z not in opts:opts[z]=tidy(body[a.end():matches[t+1].start() if t+1<len(matches) else len(body)]).replace('\n',' ')[:2000]
                count=max(4,int(value),*(opts.keys() or [0]))
                f={'id':fid,'label':lab,'type':'singleChoice','grading':{'method':'exactText'},'referenceAnswers':[value],
                  'choices':[{'id':f'option-{k}','label':str(k),'text':opts.get(k) or f'原本の選択肢・語群{k}（本文参照）'} for k in range(1,count+1)],
                  'explanation':f'{lab}の公式解答番号は{value}。原本の同番号の語群・選択肢を参照。根拠は別担当の確認対象。',
                  'rubric':['選択肢・語群の番号と公式模範解答を照合する。']}
            fields.append(f)
        figures=[]
        if any(t in body for t in ('資料','下記','図','貸借対照表','路線価','キャッシュフロー','保険証券')):
            startpg=s[:m.start()].count('\f');endpg=s[:end].count('\f')
            for pg in range(startpg,min(endpg+1,len(docs['j2']))):
                rel=f'assets/written/fp2/{era}/q{n:02}-p{pg+1:02}.png'
                saveimage(docs['j2'],rel,output,pg)
                anchor=f'【原本図表 問{n} {pg+1}頁】';body+='\n\n'+anchor
                figures.append({'image':rel,'anchor':anchor,'alt':f'{label} 2級実技問{n}の原本画像','caption':f'公式原本PDF {pg+1}頁（機械トリミング）'})
        cases.append({'id':f'fp2-{era}-jafp-q{n:02}','qualificationId':'fp2','examPartId':'jafp-practical',
          'topicId':topic(n),'version':1,'status':'draft','title':label+f' 実技 問{n}',
          'source':'日本FP協会2級実技（資産設計提案業務） '+label+'実施。原本文字起こし・回答欄分割・解説草稿。',
          'body':body,'sourceImages':[],'bodyFigures':figures,
          'items':[{'id':'item1','label':f'問{n}','prompt':'公式問題の条件に従い、各回答欄を埋める。','fields':fields}],
          'sourceRecord':source(era,'j2',hashes),'legalReview':legal(era)})
    (base/'practical-cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for f in ['question-reviews','practical-reviews']:(base/(f+'.json')).write_text('[]\n')
    (output/'README.md').write_text(f'# FP2 {label}実施 学科・実技100問 Draft\n\n原本法令基準日：{legal_day}。学科60問・実技40問。独立レビュー・現行法令照合・公開は未実施。\n\n本文は公式PDFをテキスト抽出。図表は機械トリミングのため個別確認が必要。解説・選択肢別理由は公式正答に基づく未完成の草稿であり、具体的法令の根拠を含む詳細な学習解説としては未検証。公開せず別エージェントへ渡す。\n\n公式出典・加工を明記して利用条件 https://www.jafp.or.jp/exam/mohan/files/exam_riyou.pdf を確認する。\n')
    subprocess.run(['python','tools/check-fp2-delivery.py',str(output)],check=True,cwd=ROOT)
    print(era,'academic',len(questions),'practical',len(cases),'fields',sum(len(v['fields']) for c in cases for v in c['items']),flush=True)
if __name__=='__main__':
    for era in ERAS:
        dest=ROOT/'deliveries'/f'fp2-jafp-{era}-draft'
        create(era,dest)
