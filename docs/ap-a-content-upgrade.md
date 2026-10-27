# 科目A 800問のヒント・解説改訂

対象は応用情報・科目Aの既存800問。ヒント2,400件・選択肢別理由3,200件を、解説・要約・要点と一緒に現在の基準で確認する。十分な文章は残す。旧レビューを新基準での承認に読み替えない。

品質の正本は [ヒントの共通ルール](hint-authoring.md)と[解説記述ルール](explanation-authoring-rules.md)。この文書はAPの保存・担当分割・受け入れ手順だけを定義する。3段構成は既存APの契約であり、全問同じ説明配分や文量にする指示ではない。

## 計画と担当

1. 800問のID・旧版・分野・作成元・原本・旧レビューを固定し、担当と進捗を追跡する。
2. 改稿と独立確認の契約、旧版保存、決定的な版更新、公開用生成物への混入防止を整備する。
3. 17分野を含む先行20問を改稿・別担当確認し、実アプリで表示・評価・記録を確かめる。
4. 残り780問は20問×39組。各組の作者と確認者を分け、同じ公開用ファイルへ並列で書き込ませない。
5. 統合担当が確認済みの組を順次取り込み、確認済み80問を目安に公開する。先行20問の作業完了と全800問の完了は区別する。

[全800問と40組の入口](../work/ap/objective-quality/README.md)から担当を選ぶ。`pilot-00`は先行20問、`batch-01`〜`batch-39`は残り780問。分野・概念の近い問題をまとめ、境界で複数分野を含む場合も各問の原本条件を優先する。固定台帳の機械的な候補は優先順位の参考であり、不備や承認の判定ではない。

## 保存先と作業範囲

- `work/ap/objective-quality/baseline/`：変更前の800問・年度別教材・旧レビュー・原本メタデータ。上書きしない。
- `inventory.json`：ID・旧版・分野・担当組・作成元・原本と旧教材のハッシュ。
- `batches/<組>/assignment.json`：20問の固定IDと作者・確認者。担当はclaimで記録する。
- 同じ組の `context.json`：原問・全肢・公式正答・原本画像の参照。`drafts.json`：旧教材から始める改稿。`reviews.json`：作者とは別担当の最終確認。
- `registrations.json`：統合済みの組。`progress.json`：担当・確認状態のスナップショット。初期の39組は全件未着手。

基盤がmainへ取り込まれるまでは `content/ap-a-quality-pilot` を起点に担当用の作業ブランチを作る。取り込み後は最新mainを起点にする。担当組の割当ては統合担当が調整し、既に別担当がclaimした組を取り直さない。

作者が変更するのは自分の組のassignmentとdrafts、確認者が変更するのは自分の組のreviewsと補助記録。`data/lessons/`・`data/questions.json`・生成パック・共有ルール・他の組・baselineは統合担当が扱う。未確認の組を作成元へ直接コピーしない。

```sh
python tools/ap-lesson-quality.py claim batch-01 --author '一意な実担当名'
python tools/ap-lesson-quality.py check batch-01
python tools/ap-lesson-quality.py check batch-01 --reviewed
python tools/ap-lesson-quality.py check-drafts
python tools/ap-lesson-quality.py status --write-progress
```

## 作者の納品

各組の `drafts.json` は20件のenvelope配列。各件の `id`、`baseVersion`、`baseLessonSHA256` は固定。`author` にassignmentと同じ実担当名を入れ、`decision` は未着手のpendingから、keep（本文変更不要）／revise（部分修正）／rewrite（全面改稿）へ変更する。変更量を増やす目標は設けない。

`lesson` は従来のAP教材と同じ `id`・`summary`・`explanation`・`choiceReasons`・`takeaway`・`hints`・`checkedAgainst`。各肢の順序、3段のヒント、元の問題IDを維持する。要約は論点、解説は根拠、要点は再利用できる知識とし、欄を埋めるために同じ説明を増やさない。今回のAP契約では要約・要点も既存フィールドとして保持する。

`design` は教材の表示用フィールドではなく作者の作業メモ。

| 項目 | 記録する内容 |
| --- | --- |
| obstacle | この問題で初学者が止まる具体的な理由 |
| stages（3件） | newInformation＝増える知識、remainingWork＝本人に残る判断、revealsAnswer＝該当ヒントと同じ真偽値、reason＝問題文・全肢・前段と合わせた開示判断の理由 |
| changes | 実際に変更したlessonのキー。keepでは空配列 |
| sourceNotes | 実際に開いた原本と、補助の一次資料・検算・保留の記録 |

元画像を開き、公式正答と全肢を確認する。テキストや略語の置換だけで済ませない。ヒントだけ読んだ人・解説だけ読んだ人の双方に必要な定義・式・条件が伝わるかを確認する。原問・正答・図の問題を発見した場合はIDと根拠を記録して保留し、別の修正として扱う。本人の記録を添付しない。

## 独立レビューの納品

別担当が原本から解き直し、修正後の20問・全80肢の理由・全60ヒント・解説・設計メモを読む。計算・図・単位・条件・時点を再確認する。keepも新基準での別担当確認が必要。作者がレビューを埋めたり、自分で修正した内容を自分で独立承認したりしない。

`reviews.json` の各件は次の契約とする。ハッシュはUTF-8、JSONのキーをソートし、`ensure_ascii=False,separators=(',',':')` としたSHA-256。

```json
{
  "id": "対象問題ID",
  "author": "draftの実作者",
  "reviewer": "作者とは異なる実確認者",
  "status": "approved",
  "checkedAt": "実際の確認日時（タイムゾーン付きISO形式）",
  "baseLessonSHA256": "inventory.baselineLessonSHA256",
  "reviewedLessonSHA256": "最終draft.lessonの実ハッシュ",
  "questionSHA256": "inventory.baselineQuestionSHA256",
  "sourceHashes": {"参照元パス": "inventoryと一致する実SHA-256"},
  "checks": {"source": true, "answer": true, "choices": true, "hints": true, "explanation": true, "revealFlags": true, "calculation": "not-applicable"},
  "notes": "問題固有の確認内容・根拠",
  "officialAnswer": "公式のア〜エ",
  "independentResult": "実際の解答・根拠・検算",
  "issues": []
}
```

計算を確認した場合の `calculation` はtrue。未確認をnot-applicableへ置き換えない。指摘が残る問題はapprovedを付けず、ID・指摘・根拠をレビュー補助記録に残し、作者へ返す。修正後に読み直し、最終ハッシュで承認する。機械チェックの成功は内容承認ではない。初学者による試用を実施していなければ、効果測定済みとは記録しない。

## 統合・検証

```sh
python tools/ap-lesson-quality.py check pilot-00 --reviewed
python tools/ap-lesson-quality.py accept pilot-00
python tools/apply-hints.py
python tests/ap-lesson-quality.py
python tests/corpus.py
python tests/content.py
```

acceptは20問全件の独立承認・原本と最終教材のハッシュを照合してから年度別作成元と問題バンクへ取り込む。未登録の改稿をビルドへ混ぜられない。変更した問題だけ旧版＋1とし、keepは旧版を維持する。同じ内容を再生成・再取り込みしても版は増えない。問題文・選択肢・公式正答・図・元の旧レビューは保持する。

統合後に表示・未開示情報・ヒント各段階の表示とassisted/revealed・回答後の結果保持・旧記録・オフライン・バックアップを実アプリで確認する。UIの大幅変更や記録形式の移行はこの作業へ混ぜない。生成物・CI・Pagesと公開先の実ファイル／画面を確認し、公開確認は承認件数から推測せず別途記録する。

progressのapprovedは独立承認後に登録済みの件数であり、公開済みの意味ではない。公開前の先行20問はレビュー可能なPRと検証記録へまとめ、780問は未着手の担当割りとして引き渡す。旧教材は利用できる状態を保ち、新基準の確認が終わった範囲だけを進捗として数える。

先行20問の[実アプリ検証結果](../work/ap/objective-quality/batches/pilot-00/review/browser/results.json)と[画面例](../work/ap/objective-quality/batches/pilot-00/review/browser/r07h-q52-390.png)も保存する。検証は隔離した合成記録を用い、本人の記録やアカウントを使わない。
