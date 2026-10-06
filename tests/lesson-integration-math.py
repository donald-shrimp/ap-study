"""Root's independent image-based checks in addition to separate reviewers.

Constants, cells, and choices are transcribed from the original question images.
Run actual SQL and exhaustively compare all Karnaugh-map assignments.
"""
import itertools
import json
import sqlite3
from pathlib import Path

bank = {q['id']: q for q in json.loads(
    (Path(__file__).resolve().parents[1] / 'data/questions.json').read_text())}

# r07a Q1: AB and CD both follow Gray-code order 00, 01, 11, 10.
gray = [(0, 0), (0, 1), (1, 1), (1, 0)]
cells = [[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
matches = [True] * 4
for a, b, c, d in itertools.product([False, True], repeat=4):
    expected = bool(cells[gray.index((a, b))][gray.index((c, d))])
    candidates = [
        (a and b and not c and d) or (not b and not d),
        (not a and not b and not c and not d) or (b and d),
        (a and b and d) or (not b and not d),
        (not a and not b and not d) or (b and d),
    ]
    matches = [old and candidate == expected for old, candidate in zip(matches, candidates)]
assert matches == [False, False, False, True]
assert matches.index(True) == bank['r07a-q1']['answer']
print('PASS r07a Q1: all 16 Karnaugh-map assignments and all four expressions')

# r06a Q30: compare a grouped MIN join with each proposed window clause.
db = sqlite3.connect(':memory:')
db.execute('CREATE TABLE grades(student TEXT, round INTEGER, score INTEGER)')
db.executemany('INSERT INTO grades VALUES (?,?,?)', [
    ('S01', 1, 70), ('S01', 7, 80), ('S02', 2, 85), ('S02', 5, 82),
    ('S03', 3, 83), ('S03', 9, 78), ('S03', 12, 90), ('S04', 6, 100),
])
expected = db.execute('''SELECT r.student,r.round,r.score FROM grades r JOIN
    (SELECT student,MIN(round) first FROM grades GROUP BY student) m
    ON r.student=m.student AND r.round=m.first ORDER BY r.student''').fetchall()
clauses = ['ORDER BY student,round', 'PARTITION BY student ORDER BY round',
           'PARTITION BY student ORDER BY score ASC', 'PARTITION BY student ORDER BY score DESC']
results = [db.execute(f'''SELECT student,round,score FROM
    (SELECT *,ROW_NUMBER() OVER ({clause}) AS n FROM grades)
    WHERE n=1 ORDER BY student''').fetchall() for clause in clauses]
assert [result == expected for result in results] == [False, True, False, False]
assert bank['r06a-q30']['answer'] == 1
print('PASS r06a Q30: grouped-MIN query and all four actual window queries')

# r06h Q26: an absent inventory row and SQL NULL comparison are essential.
db.execute('CREATE TABLE parts(id TEXT, reorder_point INTEGER)')
db.execute('CREATE TABLE inventory(part TEXT, warehouse TEXT, quantity INTEGER)')
db.executemany('INSERT INTO parts VALUES (?,?)', [('P01', 100), ('P02', 150), ('P03', 100)])
db.executemany('INSERT INTO inventory VALUES (?,?,?)',
               [('P01', 'W01', 90), ('P01', 'W02', 90), ('P02', 'W01', 150)])
expressions = ['COALESCE(MIN(i.quantity),0)', 'COALESCE(MIN(i.quantity),NULL)',
               'COALESCE(SUM(i.quantity),0)', 'COALESCE(SUM(i.quantity),NULL)']
results = [db.execute(f'''SELECT p.id,CASE WHEN p.reorder_point>{expression}
    THEN '必要' ELSE '不要' END FROM parts p LEFT JOIN inventory i ON p.id=i.part
    GROUP BY p.id,p.reorder_point ORDER BY p.id''').fetchall() for expression in expressions]
expected = [('P01', '不要'), ('P02', '不要'), ('P03', '必要')]
assert [result == expected for result in results] == [False, False, True, False]
assert bank['r06h-q26']['answer'] == 2
print('PASS r06h Q26: outer join, aggregation, NULL and all four actual SQL expressions')

# r05a Q1: x is a two-bit unsigned value, int is the floor operation.
matches = [True] * 4
for x in range(4):
    expected = (x % 2) * 2 + x // 2
    candidates = [2*x + 4*(x//2), 2*x + 5*(x//2),
                  2*x - 3*(x//2), 2*x - 4*(x//2)]
    matches = [old and value == expected for old, value in zip(matches, candidates)]
assert matches == [False, False, True, False]
assert bank['r05a-q1']['answer'] == matches.index(True)
print('PASS r05a Q1: all four inputs and all four bit-reversal expressions')

# r05h Q1: test every allowed input, including the wrap from 255 to zero.
matches = [True] * 4
for n in range(256):
    expected = n+1 if n < 255 else 0
    candidates = [(n+1)&255, (n+1)&256, (n+1)|255, (n+1)|256]
    matches = [old and value == expected for old, value in zip(matches, candidates)]
assert matches == [True, False, False, False]
assert bank['r05h-q1']['answer'] == matches.index(True)
print('PASS r05h Q1: all 256 inputs and all four next-value expressions')

# r05h Q53: use period proportions, not effort proportions. Each program
# consumes equal time; the 100 unfinished programs are half of development.
from fractions import Fraction
period = list(map(Fraction, ['.25', '.21', '.11', '.11', '.11', '.21']))
assert sum(period) == 1
total_days = Fraction(228) / sum(period[:3])
remaining = total_days * (period[3] * Fraction(100, 200) + sum(period[4:]))
assert total_days == 400 and remaining == 150
assert [140, 150, 161, 172][bank['r05h-q53']['answer']] == remaining
print('PASS r05h Q53: period-based project duration and unfinished-program share')

# r05a Q6: reproduce two left-to-right bubble passes, not just the final sort.
values = [3, 5, 9, 6, 1, 2]
passes = []
for last in [5, 4]:
    for i in range(last):
        if values[i] > values[i+1]:
            values[i], values[i+1] = values[i+1], values[i]
    passes.append(values.copy())
assert passes == [[3, 5, 6, 1, 2, 9], [3, 5, 1, 2, 6, 9]]
assert bank['r05a-q6']['answer'] == 2
print('PASS r05a Q6: both supplied intermediate sorting states')

# r05h Q6: average successful comparisons, weighted by success probability,
# plus n comparisons on failure. Check all four proposed formulae separately.
valid = [True] * 4
for n in range(1, 21):
    success_mean = Fraction(sum(range(1, n+1)), n)
    for absent in [Fraction(0), Fraction(1, 3), Fraction(1)]:
        expected = success_mean * (1-absent) + n*absent
        candidates = [Fraction(n+1, 2)*n*absent,
                      Fraction(n+1, 2)*(1-absent),
                      Fraction(n+1, 2)*(1-absent)+Fraction(n, 2),
                      Fraction(n+1, 2)*(1-absent)+n*absent]
        valid = [old and value == expected for old, value in zip(valid, candidates)]
assert valid == [False, False, False, True]
assert bank['r05h-q6']['answer'] == valid.index(True)
print('PASS r05h Q6: search-cost enumeration and all four probability formulae')

# r05h Q7: the problem specifies stable partitioning with the first element
# as pivot. The singleton left group requires no further partition.
def stable_partition(group):
    pivot = group[0]
    return ([v for v in group[1:] if v < pivot], pivot,
            [v for v in group[1:] if v > pivot])
left, pivot, right = stable_partition([2, 3, 5, 4, 1])
assert (left, pivot, right) == ([1], 2, [3, 5, 4])
left2, pivot2, right2 = stable_partition(right)
after_two = left + [pivot] + left2 + [pivot2] + right2
choices = [[1,2,3,5,4], [1,2,5,4,3], [2,3,1,4,5], [2,3,4,5,1]]
assert after_two == [1,2,3,5,4]
assert bank['r05h-q7']['answer'] == choices.index(after_two)
print('PASS r05h Q7: two stable first-pivot partitions and all four candidate arrays')

# r05a Q29: correlated NOT EXISTS, with an absent product and an exact
# boundary value of 30. Summing warehouses would give a different result.
db.execute('CREATE TABLE products(id TEXT)')
db.execute('CREATE TABLE stock(warehouse TEXT, product TEXT, quantity INTEGER)')
db.executemany('INSERT INTO products VALUES (?)', [(x,) for x in
               ['AB1805', 'CC5001', 'MZ1000', 'XZ3000', 'ZZ9900']])
db.executemany('INSERT INTO stock VALUES (?,?,?)', [
    ('WH100','AB1805',20), ('WH100','CC5001',200), ('WH100','ZZ9900',130),
    ('WH101','AB1805',150), ('WH101','XZ3000',30), ('WH102','XZ3000',20),
    ('WH102','ZZ9900',10), ('WH103','CC5001',40)])
result = db.execute('''SELECT DISTINCT p.id FROM products p WHERE NOT EXISTS
    (SELECT s.product FROM stock s WHERE s.quantity>30 AND p.id=s.product)
    ORDER BY p.id''').fetchall()
assert result == [('MZ1000',), ('XZ3000',)]
assert [1,2,3,4][bank['r05a-q29']['answer']] == len(result)
print('PASS r05a Q29: actual NOT EXISTS query, missing rows and strict >30 boundary')
