# 資格と問題を増やす

同じ単一選択なら、画面のJavaScriptを変更せず「資格設定＋作成元JSON」から公開用ファイルを生成する。実際の資格と原本が決まった後、少数の独立確認済み問題から登録する。

## 応用情報の既存教材を更新する

1. `data/lessons/<回>.json` に解説・各選択肢の理由・段階ヒントを保存する。
2. 別担当が原本と公式正解から解き直し、`data/lesson-reviews/` の根拠・指摘と対応・完成教材ハッシュを更新する。
3. `python tools/apply-hints.py` を実行する。作成元の `data/questions.json` と資格別パック・入口を再生成する。
4. `python tests/corpus.py` と `python tests/content.py`、内容に必要な独立検算、学習・PWAテストを実施する。

原本画像・公式解答・出典・確認記録は従来の場所を使う。生成したパックを直接編集して作成元と食い違わせない。

## 新しい資格を登録する

`content/<資格ID>/qualification.json` を作成し、`content/qualifications.json` の `qualifications` 配列へIDを追加する。資格ID・問題ID・パックID・分野ID・選択肢IDは、英数字で始まる100文字以下の英数字・`_`・`-`。表示名・公開年・公開パスを変えても識別IDを変更しない。

```json
{
  "id": "exam-id",
  "name": "資格の正式名",
  "shortName": "表示名",
  "questionSource": "content/exam-id/questions.json",
  "sourceLabel": "問題の出典元",
  "sourceDoc": "docs/SOURCES.md",
  "sourceDescription": "収録範囲と出典・改変内容",
  "topics": [{"id": "stable-topic", "name": "分野の表示名"}]
}
```

`exam-id` と資格名・分野・出典は、対象に合わせて変更する。応用情報の `storageKey`・`adapter` は既存形式のための設定なので、他資格には付けない。

作成元は問題オブジェクトの配列。必要な項目は以下のとおり。

| 項目 | 内容 |
|---|---|
| `id`, `version` | 資格内で一意の問題ID、正の整数の版。内容を改訂したら版を増やす |
| `type` | `singleChoice`。未対応の形式は拒否する |
| `packId`, `packLabel` | 追加の単位と表示名。春秋・年度・80問に限定しない |
| `number`, `title`, `topicId` | 正の問題番号、タイトル、設定に登録した分野ID |
| `stem` または `sourceImages` | 正確な問題文、または原本画像。画像の場合 `imageSizes` に幅と高さ |
| `choices` | 2〜20個。各選択肢は安定した `id`、表示 `label`、`text`／`image` |
| `correctChoiceId` | 正答の選択肢ID。配列を並べ替えても正答参照を保つ |
| `hints` | 1〜20段階。各段階は `title`、具体的な `text`、`revealsAnswer`（真偽値） |
| `summary`, `explanation`, `takeaway` | 要約、問題固有の解説、要点 |
| `choiceReasons` | 個別解説付きなら選択肢と同数。各選択肢の正誤理由 |
| `enrichment`, `hintStatus` | 確認済み解説は `reviewed`。個別ヒントは `individual` |
| `source` | 出典名・回・問番号。必要に応じて `questionUrl`, `answerUrl` |
| `related` | 同じ資格内の関連問題ID配列。未登録の参照は拒否する |

画像の作成元パスはリポジトリルート相対で、実ファイルが必要。外部URLやリポジトリ外の画像を参照しない。出典URLと第三者資料の扱いも確認する。未確認の教材を `reviewed` として登録しない。この共通生成ツールは内容の独立レビューを自動保証しない。

```sh
python tools/build-content.py
python tests/content.py
python tests/qualifications.py
python tests/storage.py
python tests/e2e.py
python tests/pwa.py
```

資格別入口は `<資格ID>/index.html`、公開データは `data/qualifications/<資格ID>/` へ生成する。問題追加は作成元へ追加するだけで一覧・件数・パックを再生成できる。`templates/study.html` が共通画面の入口なので、生成済みHTMLを個別に修正しない。

現行のAP専用 `tests/corpus.py` は収録800問・公式正解・画像・教材確認を維持する。別資格には、その原本・正答・レビュー記録を照合する資格固有のチェックを追加する。公開時は最新main・教材保持・生成ハッシュ・ブラウザ・公開ファイルの一致を確認する。

第二資格の本番教材は未登録。`tests/content.py`・`tests/qualifications.py` の架空問題は一時ディレクトリだけに生成する。
