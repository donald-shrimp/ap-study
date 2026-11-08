"""Verify the third batch's arithmetic and small spec models, not real devices."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
bank = {c['id']: c for c in json.loads((ROOT / 'content/ap/written-cases.json').read_text())}

def answer(cid, item_id, field_id):
    item = next(i for i in bank[cid]['items'] if i['id'] == item_id)
    return next(f['referenceAnswers'][0] for f in item['fields'] if f['id'] == field_id)

minutes = Decimal(30*24*60)
guarantee = Decimal('0.9995')
actual = Decimal('0.995')
outage_limit = minutes*(1-guarantee)
rounded_minutes = outage_limit.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
discount = Decimal(200000)*(guarantee-actual)
assert minutes == 43200 and outage_limit == Decimal('21.6')
assert str(rounded_minutes) == answer('ap-r07h-pm4', 'q2-2', 'g') == '22'
assert (minutes-outage_limit)/minutes == guarantee
assert (minutes-Decimal(22))/minutes < guarantee
assert int(discount) == int(answer('ap-r07h-pm4', 'q2-3', 'answer')) == 900
assert Decimal(200000)*(1-actual) == 1000

def transition(state, event, speed=Decimal('0')):
    if state == '停止中' and event == '手押し' and speed >= Decimal('0.3'):
        return '走行準備'
    if state == '走行準備' and event == '手押し' and speed >= Decimal('3'):
        return '加速可能'
    if state == '加速可能' and event == 'アクセルを押す':
        return '走行中'
    if state == '走行中' and event == 'アクセルを戻す':
        return '加速可能'
    # The spec gives no numeric duration: this event means it already continued.
    if state in ['走行準備', '加速可能', '走行中'] and event == '低速が一定時間継続' and speed < Decimal('0.1'):
        return '停止中'
    return state

state = '停止中'
trajectory = []
for event, speed in [('手押し', Decimal('0.3')), ('手押し', Decimal('3')), ('アクセルを押す', Decimal('3')), ('アクセルを戻す', Decimal('3'))]:
    state = transition(state, event, speed)
    trajectory.append(state)
assert trajectory == ['走行準備', '加速可能', '走行中', '加速可能']
assert answer('ap-r07h-pm7', 'q1', 'answer') == 'ウ'
assert transition('走行中', '低速が一定時間継続', Decimal('0.099')) == '停止中'
assert transition('走行中', '低速が一定時間継続', Decimal('0.1')) == '走行中'
assert transition('走行中', '一瞬だけ低速', Decimal('0.099')) == '走行中'

body = bank['ap-r07h-pm7']['body']
caption = '表3 本システムで使用する主なメッセージ'
rows = []
for line in body[body.index(caption):].splitlines()[2:]:
    if not line:
        continue
    if not line.startswith('|'):
        break
    cells = [c.strip() for c in line.strip('|').split('|')]
    if cells[0] not in ['メッセージ名', '---']:
        rows.append(cells)
messages = {row[0].replace('¹⁾', '').replace('²⁾', ''): row[1:3] for row in rows}
names = ['貸出し要求', '貸出し指示', '車輪ロック解除指示', '車輪ロック解除応答', '貸出し応答']
peers = [messages[name] for name in names]
assert peers == [['アプリ', '管理サーバ'], ['管理サーバ', 'アプリ'], ['アプリ', '電動KB'], ['電動KB', 'アプリ'], ['アプリ', '管理サーバ']]
assert [answer('ap-r07h-pm7', 'q4-1', key) for key in ['e', 'f', 'g']] == ['エ', 'オ', 'ア']

first_ms = [200, 200]
second_ms = [10, 1000, 10, 500, 10, 1000, 10]
first = (Decimal(sum(first_ms))/1000).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
second = (Decimal(sum(second_ms))/1000).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
assert str(first) == answer('ap-r07h-pm7', 'q4-2', 'one') == '0.40'
assert str(second) == answer('ap-r07h-pm7', 'q4-2', 'two') == '2.54'

limits = []
for cid in ['ap-r07h-pm2', 'ap-r07h-pm4', 'ap-r07h-pm7']:
    for item in bank[cid]['items']:
        for field in item['fields']:
            if field.get('maxLength', 2000) < 2000:
                for value in field['referenceAnswers']:
                    assert len(value) <= field['maxLength']
                    limits.append({'caseId': cid, 'itemId': item['id'], 'characters': len(value), 'maximum': field['maxLength'], 'answer': value})

print(json.dumps({'scope': 'exact arithmetic, source message table comparison and a small model of selected state transitions; no live cloud or vehicle test; strategy interpretation is separately reviewed', 'sla': {'monthlyMinutes': str(minutes), 'exactOutageLimitMinutes': str(outage_limit), 'answerAfterRounding': str(rounded_minutes), '22MinutesMeetsGuarantee': False, 'discountYen': int(discount), 'incorrectAllOutageDiscountYen': 1000}, 'embedded': {'trajectory': trajectory, 'messageNames': names, 'messagePeers': peers, 'firstIntervalMilliseconds': first_ms, 'secondIntervalMilliseconds': second_ms, 'firstAnswerSeconds': str(first), 'secondAnswerSeconds': str(second), 'excludedLaterReportMilliseconds': 200, 'lowSpeedThresholdStrictAndDurationRequired': True}, 'answerLimits': limits}, ensure_ascii=False, indent=2))
