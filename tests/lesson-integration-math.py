"""Root's independent image-based checks in addition to the three reviewers.

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
