"""Root's independent checks, transcribed from IPA images before reading lessons.

These complement the separate author and reviewer calculations; they do not
establish the educational quality of the prose.
"""
import itertools
import json
import sqlite3
from pathlib import Path

bank = {q['id']: q for q in json.loads(
    (Path(__file__).resolve().parents[1] / 'data/questions.json').read_text())}

# r04a Q2: Gray-code row/column order, six true cells, four expressions.
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
    matches = [old and actual == expected for old, actual in zip(matches, candidates)]
assert matches == [False, False, False, True]
assert matches.index(True) == bank['r04a-q2']['answer']
print('PASS r04a Q2: 16 assignments and all four Karnaugh expressions')

# r04a Q6: descend from n to i+1, exchanging adjacent inverted pairs.
def original_sort(values):
    a = [None, *values]  # original diagram uses one-based subscripts
    n = len(values)
    for i in range(1, n):
        for j in range(n, i, -1):
            if a[j] < a[j-1]:
                w = a[j]
                a[j] = a[j-1]
                a[j-1] = w
        assert a[1:i+1] == sorted(values)[:i]
    return a[1:]

for n in range(1, 8):
    for values in itertools.permutations(range(n)):
        assert original_sort(values) == sorted(values)
for values in itertools.product(range(3), repeat=5):
    assert original_sort(values) == sorted(values)
assert bank['r04a-q6']['answer'] == 3  # エ: bubble sort, not minimum-index selection
print('PASS r04a Q6: original loop direction, adjacent swaps, all permutations through n=7 and duplicates')

# r04a Q23: bubbles on the three final gates distinguish NAND/NOR from AND/OR.
matches = [True] * 4
truth_tables = [[] for _ in range(4)]
for x, y in itertools.product([False, True], repeat=2):
    candidates = [
        (x and y) and (not x and not y),
        (x or y) or (not x or not y),
        not (not (x and y) and not (not x and not y)),
        not (not (x or y) or not (not x or not y)),
    ]
    for table, actual in zip(truth_tables, candidates): table.append(int(actual))
    matches = [old and actual == (x == y) for old, actual in zip(matches, candidates)]
assert truth_tables == [[0, 0, 0, 0], [1, 1, 1, 1], [1, 0, 0, 1], [0, 1, 1, 0]]
assert matches == [False, False, True, False]
assert matches.index(True) == bank['r04a-q23']['answer']
print('PASS r04a Q23: all inputs of all four original circuits')

# r04a Q28: DISTINCT applies after comparing each product's margin with AVG.
db = sqlite3.connect(':memory:')
db.execute('CREATE TABLE products(code TEXT, price INTEGER, supplier TEXT, cost INTEGER)')
db.executemany('INSERT INTO products VALUES (?,?,?,?)', [
    ('A001', 1000, 'S1', 800), ('B002', 2500, 'S2', 2300),
    ('C003', 1500, 'S2', 1400), ('D004', 2500, 'S1', 1600),
    ('E005', 2000, 'S1', 1600), ('F006', 3000, 'S3', 2800),
    ('G007', 2500, 'S3', 2200), ('H008', 2500, 'S4', 2000),
    ('I009', 2500, 'S5', 2000), ('J010', 1300, 'S6', 1000),
])
assert db.execute('SELECT AVG(price-cost) FROM products').fetchone()[0] == 360
result = db.execute('''SELECT DISTINCT supplier FROM products
    WHERE price-cost > (SELECT AVG(price-cost) FROM products) ORDER BY supplier''').fetchall()
assert result == [('S1',), ('S4',), ('S5',)]
assert [1, 2, 3, 4][bank['r04a-q28']['answer']] == len(result)
print('PASS r04a Q28: original SQL, all ten rows, AVG and duplicate supplier')

# r04h Q47: branch coverage is about both compound decisions, not each clause.
def branches(a, b):
    c = 1
    first = a > 0 and b == 0
    c = a*c if first else 2
    second = a > 0 and c == 1
    if not second: c *= c
    return first, second

sets = [[(0, 0), (1, 1)], [(1, 0), (1, 1)],
        [(0, 0), (1, 1), (1, 0)], [(0, 0), (0, 1), (1, 0)]]
coverage = [all({branches(a, b)[i] for a, b in cases} == {False, True}
                for i in (0, 1)) for cases in sets]
assert coverage == [False, True, True, True]
smallest = min(len(cases) for cases, covers in zip(sets, coverage) if covers)
valid = [covers and len(cases) == smallest for cases, covers in zip(sets, coverage)]
assert valid == [False, True, False, False]
assert valid.index(True) == bank['r04h-q47']['answer']
print('PASS r04h Q47: every supplied test case, decision branches and minimality')

# r04h Q4: original word order X1 X2 X3 P3 X4 P2 P1, not numeric bit order.
def syndrome(word):
    x1, x2, x3, p3, x4, p2, p1 = map(int, word)
    return x1^x3^x4^p1, x1^x2^x4^p2, x1^x2^x3^p3

valid_words = []
for x1, x2, x3, x4 in itertools.product([0, 1], repeat=4):
    p1, p2, p3 = x1^x3^x4, x1^x2^x4, x1^x2^x3
    word = ''.join(map(str, [x1, x2, x3, p3, x4, p2, p1]))
    assert syndrome(word) == (0, 0, 0)
    valid_words.append(word)
assert min(sum(a != b for a, b in zip(x, y))
           for x, y in itertools.combinations(valid_words, 2)) == 3
for word in valid_words:
    for i in range(7):
        damaged = word[:i]+str(1-int(word[i]))+word[i+1:]
        assert [candidate for candidate in valid_words
                if sum(a != b for a, b in zip(candidate, damaged)) <= 1] == [word]
received = '1110011'
assert syndrome(received) == (1, 1, 1)
repaired = [word for word in valid_words if sum(a != b for a, b in zip(word, received)) == 1]
assert repaired == ['0110011']
choices = ['0110011', '1010011', '1100011', '1110111']
assert choices[bank['r04h-q4']['answer']] == repaired[0]
print('PASS r04h Q4: original field order, all 16 codewords and all 112 one-bit errors')

# r04h Q53: manual creation runs in parallel; education waits for both paths.
durations = {'requirements': 30, 'design': 20, 'build': 25,
             'test': 15, 'manual': 20, 'education': 10}
dependencies = {'requirements': [], 'design': ['requirements'], 'build': ['design'],
                'test': ['build'], 'manual': ['design'], 'education': ['test', 'manual']}
finish = {}
for task, duration in durations.items():
    finish[task] = max((finish[p] for p in dependencies[task]), default=0) + duration
assert finish == {'requirements': 30, 'design': 50, 'build': 75,
                  'test': 90, 'manual': 70, 'education': 100}
assert [80, 95, 100, 120][bank['r04h-q53']['answer']] == finish['education']
print('PASS r04h Q53: all six dependencies and the parallel manual path')

# r04h Q73: directed setup times; no initial setup or return-to-start is specified.
matrix = [[0, 2, 1, 2], [1, 0, 1, 2], [3, 2, 0, 2], [4, 3, 2, 0]]
routes = [(sum(matrix[a][b] for a, b in zip(order, order[1:])), order)
          for order in itertools.permutations(range(4))]
minimum = min(total for total, _ in routes)
assert minimum == 4 and (4, (1, 0, 2, 3)) in routes
assert [4, 5, 6, 7][bank['r04h-q73']['answer']] == minimum
print('PASS r04h Q73: all 24 job orders with original asymmetric setup times')
