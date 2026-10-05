"""Apply explicitly authored three-step hints; keep the nine existing full lessons."""
import json
from pathlib import Path

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
    # Validate all records before writing, so a broken authoring file cannot erase the corpus.
    path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
    print(f'Individual hints: {len(bank)} questions; authored records: {len(assigned)}')


if __name__ == '__main__':
    main()
