"""Check additional worked examples; not real networking or a pseudo-code runtime."""
import ast
import json
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
bank = {c['id']: c for c in json.loads((ROOT / 'content/ap/written-cases.json').read_text())}

def neighbors(board):
    """A small Python model using the original direction order and 1-based bounds."""
    n = len(board)
    row, col = next((r+1, c+1) for r in range(n) for c in range(n) if board[r][c] == n*n)
    for dr, dc in [(1, 0), (0, -1), (-1, 0), (0, 1)]:
        r, c = row+dr, col+dc
        if 1 <= r <= n and 1 <= c <= n:
            changed = [list(line) for line in board]
            changed[row-1][col-1], changed[r-1][c-1] = changed[r-1][c-1], changed[row-1][col-1]
            yield tuple(tuple(line) for line in changed)

start = ((8, 6, 7), (2, 5, 4), (3, 9, 1))
second = ((8, 6, 7), (2, 9, 4), (3, 5, 1))
assert second in list(neighbors(start))
official = bank['ap-r07h-pm3']['items'][0]['fields'][0]['referenceAnswers'][0]
assert ast.literal_eval(official.replace('{', '[').replace('}', ']')) == [list(row) for row in second]
assert len(list(neighbors(start))) == 3
corner_moves = {}
for n in [2, 3, 4]:
    values = list(range(1, n*n+1))
    values[0], values[-1] = values[-1], values[0]
    board = tuple(tuple(values[i:i+n]) for i in range(0, len(values), n))
    destinations = list(neighbors(board))
    assert len(destinations) == 2
    assert all(sorted(v for row in b for v in row) == list(range(1, n*n+1)) for b in destinations)
    corner_moves[str(n)] = len(destinations)

# Explain FIFO order with exactly the draft's small named-state example.
queue = deque(['開始盤面'])
assert queue.popleft() == '開始盤面'
queue.extend(['A', 'B'])
assert queue.popleft() == 'A'
queue.extend(['C', 'D'])
assert list(queue) == ['B', 'C', 'D']

# A short puzzle checks the model's shortest route and predecessor reconstruction.
goal = ((1, 2, 3), (4, 5, 6), (7, 8, 9))
short_start = ((1, 2, 3), (4, 5, 6), (9, 7, 8))
queue = deque([short_start])
previous = {short_start: None}
while queue:
    current = queue.popleft()
    if current == goal:
        break
    for nxt in neighbors(current):
        if nxt not in previous:
            previous[nxt] = current
            queue.append(nxt)
path = [goal]
while previous[path[-1]] is not None:
    path.append(previous[path[-1]])
path.reverse()
assert path[0] == short_start and len(path)-1 == 2
assert all(b in list(neighbors(a)) for a, b in zip(path, path[1:]))

def table(body, caption):
    lines = body[body.index(caption):].splitlines()[1:]
    rows = []
    for line in lines:
        if not line.startswith('|'):
            break
        rows.append([cell.strip() for cell in line.strip('|').split('|')])
    return rows[2:]

network = bank['ap-r07h-pm5']['body']
devices = table(network, '表1 IPアドレスを固定で割り当てている主な機器のIPアドレスとMACアドレス')
arp = table(network, '表2 PC-CのARPテーブル')
traffic = table(network, '表3 社内LANとDMZとの間の送信元と送信先の組合せ別のパケットの割合（一部）')
printer = next(r for r in devices if r[0] == 'プリンタ')
observed = next(r for r in arp if r[1] == printer[1])
assert printer[1] == '192.168.1.21' and printer[2].endswith('63')
assert observed[2].endswith('E4') and observed[2] != printer[2]
shared_ips = set.intersection(*[set(row[:2]) for row in traffic])
assert shared_ips == {'192.168.11.51'}
assert next(row[0] for row in devices if row[1] in shared_ips) == 'ファイルサーバ'
assert next(row[1] for row in devices if row[0] == 'キャッシュDNSサーバ') == '192.168.11.41'

audit = bank['ap-r07h-pm11']
limits = []
for case_id in ['ap-r07h-pm5', 'ap-r07h-pm11']:
    for item in bank[case_id]['items']:
        for field in item['fields']:
            if field.get('maxLength', 2000) < 2000:
                for answer in field['referenceAnswers']:
                    assert len(answer) <= field['maxLength']
                    limits.append({'caseId': case_id, 'itemId': item['id'], 'answer': answer, 'characters': len(answer), 'maximum': field['maxLength']})
assert 13-8 == 5
assert '1月140時間' in audit['body'] and '1月160時間' in audit['body']

print(json.dumps({'scope': 'worked-example models and source table comparisons; no live network, payroll, or original pseudo-code execution', 'algorithm': {'secondBoard': second, 'originalStartLegalMoves': 3, 'cornerMovesByBoardSize': corner_moves, 'fifoAfterExpandingA': ['B', 'C', 'D'], 'illustrativeShortestPath': path, 'illustrativeMoveCount': 2}, 'network': {'printerIP': printer[1], 'expectedMAC': printer[2], 'observedMAC': observed[2], 'commonTrafficPeer': list(shared_ips), 'commonTrafficDevice': 'ファイルサーバ', 'exampleDNS': '192.168.11.41'}, 'audit': {'illustrativeStartDifferenceHours': 5, 'storeMonthlyStandardHoursJanuary': {'販売職': 140, '事務職': 160}}, 'answerLimits': limits}, ensure_ascii=False, indent=2))
