"""Author's candidate assembly and source hashing. This does not create reviews."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

case = json.loads((HERE / 'blind.json').read_text())
case['body'] = (HERE / 'body.md').read_text().strip()
case['bodyFormat'] = 'hitomon-markdown-math-v1'
case['source'] = 'IPA 令和7年度春期 応用情報技術者試験 午後 問1'
base = 'https://www.ipa.go.jp/shiken/mondai-kaiotu/nl10bi0000009lh8-att/'
case['sourceRefs'] += [base + '2025r07h_ap_pm_ans.pdf', base + '2025r07h_ap_pm_cmnt.pdf']
case['sourcePages'] = [6, 7, 8, 9, 10]
case['imageSizes'] = {p: {'width': Image.open(REPO / p).width, 'height': Image.open(REPO / p).height} for p in case['sourceImages']}
case['bodyFigures'] = [{'id': 'figure-1', 'image': 'assets/written/ap-r07h-pm1/figure-1.png', 'caption': '図1 C社及びP社のネットワーク構成（抜粋）', 'sourcePage': 6, 'placement': 'replace-caption', 'anchor': '図1 C社及びP社のネットワーク構成（抜粋）', 'alt': 'C社及びP社のネットワーク構成。C社にはDMZセグメントのWebサーバ，バックアップセグメントのNAS，業務セグメントのAPサーバ，DBサーバ，PC-C，PC-S，PC-Rがある。FW1を介してインターネットへ接続する。P社にはVPNルータ，FW3，業務セグメントのPC-Pがあり，C社のFW2と広域イーサネットで接続する。C社販売店の販売店PC，P社販売店の販売店PC，P社従業員自宅の自宅PCはインターネットに接続する。原本画像に結線と配置を保持。'}]
case['bodyRefs'] = {
    'figure-1': {'sourcePages': [6], 'anchor': '図1 C社及びP社のネットワーク構成（抜粋）'},
    'table-1': {'sourcePages': [7], 'anchor': '表1 C社FW1，FW2及びP社FW3の許可ルール（抜粋）'},
    'table-2': {'sourcePages': [9], 'anchor': '表2 C社の課題（抜粋）'},
    'underline-1': {'sourcePages': [7], 'text': '①電磁的記録の証拠保全，調査及び分析'},
    'underline-2': {'sourcePages': [9], 'text': '②今回と同様の攻撃を防御するために，PC-Pの設定を変更した。ただし，パスワードが漏えいし，リバースブルートフォース攻撃を受けた場合は，このPC-Pの設定変更では防御できないおそれがある'},
    'underline-3': {'sourcePages': [9], 'text': '③バックアップデータからの復旧に問題が生じたおそれがある'},
    'underline-4': {'sourcePages': [9], 'text': '④過去に発生した事象が調査できなくなるおそれがある'},
    'blank-a': {'sourcePages': [8], 'text': 'PC-Pへ［a］攻撃'},
    'blank-b': {'sourcePages': [8], 'text': '［b］でPC-Rへログイン'},
    'blank-c': {'sourcePages': [10], 'text': '［c］バックアップに対応したストレージ'},
}
case['bodyPageMap'] = [
    {'page': 6, 'start': '次の問1は必須問題です。', 'end': '図1 C社及びP社のネットワーク構成（抜粋）'},
    {'page': 7, 'start': 'C社FW1，FW2及びP社FW3の許可ルール', 'end': 'R主任は要請に従った。'},
    {'page': 8, 'start': '［セキュリティインシデントの調査］', 'end': 'とR主任へ報告した。'},
    {'page': 9, 'start': '［暫定対応及びシステムの復旧］', 'end': '作成してもらった運用ルールが適切であることを確認する。'},
    {'page': 10, 'start': '・項番2の対策として', 'end': '対策案は承認された。'},
]
case['rubricNotice'] = '確認ポイントは学習用に独自作成したものです。IPAの公式配点・部分点基準ではありません。'
case['author'] = '/root/author_subject_b_pilot'
case['authoringStatus'] = 'awaiting-independent-review'

answers = {
    ('q1', 'answer'): (['デジタルフォレンジックス'], 'exactText',
        '下線①は，事故に関係する電磁的記録を証拠として保全し，調査・分析する行為を指す。これはデジタルフォレンジックスである。本文のネットワーク遮断やPCの使用停止という要請も，調査対象の記録を保全するための対応として読める。',
        ['電磁的記録を証拠として保全し，調査・分析する方法を特定する。', '片仮名の名称を12字以内で答える。'], ['underline-1']),
    ('q2', 'a'): (['オ'], 'exactText',
        'PC-Pでは，同じIDに対して異なるパスワードで多数回ログインを試みている。解答群では，候補となるパスワードを順に試す辞書攻撃が該当する。PC-Sに対するリバースブルートフォース攻撃は，同じパスワードを複数のIDに試す攻撃なので，PC-Pで記録された攻撃の向きと区別する。',
        ['PC-Pで同一IDに対し異なるパスワードを繰り返し試した記録を読む。', '解答群の「辞書」を選び，記号オで答える。'], ['blank-a']),
    ('q2', 'b'): (['ウ'], 'exactText',
        'PC-PからPC-Rへのログインはリモートデスクトップで行われる。表1のFW2とFW3では，P社の業務セグメントからC社の業務セグメントへのTCP/3389（RDP）が許可されている。したがって，空欄bはRDPである。',
        ['PC-PからPC-Rへのアクセス方式がリモートデスクトップであることを確認する。', '表1のTCP/3389（RDP）と対応させ，記号ウで答える。'], ['blank-b', 'table-1']),
    ('q3', 'setting'): (['ロックアウトのしきい値'], 'exactText',
        'C社の各PC・各サーバはログインのロックアウトのしきい値を5回に設定している。一方，PC-Pでは同一IDへの失敗が多数回続いた後にもログインできている。今回と同様の攻撃を抑止する変更対象は，本文にある「ロックアウトのしきい値」である。',
        ['PC-Pで多数回の失敗後もログインできた状況と，C社の5回という設定を対比する。', '本文中の設定項目名を15字以内で答える。'], ['underline-2']),
    ('q3', 'reason'): (['同一のIDで2回以上ログイン試行しないから', '同一のパスワードで異なるIDにログイン試行するから'], 'self',
        'ロックアウトのしきい値は，同一IDに対するログイン失敗が繰り返される攻撃には有効である。しかし，リバースブルートフォース攻撃では，漏えいした一つのパスワードを異なるIDに試す。同一IDで失敗を重ねないため，IDごとの失敗回数がしきい値に達する前に，そのパスワードを使うIDへログインされるおそれがある。IPAの採点講評も，同一IDで2回以上試行しないことを理由に挙げている。',
        ['同一パスワードを異なるIDに試す攻撃，または同一IDで2回以上試さないことを説明する。', '同一IDの失敗回数を増やさないため，ロックアウトが防御にならないという関係を説明する。', '「同一」を用い，25字以内で答える。'], ['underline-2']),
    ('q4-1', 'answer'): (['暗号化されたデータで上書きされている。'], 'self',
        '前日の日曜日にデータが暗号化されていたなら，月曜日の午前0時30分～午前1時30分に実施するフルバックアップには暗号化後のデータが保存される。NASは1世代分だけ保存し，次世代のデータを前世代に上書きするため，復旧用バックアップが暗号化されたデータで上書きされていたおそれがある。NASへ直接侵入して暗号化する別のリスクと，この上書きの事象を区別する。',
        ['前日の暗号化後に，月曜日のフルバックアップが行われる時系列を確認する。', 'バックアップが暗号化されたデータで上書きされる事象を述べる。', 'バックアップデータに起きた事象として，30字以内で答える。'], ['underline-3', 'table-2']),
    ('q4-2', 'answer'): (['古い記録のログが上書きされるから'], 'self',
        '各機器のログは機器内部に保存され，サイズが最大値に達すると最も古い記録から上書きされる。大量の攻撃で記録量が増えれば，過去の事象に関するログが上書きされ，調査に必要な記録を参照できなくなる。攻撃による機器故障などを仮定するのではなく，本文のログ保存条件から理由を答える。',
        ['大量の攻撃によるログ記録の増加と，最大サイズ到達後の上書き設定を結び付ける。', '古いログが上書きされることを調査不能の理由として，20字以内で答える。'], ['underline-4', 'table-2']),
    ('q5', 'c'): (['ア'], 'exactText',
        'イミュータブルバックアップでは，書き込んだバックアップデータを変更できないストレージを使い，攻撃による書換えや暗号化から保護する。差分や増分を保存する方法だけでは，保存済みデータ自体の変更は防げない。IPAの採点講評は，バックアップデータ自体が書き換えられると復旧できないことと，書込み後に変更できないストレージが有効であることを説明している。',
        ['保護対象は稼働中のデータに加えて，保存済みバックアップデータ自体であると理解する。', '書き込んだデータを変更できない方式を選び，記号アで答える。'], ['blank-c']),
}
for item in case['items']:
    if 'choices' in item:
        for index, choice in enumerate(item['choices']):
            choice['id'] = chr(ord('a') + index)
    for field in item['fields']:
        refs, method, explanation, rubric, body_refs = answers[(item['id'], field['id'])]
        field.update(referenceAnswers=refs, grading={'method': method}, explanation=explanation, rubric=rubric)
        field['evidence'] = {'bodyRefs': body_refs, 'questionPages': item['sourcePages'], 'officialAnswerPage': 1}
        if item['id'] in ['q3', 'q5']:
            field['evidence']['officialCommentaryPage'] = 1
        if 'choices' in item:
            field['choices'] = item['choices']
            field['selection'] = {'mode': 'exact', 'count': 1}
    item.pop('choices', None)
dump('case.json', case)

# Keep independent review input answer-free; enrich it only with the same source text/figures.
blind = {k: v for k, v in case.items() if k not in ['rubricNotice', 'author', 'authoringStatus']}
blind['sourceRefs'] = [u for u in blind['sourceRefs'] if not u.endswith(('_ans.pdf', '_cmnt.pdf'))]
blind['items'] = json.loads(json.dumps(case['items']))
for item in blind['items']:
    for field in item['fields']:
        for key in ['referenceAnswers', 'grading', 'explanation', 'rubric', 'evidence']:
            field.pop(key, None)
dump('blind.json', blind)

evidence = {
    'caseId': case['id'], 'version': 1, 'author': case['author'], 'status': 'draft',
    'recordType': 'author-source-evidence', 'createdAt': datetime.now(timezone.utc).isoformat(),
    'officialIndexUrl': 'https://www.ipa.go.jp/shiken/mondai-kaiotu/2025r07.html',
    'officialSources': [], 'images': [],
    'method': {
        'download': 'curl -L --fail; official PDF links read from the saved IPA index HTML.',
        'pageSelection': 'Located Question 1 by rendering PDF pages. Question 1 is PDF pages 6–10, matching printed page numbers 6–10.',
        'render': 'PyMuPDF 1.26.6 / MuPDF 1.26.11, get_pixmap(matrix=fitz.Matrix(2,2)); full page, opaque RGB PNG. Question PDF has no text layer.',
        'read': 'Author opened question-p06.png through question-p10.png with view_image and read their content. Author also opened official-ans-p01.png and official-cmnt-p01.png. Initial 1x locator images were removed after page identification.',
        'transcription': 'Manual transcription from rendered page images. Paragraphs replace paper-width line breaks. ++...++ preserves underlining; [a/b/c] blanks use full-width brackets. Figure 1 is retained as a pixel crop. Table 1 and Table 2 are transcribed as Markdown tables. No third-party explanation was consulted.',
        'figureCrop': 'Pillow crop of the already rendered question-p06.png; rectangle [102,1004,976,1360] in rendered pixels, includes figure, FW note and caption.',
        'answers': 'Read official IPA answer-example PDF page 1 image. Preserve all listed examples; typography spaces around Latin characters/digits are removed. Only official examples are registered, with no authored alternative accepted answers.',
        'rubric': 'Each field has 2–3 independently authored learning points, informed by question conditions and official answer/commentary. These are not official partial-credit criteria.',
        'review': 'No independent review performed or review record created by this author. Awaiting parent /root independent source review.',
    },
    'authorNotes': [
        'Question 1 has 6 items and 8 fields: 1 + 2 + 2 + 1 + 1 + 1. Question 4 is split into (1) and (2) items.',
        'Short term/setting/choice fields use exactText. All explanation sentences use self; no keyword or similarity-based automatic marking is provided.',
        'No full mock exam was created. This is one official-question draft for a self-evaluation pilot.',
        'body.md and body in case.json cover the entire common passage. sourceImages keep every original paragraph, diagram, table, condition and item prompt; image fidelity remains available even if Markdown layout differs.',
        'Network figure alt text is an accessibility description, not a substitute for the faithful source figure.',
        'case.json, blind.json and sourceEvidence.json are drafts, not publication/review authorization.',
    ],
    'files': {}
}
for kind, suffix, pages in [('question', 'qs', [6,7,8,9,10]), ('answer', 'ans', [1]), ('commentary', 'cmnt', [1])]:
    path = HERE / f'2025r07h_ap_pm_{suffix}.pdf'
    evidence['officialSources'].append({'kind': kind, 'url': base + path.name, 'path': str(path.relative_to(REPO)), 'sha256': sha(path), 'pagesRead': pages})
image_paths = list((REPO / 'assets/written/ap-r07h-pm1').glob('*.png')) + [HERE / 'official-ans-p01.png', HERE / 'official-cmnt-p01.png']
for path in sorted(image_paths):
    im = Image.open(path)
    record = {'path': str(path.relative_to(REPO)), 'sha256': sha(path), 'width': im.width, 'height': im.height, 'openedByAuthor': True}
    if path.name.startswith('question-p'):
        record.update(pdf='2025r07h_ap_pm_qs.pdf', pdfPage=int(path.stem[-2:]), printedPage=int(path.stem[-2:]), matrix=[2,2], rectangle='full-page')
    elif path.name == 'figure-1.png':
        record.update(sourceImage='assets/written/ap-r07h-pm1/question-p06.png', rectanglePixels=[102,1004,976,1360])
    else:
        record.update(pdf=f"2025r07h_ap_pm_{'ans' if 'ans-' in path.name else 'cmnt'}.pdf", pdfPage=1, matrix=[2,2], rectangle='full-page')
    evidence['images'].append(record)
for name in ['official-index.html', 'body.md', 'blind.json', 'case.json']:
    evidence['files'][name] = sha(HERE / name)
evidence['canonicalCaseSHA256'] = hashlib.sha256(json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
dump('sourceEvidence.json', evidence)
print('Wrote draft case.json, answer-free blind.json, author-only sourceEvidence.json.')
print('Fields:', sum(len(item['fields']) for item in case['items']))
print('Case canonical SHA256:', evidence['canonicalCaseSHA256'])
for item in case['items']:
    for field in item['fields']:
        if field.get('maxLength'):
            print(item['id'], field['id'], 'lengths', [len(a) for a in field['referenceAnswers']], 'limit', field['maxLength'])
