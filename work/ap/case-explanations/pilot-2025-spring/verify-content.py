"""Check worked examples against the existing case SQL and source numbers."""
import json
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
bank = {c['id']: c for c in json.loads((ROOT / 'content/ap/written-cases.json').read_text())}
db_case = bank['ap-r07h-pm6']
queries = re.findall(r'```sql\n(.*?)\n```', db_case['body'], re.S)
assert len(queries) == 2
answers = {f['id']: f['referenceAnswers'][0] for i in db_case['items'] for f in i['fields']}
filled = [re.sub(r'［([c-g])］', lambda m: answers[m[1]], q) for q in queries]

con = sqlite3.connect(':memory:')
con.executescript('''
CREATE TABLE キャンペーン実施 (キャンペーン番号 INTEGER, キャンペーン種別 TEXT, キャンペーン実施金額 INTEGER);
CREATE TABLE 売上 (売上番号 INTEGER, キャンペーン番号 INTEGER, キャンペーン種別 TEXT, 会員番号 INTEGER, 店舗番号 INTEGER, 売上年月日 TEXT);
CREATE TABLE 売上明細 (売上番号 INTEGER, 商品番号 INTEGER, 商品個数 INTEGER, 商品単価 INTEGER);
CREATE TABLE 商品 (商品番号 INTEGER, 商品原価 INTEGER);
CREATE TABLE 会員 (会員番号 INTEGER, 会員郵便番号 TEXT);
INSERT INTO キャンペーン実施 VALUES (1,'H',75),(1,'H',75),(1,'E',50);
INSERT INTO 商品 VALUES (1,70);
INSERT INTO 会員 VALUES (1,'1110001'),(2,'1110002');
INSERT INTO 売上 VALUES (1,1,'H',1,1,'2025-03-01'),(2,1,'H',1,1,'2025-03-02'),(3,1,'B',2,1,'2025-03-02');
INSERT INTO 売上明細 VALUES (1,1,1,200),(2,1,1,200),(3,1,1,200);
''')
outer = con.execute(filled[0], {'キャンペーン番号': 1}).fetchall()
assert sorted(outer) == [('E', 0, 0, 0, 50), ('H', 400, 140, 260, 150)], outer
inner = con.execute(filled[0].replace('LEFT OUTER JOIN', 'INNER JOIN'), {'キャンペーン番号': 1}).fetchall()
assert inner == [('H', 400, 140, 260, 150)], inner
postal = con.execute(filled[1], {'店舗番号': 1, '一年前年月日': '2025-01-01'}).fetchall()
assert postal == [('1110001', 2)], postal
members = con.execute(filled[1].replace('COUNT(*)', 'COUNT(DISTINCT U.会員番号)'), {'店舗番号': 1, '一年前年月日': '2025-01-01'}).fetchall()
assert members == [('1110001', 1)], members

weights = [2, 1.5, 1, 1, 1]
scores = {'K': [4, 4, 4, 3, 4], 'L': [3, 3, 3, 4, 4], 'M': [4, 5, 5, 2, 4], 'N': [3, 3, 4, 5, 5]}
totals = {k: sum(a*b for a, b in zip(values, weights)) for k, values in scores.items()}
assert totals == {'K': 25, 'L': 21.5, 'M': 26.5, 'N': 24.5}
eligible = [k for k, values in scores.items() if min(values) > 2]
assert max(eligible, key=totals.get) == 'K'
assert 70-30+1 == 41 and 70-41+1 == 30
durations = [30, 30, 30, 20]
buffers = [d//10 for d in durations]
work = sum(d-b for d, b in zip(durations, buffers))
assert work == 99 and sum(buffers) == 11
assert work+12 == 111 and (work+12)-(work+sum(buffers)) == 1
assert work+10 == 109

counts = []
for cid in ['ap-r07h-pm1', 'ap-r07h-pm6', 'ap-r07h-pm9']:
    text = (HERE / (cid+'.md')).read_text()
    for answer, length in re.findall(r'「([^「」\n]+)」（(\d+)字）', text):
        assert len(answer) == int(length), (cid, answer, len(answer), length)
        counts.append({'caseId': cid, 'answer': answer, 'characters': len(answer)})
    assert bank[cid]['version'] == 1

print(json.dumps({'sqlExamples': {'outerJoin': sorted(outer), 'innerJoin': inner, 'salesRowsByPostalCode': postal, 'distinctMembersByPostalCode': members}, 'weightedTotals': totals, 'selectedVendor': 'K', 'schedule': {'latestStartB': 41, 'chainWorkdays': work, 'projectBuffer': sum(buffers), 'deadline': 110, 'delayedFinish': 111, 'deadlineOverrun': 1}, 'answerCharacterCounts': counts}, ensure_ascii=False, indent=2))
