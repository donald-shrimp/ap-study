"""Contracts shared by publication checks and the external FP authoring handoff."""
import hashlib,re
from datetime import date

def require(ok,message):
    if not ok:raise ValueError(message)

def decimal_value(value):
    if not isinstance(value,str) or len(value)>100:return None
    text=value.translate(str.maketrans('０１２３４５６７８９＋－．，','0123456789+-.,')).strip()
    if not re.fullmatch(r'[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?',text):return None
    plain=text.replace(',','');negative=plain.startswith('-');parts=plain.lstrip('+-').split('.')
    whole=parts[0].lstrip('0') or '0';fraction=parts[1].rstrip('0') if len(parts)>1 else ''
    return ('-' if negative and (whole!='0' or fraction) else '')+whole+('.'+fraction if fraction else '')

def validate_numeric(field):
    n=field.get('numeric',{});refs=field.get('referenceAnswers',[])
    require(field['type']=='numeric' and field.get('grading')=={'method':'exactDecimal'} and isinstance(n,dict) and set(n)=={'unit','decimalPlaces','rounding'},'Invalid numeric contract')
    require(isinstance(n['unit'],str) and 0<len(n['unit'])<=30 and type(n['decimalPlaces']) is int and 0<=n['decimalPlaces']<=12 and n['rounding'] in ['none','halfUp','floor','ceil','truncate'],'Invalid numeric unit/precision/rounding')
    require(type(field.get('maxLength')) is int and 1<=field['maxLength']<=100 and isinstance(refs,list) and refs,'Invalid numeric answer length')
    for v in refs:
        require(isinstance(v,str) and len(v)<=field['maxLength'] and re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?',v) and decimal_value(v) is not None and (len(v.split('.')[1]) if '.' in v else 0)<=n['decimalPlaces'],'Invalid decimal reference answer')

def valid_date(v):
    if not isinstance(v,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',v):return False
    try:return date.fromisoformat(v).isoformat()==v
    except ValueError:return False

def validate_legal(material,required=False):
    s=material.get('sourceRecord');r=material.get('legalReview')
    if s is None and r is None and 'sourceRecord' not in material and 'legalReview' not in material:
        require(not required,'Missing legal context');return
    url=lambda v:isinstance(v,str) and len(v)<=2000 and re.fullmatch(r'https?://[^\s]+',v)
    digest=lambda v:isinstance(v,str) and re.fullmatch(r'[a-f0-9]{64}',v)
    require(isinstance(s,dict) and set(s)=={'publisher','publishedAt','legalAsOf','questionUrl','questionSha256','answerUrl','answerSha256','modifiedFromOriginal','modificationNote'},'Invalid source record fields')
    require(isinstance(s['publisher'],str) and s['publisher'].strip() and len(s['publisher'])<=200 and (s['publishedAt'] is None or valid_date(s['publishedAt'])) and (s['legalAsOf'] is None or valid_date(s['legalAsOf'])),'Invalid source date/publisher')
    require(url(s['questionUrl']) and url(s['answerUrl']) and digest(s['questionSha256']) and digest(s['answerSha256']) and type(s['modifiedFromOriginal']) is bool and isinstance(s['modificationNote'],str) and len(s['modificationNote'])<=2000 and (not s['modifiedFromOriginal'] or s['modificationNote'].strip()),'Invalid source hashes/modification')
    require(isinstance(r,dict) and set(r)=={'status','checkedAt','sourceRefs','note'} and r['status'] in ['unverified','current','outdated'] and isinstance(r['sourceRefs'],list) and len(r['sourceRefs'])<=20 and all(url(v) for v in r['sourceRefs']) and len(set(r['sourceRefs']))==len(r['sourceRefs']) and isinstance(r['note'],str) and len(r['note'])<=4000,'Invalid legal review')
    require(r['checkedAt'] is None if r['status']=='unverified' else valid_date(r['checkedAt']) and r['sourceRefs'] and r['note'].strip() and (r['status']=='outdated' or s['legalAsOf'] is not None),'Legal review needs a date and evidence')

def validate_source_hashes(root,material,review):
    if not material.get('sourceRecord'):return
    hashes=review.get('sourceHashes',{})
    require(isinstance(hashes,dict) and hashes,'Source PDF hashes missing')
    for path,digest in hashes.items():
        file=(root/path).resolve()
        require(file.is_relative_to(root.resolve()) and file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==digest,'Source file changed: '+path)
    s=material['sourceRecord']
    require(s['questionSha256'] in hashes.values() and s['answerSha256'] in hashes.values(),'Source record SHA differs from reviewed PDFs')

def validate_case_figures(material):
    body=material['body'];cursor=0
    for figure in material['bodyFigures']:
        anchor=figure.get('anchor')
        require(isinstance(anchor,str) and anchor.strip() and len(anchor)<=500,'Invalid figure anchor')
        position=body.find(anchor,cursor)
        require(position>=0 and body.find(anchor)==body.rfind(anchor),'Missing, ambiguous or out-of-order figure anchor: '+anchor)
        cursor=position+len(anchor)
