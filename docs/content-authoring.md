# 資格と問題を増やす

同じ単一選択なら、画面のJavaScriptを変更せず「資格設定＋作成元JSON」から公開用ファイルを生成する。実際の資格と原本が決まった後、少数の独立確認済み問題から登録する。

## 応用情報の既存教材を更新する

1. `data/lessons/<回>.json` に解説・各選択肢の理由・段階ヒントを保存する。
2. 別担当が原本と公式正解から解き直し、`data/lesson-reviews/` の根拠・指摘と対応・完成教材ハッシュを更新する。
3. `python tools/apply-hints.py` を実行する。作成元の `data/questions.json` と資格別パック・入口を再生成する。
4. `python tests/corpus.py` と `python tests/content.py`、内容に必要な独立検算、学習・PWAテストを実施する。

原本画像・公式解答・出典・確認記録は従来の場所を使う。生成したパックを直接編集して作成元と食い違わせない。

## 新しい資格を登録する

原本画像をテキスト表示に切り替える場合は [文字起こし手順](transcription-authoring.md) を参照する。数式・表・コード・下線を含む限定形式を `stem` と選択肢の `text` に保存し、`python tools/apply-transcriptions.py` で別担当確認済みの内容だけを反映する。生成済みパックを直接編集しない。解説と正答はこの作業で変更しない。

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
| `packId`, `packLabel` | 任意。省略時は `study`／学習問題。春秋・年度・80問に限定しない |
| `number`, `title`, `topicId` | 番号とタイトルは任意（順番と「問題N」で補完）。分野が1つなら分野IDも補完 |
| `stem` または `sourceImages` | 正確な問題文、または原本画像。画像の場合 `imageSizes` に幅と高さ |
| `choices` | 2〜20個。各選択肢は安定した `id`、表示 `label`、`text`／`image` |
| `correctChoiceId` | 正答の選択肢ID。配列を並べ替えても正答参照を保つ |
| `hints` | 任意、0〜20段階。各段階は `title`、具体的な `text`、`revealsAnswer`（真偽値） |
| `summary`, `explanation`, `takeaway` | 要約・要点は任意。確認済み教材には問題固有の解説が必須 |
| `choiceReasons` | 個別解説付きなら選択肢と同数。各選択肢の正誤理由 |
| `enrichment`, `hintStatus` | 確認済み解説は `reviewed`。個別ヒントは `individual` |
| `source` | 任意の出典表示。必要に応じて `questionUrl`, `answerUrl`, `sourceRefs` |
| `related` | 任意。同じ資格内の関連問題ID配列。分野をまたげるが未登録の参照は拒否する |

画像の作成元パスはリポジトリルート相対で、実ファイルが必要。外部URLやリポジトリ外の画像を参照しない。出典URLと第三者資料の扱いも確認する。未確認の教材を `reviewed` として登録しない。確認済みとして登録する一般教材には `questionReviewSource` または `assessmentReviewSource` が必須。ハッシュと確認記録の一致は検査するが、独立確認が実際に行われたかは作成・確認の記録に基づいて判断する。

```sh
python tools/build-content.py
python tests/content.py
python tests/qualifications.py
python tests/storage.py
python tests/e2e.py
python tests/pwa.py
```

資格別入口は `<資格ID>/index.html`、公開データは `data/qualifications/<資格ID>/` へ生成する。問題追加は作成元へ追加するだけで一覧・件数・パックを再生成できる。`templates/study.html` が共通画面の入口なので、生成済みHTMLを個別に修正しない。

## 資格ごとの入口と切替

少数の確認済み問題から通常学習を公開できる。未提供の機能を準備中のボタンとして並べない。

| 入口 | 表示の条件 |
|---|---|
| 通常学習・分野・記録・計画 | 資格の公開問題があること。紙ペン分類がなければ「おまかせで1問」から開始 |
| 身軽に1問・書いて考える1問 | 資格に `studyContext` の教材分類があること |
| 実力診断 | `diagnosticBlueprint.size` を30〜200で設定し、通常／専用の確認済み教材で指定配分・派生上限・ファミリー重複回避を満たすこと |
| 模試 | 確認済みの固定模試セットが登録されていること |
| 単語帳 | 資格別のカード教材が登録されていること |

診断の配分は登録した分野を使う。派生問題は必須ではない。診断が未提供ならホーム・記録の入口と新規開始を無効にするが、すでに保存された診断の再開・結果は残す。診断は30〜200問、固定模試はセットごと1〜200問。APは診断30問・模試80問を維持する。10問診断は提供しない。開始時に問題・配分・対象版・問題数を保存し、後の設定変更で再抽出や採点変更をしない。模試セットの問数変更・公開終了後も、保存済みの再開・結果と記録の入口を残す。

- 公開資格が1つなら直接学習画面へ進む。2つ以上になったら、上部の資格名から一覧へ移動できる。
- トップ `/ap-study/` とPWAの起動では、同じブラウザで最後に開いた公開資格を開く。初回や登録解除済みの資格なら一覧を表示する。`?qualifications` は明示的に一覧を開くURL。
- `<資格ID>/` の直リンクは前回設定より優先する。前回の資格だけを端末のlocalStorageへ保存し、学習記録の資格別保存やFirebase同期形式は変更しない。
- 一覧の表示だけでは学習を開始しない。資格切替前に学習記録と保存待ちのメモ・計画を保存する。入力中の計画は保存／取り消しを案内し、保存できなければ今の画面を維持する。
- オフラインでは取得済みの資格と問題を使う。未取得の教材を利用できるとは保証しない。PWAのIDとスコープは全資格で共通の `/ap-study/` を維持する。

追加後は `tests/qualifications.py` で資格間の同名問題ID・記録・中断の分離、切替・再起動・保存失敗・オフラインを確認する。診断の入口条件は `node --test tests/qualification-features.mjs`。テスト用資格は公開しない。

現行のAP専用 `tests/corpus.py` は収録800問・公式正解・画像・教材確認を維持する。別資格には、その原本・正答・レビュー記録を照合する資格固有のチェックを追加する。公開時は最新main・教材保持・生成ハッシュ・ブラウザ・公開ファイルの一致を確認する。

第二資格の本番教材は未登録。`tests/content.py`・`tests/qualifications.py` の架空問題は一時ディレクトリだけに生成する。


## 共通の教材契約（2026-10-13）

[読みやすい実装概要](common-foundation.html)。新しい資格は `qualification.json` と各作成元JSONで追加し、共通画面へ資格IDの分岐を加えない。公開対象はまだAPのみ。非公開の合成テスト教材を実資格の問題として使わない。

### 用途と由来を分ける

- `uses`: `practice`／`diagnostic`／`mock` の重複のない配列。省略時は通常学習＋診断。固定模試には `mock` の明示が必要。
- `sourceKind`: `official`／`authored`／`derived`。一般教材の省略時は独自問題（親があれば派生）。AP公式原本は公式問題として扱う。
- `parentQuestionId`: 実際の派生だけ必須。独自問題・公式問題へ架空の親を付けない。親は同じ資格・分野・パートの非派生問題。
- `familyId`: 同じ理解を問う同等問題をまとめたい場合だけ設定。同じ主分野・パートに属する問題をまとめる。省略時は親IDまたは自分のID。診断・模試内で同じファミリーを重複させない。

通常教材は `questionSource`、受験専用教材は `assessmentQuestionSource` と `assessmentReviewSource` へ保存する。専用教材の `uses` に `practice` は含めない。専用バンクは通常の検索・復習へ混入させない。公式問題も用途を限定でき、独自問題を普段の学習に使うこともできる。AP作成元の既存フラグは生成時に用途へ変換するが、新しい教材には `uses` を使う。

### 版・言語・出題目標は任意

資格設定の `syllabuses` は `{id,label,language,effectiveFrom?,effectiveTo?}` の配列。`defaultSyllabusId` は新規教材の既定値。言語は `ja-JP` 等。日付は正式な適用日が確認できた場合だけ登録し、推測で入れない。

`objectives` は `{id,label,topicId}` の配列。問題には `syllabusId`、`language`、`objectiveIds`、`sourceRefs` を任意に設定する。参照は登録済みID／HTTP(S)のURLだけを許可する。生成時に版の表示名・言語・出題目標の表示名も問題へ保存し、履歴・再開・AI Exportでは開始時の値を使用する。対象版が変わっても過去の受験を新しい版として読み替えない。

出題目標と主分野は別の概念。同じ問題から複数目標へ関連付けてよい。単語帳の `relatedQuestionIds` と `sourceNote` も任意で、別分野の通常問題へ関連付けられる。

### 出題設定

```json
{
  "diagnosticBlueprint": {
    "size": 40,
    "sampling": "topic-weighted",
    "weights": {"foundation": 3, "application": 1},
    "defaultVariantLimit": 1
  }
}
```

均等巡回は `topic-round-robin`（省略時も同じ）。重み付きは正の整数の相対比を指定し、最大剰余法で整数の問題数に配分する。同率なら分野IDのASCII順。設定した分野ごとの必要数を満たせなければ診断を開始しない。別分野への無言の補填は行わない。`variantLimits` は分野別に派生上限を上書きする。独立した独自問題は派生上限の対象外。

未見の専用教材→未見の通常教材→既見の専用教材→既見の通常教材を優先。元問題／ファミリーの重複を避ける。診断と模試は常に支援なし・終了後採点。模試は `mockSetSource` の `size` と `slots` で固定する。配列数・順序・ファミリーの一意性と用途を照合する。

### 確認記録と生成

一般教材で `reviewed` にするには、別担当が問題・正答・全選択肢理由・語調を確認し、計算があれば検算する。確認レコードは次の形式。

```json
{
  "questionId": "stable-question-id",
  "version": 1,
  "sha256": "作成元オブジェクトのcanonical JSON SHA-256",
  "normalizedSha256": "公開用補完後の最終オブジェクトのcanonical JSON SHA-256",
  "author": "実際の作成担当",
  "reviewer": "実際の別確認担当",
  "checkedAt": "2026-10-13T00:00:00Z",
  "checks": {"source": true, "answer": true, "choices": true, "wording": true, "calculation": "not-applicable"},
  "notes": "確認根拠、指摘と対応、再確認内容"
}
```

canonical JSONはUTF-8・キーソート・空白なし・Unicode文字をそのまま保存（`diagnostic_digest`）。最終オブジェクトは `normalize(raw, config, ordinal)` で取得する。親に明示ファミリーがあれば派生へ同じ値を補完した後にハッシュ化。既定版・分野名・出題目標名など設定由来の変更も最終ハッシュで検知する。修正後は再確認し、版と両ハッシュを更新する。APは既存の原本・教材・図の確認手順を保つ。

`python tests/common-content.py`、`node --test tests/common-assessment.mjs`、`python tests/common-flow.py` は合成教材だけで共通契約を検証する。実教材の内容レビューの代替にはならない。Firebase Rulesも診断30〜200問／模試1〜200問と保存件数・回答範囲を検証する。Rulesの本番公開はFirebaseコンソールで別途必要。

### 新しい問題形式を増やすとき

現在は `singleChoice` のみ。複数選択・並べ替え・ケース内複数設問は未対応。必要になったら、生成検証→表示→採点→スナップショット検証→Rules→バックアップ／AI Exportを同時に拡張する。単一選択の配列へ無理に押し込まない。
