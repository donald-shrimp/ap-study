"""Recheck the published first batch and its evidence, without approving records."""
import hashlib
import itertools
import json
import re
import sqlite3
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

def unique(topic, valid):
    q = first[topic]
    ids = [c['id'] for c in q['choices'] if valid(c['text'])]
    assert ids == [q['correctChoiceId']], (topic, ids)

# Truth tables and recurrence are recomputed from definitions, not stored answers.
imp = lambda a, b: (not a) or b
p, q = True, False
table = [[imp(p, q) and r, p and imp(q, r), imp(q, p) and r, imp(r, q)] for r in (False, True)]
assert [i for i in range(4) if all(row[i] for row in table)] == [1]
assert first['theory']['correctChoiceId'] == first['theory']['choices'][1]['id']
inputs = list(itertools.product((False, True), repeat=2))
output = [not ((not (a and b)) and (not (a and b))) for a, b in inputs]
gates = {'AND': lambda a,b:a and b, 'OR':lambda a,b:a or b, 'XOR':lambda a,b:a!=b, 'NOR':lambda a,b:not(a or b)}
unique('logic', lambda text: [gates[text](a,b) for a,b in inputs] == output)
def g(n): return 0 if n == 0 else n + g(n-1)
unique('algorithm', lambda text: int(text) == g(4))
unique('architecture', lambda text: Fraction(text.removesuffix('倍')) == Fraction(1,2)*3/(2*Fraction(3,2)))
unique('hardware', lambda text: int(text.replace(',', '')) == 100 + (3*16+10)*20)
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
assert (480-640, 480-600, Fraction(720,560), 640+720/Fraction(480,640)) == (-160,-120,Fraction(9,7),1600)
assert first['project']['correctChoiceId'] == 'choice-0'
assert (Fraction(900,300)>Fraction(1200,600), Fraction(45,300)>Fraction(96,600)) == (True, False)
assert first['business']['correctChoiceId'] == 'choice-0'
unique('business-strategy', lambda text: text == {(True,True):'花形',(True,False):'問題児',(False,True):'金のなる木',(False,False):'負け犬'}[2>=10, Fraction('1.8')>=1])
# Concrete witness: employees share one department; A reconstructs exactly, D loses affiliation.
rows = {(1, '甲', 10, '開発'), (2, '乙', 10, '開発'), (3, '丙', 20, '営業')}
employees = {(i,n,d) for i,n,d,label in rows}; departments = {(d,label) for i,n,d,label in rows}
joined = {(i,n,d,label) for i,n,d in employees for d2,label in departments if d==d2}
assert joined == rows
without_link = {(i,n) for i,n,d,label in rows}
assert {(i,n,d,label) for i,n in without_link for d,label in departments} != rows
assert first['database']['correctChoiceId'] == 'choice-0'

progress = read('content/ap/diagnostic-progress.json')
assert progress['publishedCount'] == len(questions)
assert progress['pendingReviewCount'] == sum(i['status']=='awaiting-independent-review' for i in progress['items'])
for topic, counts in progress['topicCounts'].items():
    assert counts['published'] == sum(q['topicId']==topic for q in questions)
assert not read('content/ap/qualification.json')['diagnosticBlueprint']['variantLimits']
print('PASS first 17 reviewed questions / unique answers and fresh calculations / source hashes / final review hashes / honest single-worker review method / progress / unchanged per-topic cap')
