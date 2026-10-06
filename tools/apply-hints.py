"""Apply explicit hints, then the reviewed explanation-and-hint lesson sources."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TITLES = ['注目するところ', '使う考え方', 'この問題に当てはめる']


def main():
    path = ROOT / 'data/questions.json'
    bank = json.loads(path.read_text())
    by_id = {q['id']: q for q in bank}
    assigned = set()
    for file in sorted((ROOT / 'data/hint-authoring').glob('*.txt')):
        for lineno, line in enumerate(file.read_text().splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            fields = line.split('|')
            source = f'{file.name}:{lineno}'
            if len(fields) not in (5, 6):
                raise ValueError(f'{source}: expected IDs, concept, three hints, optional flags')
            ids, concept, *content = fields
            texts = content[:3]
            flags = content[3] if len(content) == 4 else '000'
            if len(flags) != 3 or set(flags) - {'0', '1'} or not all(texts):
                raise ValueError(f'{source}: empty hint or invalid answer-reveal flags')
            for id in ids.split():
                if id not in by_id or id in assigned:
                    raise ValueError(f'{source}: unknown or duplicate question {id}')
                assigned.add(id)
                q = by_id[id]
                q.update(concept=concept, hintStatus='individual', hintSource=source)
                q['hints'] = [
                    {'title': title, 'text': text, 'revealsAnswer': flag == '1'}
                    for title, text, flag in zip(TITLES, texts, flags)
                ]
    for q in bank:
        if q['id'] not in assigned:
            if q['enrichment'] != 'reviewed':
                raise ValueError(f"Missing individual hints: {q['id']}")
            q.update(hintStatus='individual', hintSource='existing-reviewed')
    # A complete lesson is the single source for both its explanation and hints.
    # Apply it last so rebuilding the bank cannot restore older, separate hints.
    lessons = set()
    for file in sorted((ROOT / 'data/lessons').glob('*.json')):
        for lesson in json.loads(file.read_text()):
            id = lesson['id']
            source = f'lessons/{file.name}:{id}'
            if id not in by_id or id in lessons:
                raise ValueError(f'{source}: unknown or duplicate lesson')
            if lesson.get('checkedAgainst') != 'official-question-image-and-answer-key':
                raise ValueError(f'{source}: source check missing')
            fields = ['summary', 'explanation', 'takeaway']
            if not all(isinstance(lesson.get(f), str) and lesson[f].strip() for f in fields):
                raise ValueError(f'{source}: incomplete explanation')
            reasons, hints = lesson.get('choiceReasons', []), lesson.get('hints', [])
            if len(reasons) != 4 or not all(isinstance(r, str) and r.strip() for r in reasons):
                raise ValueError(f'{source}: four choice reasons required')
            if len(hints) != 3 or not all(
                isinstance(h.get('text'), str) and h['text'].strip()
                and isinstance(h.get('title'), str) and h['title'].strip()
                and isinstance(h.get('revealsAnswer'), bool) for h in hints
            ):
                raise ValueError(f'{source}: invalid three-step hints')
            lessons.add(id)
            by_id[id].update({f: lesson[f] for f in [*fields, 'choiceReasons', 'hints']})
            by_id[id].update(enrichment='reviewed', hintStatus='individual', hintSource=source,
                             lessonSource=source)
    # Validate all records before writing, so a broken authoring file cannot erase the corpus.
    path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
    print(f'Individual hints: {len(bank)}; hint assignments: {len(assigned)}; complete lessons: {len(lessons)}')
    # Runtime reads qualification packs, not this authoring JSON. Keep the
    # existing AP authoring command sufficient to update the published material.
    subprocess.run([sys.executable, str(ROOT / 'tools/build-content.py')], check=True)


if __name__ == '__main__':
    main()
