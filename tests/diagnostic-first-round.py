"""Recheck the published first batch and its evidence, without approving records."""
import hashlib
import itertools
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: json.loads((ROOT / p).read_text())
digest = lambda q: hashlib.sha256(json.dumps(q, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
questions = read('content/ap/diagnostic-questions.json')
reviews = {r['questionId']: r for r in read('content/ap/diagnostic-reviews.json')}
solutions = read('content/ap/diagnostic-drafts/20261008-first-round-review-solutions.json')
by_id = {q['id']: q for q in questions}
first = {s['topicId']: by_id['ap-diagnostic-' + s['topicId'] + '-001'] for s in solutions['solutions']}
assert len(first) == len({q['parentQuestionId'] for q in first.values()}) == 17
assert set(first) == {t['id'] for t in read('content/ap/qualification.json')['topics']}
for s in solutions['solutions']:
    q = first[s['topicId']]; r = reviews[q['id']]
    if r['method'].get('revisionRecord'):
        journal = read(r['method']['revisionRecord'])
        edit = next(item for item in journal['items'] if item['questionId'] == q['id'])
        initial = edit['beforeReview']
        assert initial['sha256'] == digest(edit['beforeQuestion'])
        assert edit['beforeQuestion']['choices'][s['choiceIndex']]['id'] == edit['beforeQuestion']['correctChoiceId']
        assert edit['afterVersion'] == q['version'] and edit['afterSha256'] == digest(q)
        assert q['correctChoiceId'] == edit['solution']['correctChoiceId']
        assert journal['sameEditorAndReviewer'] and not journal['independentReview']
        assert edit['revisionAuthor'] == edit['revisionReviewer'] == r['editor'] == r['reviewer']
        assert not r['method']['independentRevisionReview']
    else:
        initial = r
        assert q['choices'][s['choiceIndex']]['id'] == q['correctChoiceId']
    assert r['sha256'] == digest(q) and r['version'] == q['version']
    assert r['author'] == initial['author'] == solutions['previousAuthorRun'] and initial['reviewer'] == solutions['reviewRun']
    assert r['method']['separateExecution'] and not r['method']['separateAgent'] and not r['method']['blindContext']
    assert all(r['checks'].values()) and len(q['choiceReasons']) == 4 and q['hints'] == []
    for image in r['sourceEvidence']['sourceImages']:
        assert hashlib.sha256((ROOT / image['path']).read_bytes()).hexdigest() == image['sha256']
    for image in r.get('derivedImages', []):
        assert hashlib.sha256((ROOT / image['path']).read_bytes()).hexdigest() == image['sha256']

def unique(topic, valid):
    q = first[topic]
    ids = [c['id'] for c in q['choices'] if valid(c['text'])]
    assert ids == [q['correctChoiceId']], (topic, ids)

# Evaluate the actual displayed Boolean expressions, including whole-expression negation.
def boolean(text, values):
    tokens=re.findall(r'[PQR¬∧∨→()]', text); pos=0
    assert ''.join(tokens)==text.replace(' ','')
    def atom():
        nonlocal pos
        token=tokens[pos];pos+=1
        if token=='¬': return not atom()
        if token=='(':
            value=expr();assert tokens[pos]==')';pos+=1;return value
        return values[token]
    def chain(next_level, op, combine):
        nonlocal pos
        value=next_level()
        while pos<len(tokens) and tokens[pos]==op:
            pos+=1;right=next_level();value=combine(value,right)
        return value
    def conjunction(): return chain(atom,'∧',lambda a,b:a and b)
    def disjunction(): return chain(conjunction,'∨',lambda a,b:a or b)
    def expr():
        nonlocal pos
        left=disjunction()
        if pos<len(tokens) and tokens[pos]=='→':
            pos+=1;right=expr();return (not left) or right
        return left
    value=expr();assert pos==len(tokens);return value
unique('theory',lambda text:all(boolean(text,{'P':False,'Q':True,'R':r}) for r in [False,True]))
assert 'Pが偽、Qが真' in first['theory']['stem']

def svg_data(path):
    root=ET.parse(ROOT/path).getroot()
    return root,json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
chart,signal=svg_data(first['logic']['image'])
assert set(zip(signal['A'],signal['B']))==set(itertools.product((0,1),repeat=2))
# Check that the rendered wave paths implement the data, rather than trusting metadata.
wave_paths=[p.attrib['d'] for p in chart.findall('.//{http://www.w3.org/2000/svg}path') if p.attrib['d'].startswith('M92 ')]
for row,values in enumerate([signal['A'],signal['B'],signal['Y']]):
    high=32+row*100;low=high+46;expected=f'M92 {high if values[0] else low}'
    for i,v in enumerate(values):
        expected+=f'H{92+(i+1)*60}'
        if i+1<len(values):expected+=f'V{high if values[i+1] else low}'
    assert wave_paths[row]==expected
gates={'XOR':lambda a,b:a!=b,'XNOR':lambda a,b:a==b,'NAND':lambda a,b:not(a and b),'NOR':lambda a,b:not(a or b)}
matches=[]
for c in first['logic']['choices']:
    circuit,data=svg_data(c['image']);gate=data['gate']
    # Inversion bubble and XOR extra curve must agree with the actual circuit symbol.
    assert len(circuit.findall('.//{http://www.w3.org/2000/svg}circle'))==int(gate!='XOR')
    extra=any(p.attrib['d']=='M53 18Q69 48 53 78' for p in circuit.findall('.//{http://www.w3.org/2000/svg}path'))
    assert extra==(gate in ['XOR','XNOR'])
    if [int(gates[gate](a,b)) for a,b in zip(signal['A'],signal['B'])]==signal['Y']:matches.append(c['id'])
assert matches==[first['logic']['correctChoiceId']]

# Interpret each recursion choice; test base value, termination and the requested sum.
def recursive_sum(text,n):
    match=re.fullmatch(r'if n=0 then return ([01]) else return n\+sum\(n([−+])1\)',text)
    assert match
    base=int(match[1]);step=-1 if match[2]=='−' else 1
    def call(x,depth=0):
        if depth>100:raise RecursionError('not converging')
        return base if x==0 else x+call(x+step,depth+1)
    return call(n)
def valid_recursion(text):
    try:return all(recursive_sum(text,n)==sum(range(n+1)) for n in range(12))
    except RecursionError:return False
unique('algorithm',valid_recursion)

_,cpu=svg_data(first['architecture']['image'])
periods=[Fraction(row[1].removesuffix('ナノ秒')) for row in cpu['rows']]
cpis=[Fraction(row[2]) for row in cpu['rows']]
unique('architecture',lambda text:Fraction(text)==periods[0]*cpis[0]/(periods[1]*cpis[1]))
dac=first['hardware']['stem']
step=int(re.search(r'出力が(\d+)ミリV変化',dac)[1])
code=re.search(r'16進数で([0-9A-F]+)',dac)[1]
assert 'データに0を与えたときの出力は0ミリV' in dac and int(code,16)<256
unique('hardware',lambda text:int(text.replace(',',''))==int(code,16)*step)
network = first['network']['stem']
mtu = int(re.search(r'が([\d,]+)バイトに設定', network)[1].replace(',', ''))
total = int(re.search(r'で、([\d,]+)バイトのデータ', network)[1].replace(',', ''))
tcp = int(re.search(r'TCPヘッダー長は(\d+)', network)[1])
ip = int(re.search(r'IPヘッダー長は(\d+)', network)[1])
assert (mtu,total,tcp,ip) == (1280,2400,32,20)
packets = [mtu-ip-tcp, total-(mtu-ip-tcp)]
assert sum(packets) == 2400 and all(n+52 <= 1280 for n in packets)
unique('network', lambda text: int(text.replace(',', '')) == packets[1])
# Execute a harmless local SQL example, using the request value extracted from the stem.
request = next(line for line in first['security']['stem'].splitlines() if line.startswith('GET '))
value = parse_qs(urlparse(request.split()[1]).query)['user'][0]
db = sqlite3.connect(':memory:')
db.executescript("CREATE TABLE users(name TEXT);INSERT INTO users VALUES ('admin'),('reader');")
assert db.execute("SELECT name FROM users WHERE name='"+value+"'").fetchall() == [('admin',),('reader',)]
assert db.execute('SELECT name FROM users WHERE name=?',(value,)).fetchall() == []
db.close()
unique('security', lambda text: text == 'SQLインジェクション')
# Independently construct an EVM state that has the given ratios and assess each claim.
ev,ac,pv,bac=360,450,400,1350
cpi,spi,tcpi=Fraction(ev,ac),Fraction(ev,pv),Fraction(bac-ev,bac-ac)
project=first['project']['stem']
assert (cpi,spi,tcpi)==tuple(Fraction(re.search(label+r'[^\n]+：(\d+\.\d+)',project)[1]) for label in ['CPI','SPI','TCPI'])
assert ev-ac<0 and ev-pv<0 and tcpi>1
unique('project',lambda text: 'コストが予算を超えて' in text and 'スケジュールが予定より遅れ' in text and '上げる必要がある' in text)

_,financials=svg_data(first['business']['image'])
sales,profits,assets=[[Fraction(value.replace(',','')) for value in row[1:]] for row in financials['rows']]
turnover=[s/a for s,a in zip(sales,assets)];margin=[p/s for p,s in zip(profits,sales)];returns=[p/a for p,a in zip(profits,assets)]
predicates=[sales[0]<sales[1] and assets[0]<assets[1] and turnover[0]<turnover[1],margin[0]>margin[1] and returns[0]>returns[1],profits[0]<profits[1] and assets[0]<assets[1] and returns[0]<returns[1],turnover[0]>turnover[1] and returns[0]>returns[1]]
assert [c['id'] for c,truth in zip(first['business']['choices'],predicates) if truth]==[first['business']['correctChoiceId']]

# Partial dependency witness: product name depends on only one part of a composite key.
rows={(1,10,'甲',100),(1,20,'甲',110),(2,10,'乙',200)}
products={(p,name) for p,v,name,price in rows};offers={(p,v,price) for p,v,name,price in rows}
joined={(p,v,name,price) for p,name in products for p2,v,price in offers if p==p2}
assert joined==rows
assert len({(p,v) for p,v,name,price in rows})==len(rows)
assert len({p for p,v,name,price in rows})<len(rows) # product alone is not the candidate key
assert '第1正規形から第2正規形' in first['database']['stem']
unique('database',lambda text:text.startswith('候補キーの一部の属性から、候補キー以外の属性への'))
unique('business-strategy',lambda text:text=='SWOT')

progress = read('content/ap/diagnostic-progress.json')
assert progress['publishedCount'] == len(questions)
assert progress['pendingReviewCount'] == sum(i['status']=='awaiting-independent-review' for i in progress['items'])
for topic, counts in progress['topicCounts'].items():
    assert counts['published'] == sum(q['topicId']==topic for q in questions)
assert not read('content/ap/qualification.json')['diagnosticBlueprint']['variantLimits']
assert set(progress['editorialPolicy']['alignedQuestionIds'])==set(by_id)
assert progress['editorialPolicy']['pendingCount']==0 and progress['editorialPolicy']['pendingQuestionIds']==[]
print('PASS first 17 reviewed questions / unique answers and fresh calculations / source hashes / final review hashes / honest single-worker review method / progress / unchanged per-topic cap')
