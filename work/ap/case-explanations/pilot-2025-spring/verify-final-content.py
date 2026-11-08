"""Verify the final batch's numerical example, answer limits and delivery scope."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
bank = {c['id']: c for c in json.loads((ROOT / 'content/ap/written-cases.json').read_text())}
expected = {f'ap-r07h-pm{n}' for n in range(1, 12)}
drafts = {p.stem for p in HERE.glob('ap-r07h-pm*.md')}
mapping = json.loads((HERE / 'explanation-links.json').read_text())
assert drafts == expected and set(mapping) == expected
assert sum(len(i['fields']) for cid in expected for i in bank[cid]['items']) == 96
assert sum(len(targets) for targets in mapping.values()) == 88

# The draft labels these as illustrative requests, not observed production data.
responses = [Decimal('1')]*94 + [Decimal('4')]*6
average = sum(responses)/len(responses)
within_three = sum(t <= Decimal('3') for t in responses)
ratio = Decimal(within_three)/len(responses)
assert average == Decimal('1.18')
assert average < Decimal('3') and ratio == Decimal('0.94') < Decimal('0.95')
boundary_example = [Decimal('3')]*95 + [Decimal('4')]*5
assert sum(t <= Decimal('3') for t in boundary_example) == 95

# Verify elapsed time without inventing a P-batch start time or processing cost.
start = datetime.strptime('13:05', '%H:%M')
finish = datetime.strptime('13:15', '%H:%M')
deadline = datetime.strptime('13:30', '%H:%M')
assert int((finish-start).total_seconds()/60) == 10
assert finish < deadline
assert all(s in bank['ap-r07h-pm10']['body'] for s in ['13時05分', '13時15分', '13時30分'])

limits = []
for cid in ['ap-r07h-pm8', 'ap-r07h-pm10']:
    for item in bank[cid]['items']:
        for field in item['fields']:
            if field.get('maxLength', 2000) < 2000:
                for answer in field['referenceAnswers']:
                    assert len(answer) <= field['maxLength']
                    limits.append({'caseId': cid, 'itemId': item['id'], 'fieldId': field['id'], 'answer': answer, 'characters': len(answer), 'maximum': field['maxLength']})

print(json.dumps({'scope': 'worked numerical example, source timestamps, official answer lengths and full pilot coverage; not a live CRM or service load test; meaning and access rules are independently reviewed', 'coverage': {'cases': len(expected), 'sourceFields': 96, 'explanationTargets': 88}, 'illustrativeSLA': {'requests': len(responses), 'averageSeconds': str(average), 'withinThreeSeconds': within_three, 'fractionWithinThreeSeconds': str(ratio), 'meets95PercentTarget': False, 'exactlyThreeSecondsIncluded': True}, 'incidentTimeline': {'delayStarted': '13:05', 'observedBatchEnded': '13:15', 'observedDelayMinutes': 10, 'resultDeliveryDeadline': '13:30', 'observedEndBeforeDeadline': True, 'futureEndAtOrAfterDeadlineIsSeparateScenario': True}, 'answerLimits': limits}, ensure_ascii=False, indent=2))
