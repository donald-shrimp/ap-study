"""Root checks independently transcribed from IPA images before reading lessons.

These verify calculations and original diagrams, not educational prose quality.
"""
from collections import deque
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations, product
import json
from pathlib import Path

bank = {q['id']: q for q in json.loads(
    (Path(__file__).resolve().parents[1]/'data/questions.json').read_text())}

def official(n, index):
    assert bank[f'r03h-q{n}']['answer'] == index, n

# Q1: four Venn diagrams correspond to IFF, NOR, AND and OR.
matches = [True]*4
for x, y in product([False, True], repeat=2):
    candidates = [x == y, not (x or y), x and y, x or y]
    matches = [old and value == (not (x != y))
               for old, value in zip(matches, candidates)]
assert matches == [True, False, False, False]
official(1, matches.index(True))
print('PASS r03h Q1: all four inputs and all four original Boolean candidates')

# Q3: mono, 40 kHz, 16 bits, decimal kbyte expressly defined as 1000 bytes.
kbytes = F(40_000*16, 8*1000)
assert kbytes == 80
official(3, [20, 40, 80, 640].index(kbytes))
print('PASS r03h Q3: samples to bits to bytes, mono and decimal kbyte')

# Q6: A[1] is root; children of A[i] are A[2i] and A[2i+1].
def breadth(n):
    waiting = deque([1]); out = []
    while waiting:
        i = waiting.popleft()
        if i > n: continue
        out.append(i); waiting.extend([2*i, 2*i+1])
    return out

def depth(i, n, mode):
    if i > n: return []
    left, right = depth(2*i,n,mode), depth(2*i+1,n,mode)
    return {'pre': [i]+left+right, 'post': left+right+[i],
            'in': left+[i]+right}[mode]

for n in range(1, 201):
    assert breadth(n) == list(range(1, n+1))
orders = [depth(1,7,m) for m in ['pre','post','in']]+[breadth(7)]
assert orders == [[1,2,4,5,3,6,7], [4,5,2,6,7,3,1],
                  [4,2,5,1,6,3,7], [1,2,3,4,5,6,7]]
official(6, orders.index(list(range(1,8))))
print('PASS r03h Q6: original child indices, all four traversals, n=1..200')

# Q14: two series pairs are connected in parallel. Enumerate all 16 states.
for x in [F(0), F(1,10), F(1,2), F(9,10), F(1)]:
    total = F(0)
    for alive in product([0,1], repeat=4):
        if alive[0] and alive[1] or alive[2] and alive[3]:
            total += x**sum(alive)*(1-x)**(4-sum(alive))
    assert total == 1-(1-x*x)**2 == 2*x*x-x**4
assert 2*F(1,2)**2-F(1,2)**4 == F(7,16) < F(1,2)
assert 2*F(9,10)**2-F(9,10)**4 == F(9639,10000) > F(9,10)
# エ is below y=x near zero and above it near one, unlike the three alternatives.
official(14, 3)
print('PASS r03h Q14: 16 component states, series/parallel topology and graph crossing')

# Q16: one execution slot; original arrivals and durations are separate columns.
end = 0; timeline = []
for name,arrival,duration in [('A',0,5),('B',2,6),('C',3,3)]:
    start = max(end, arrival); end = start+duration
    timeline.append((name,start,end,end-arrival))
assert timeline == [('A',0,5,5),('B',5,11,9),('C',11,14,11)]
official(16, [11,12,13,14].index(timeline[-1][-1]))
print('PASS r03h Q16: FIFO timeline, C completion 14 minus arrival 3')

# Q53: the revised dummy arrow points from E2's end to E1's end, duration zero.
common = [('s','a',5),('a','b',8),('a','c',7),('b','d',7),
          ('c','merge',5),('d','end',7),('merge','h',4),('h','end',2)]
before = common+[('b','merge',9)]
after = common+[('b','e1',3),('b','e2',4),('e2','e1',0),('e1','merge',2)]
def finish_times(edges):
    nodes = {v for edge in edges for v in edge[:2]}
    @lru_cache(None)
    def finish(v):
        return max((finish(u)+duration for u,w,duration in edges if w==v), default=0)
    return {v:finish(v) for v in nodes}
old, new = finish_times(before), finish_times(after)
assert old['end'] == 28 and new['end'] == 27
assert new['e2'] == new['e1'] == 17 and new['merge'] == 19
# The previously noncritical A-B-D-G path remains 27, so the gain is only one day.
assert sum([5,8,7,7]) == 27
official(53, [1,2,3,4].index(old['end']-new['end']))
print('PASS r03h Q53: both original DAGs, reverse dummy arrow, changed critical path')

# Q55: total meeting hours, not participant-hours or elapsed hours with parallelism.
pairs = list(combinations(range(16),2))
assert len(pairs) == 16*15//2 == 120
hours = len(pairs)*F(1,2)
assert hours == 60
official(55, [8,16,30,60].index(hours))
print('PASS r03h Q55: all 120 unordered pairs, half-hour each, total meeting hours')
