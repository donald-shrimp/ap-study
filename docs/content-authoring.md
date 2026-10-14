# 資格と問題を増やす

単一選択・複数選択なら、画面のJavaScriptを変更せず「資格設定＋作成元JSON」から公開用ファイルを生成する。実際の資格と原本が決まった後、少数の独立確認済み問題から登録する。

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
| `type` | `singleChoice`／`multipleChoice`。記述式は草稿保管だけ（下記参照） |
| `packId`, `packLabel` | 任意。省略時は `study`／学習問題。春秋・年度・80問に限定しない |
| `number`, `title`, `topicId` | 番号とタイトルは任意（順番と「問題N」で補完）。分野が1つなら分野IDも補完 |
| `stem` または `sourceImages` | 正確な問題文、または原本画像。画像の場合 `imageSizes` に幅と高さ |
| `choices` | 2〜20個。各選択肢は安定した `id`、表示 `label`、`text`／`image` |
| `correctChoiceId`／`correctChoiceIds` | 単一選択の正答ID／複数選択の正答ID配列。選択肢順とは別に参照する |
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

- 公開資格が1つなら直接学習画面へ進む。資格数に関係なく、ヘッダーの現在の資格名から一覧へ移動できる。
- トップ `/ap-study/` とPWAの起動では、同じブラウザで最後に開いた公開資格を開く。初回や登録解除済みの資格なら一覧を表示する。`?qualifications` は明示的に一覧を開くURL。
- `<資格ID>/` の直リンクは前回設定より優先する。前回の資格だけを端末のlocalStorageへ保存し、学習記録の資格別保存やFirebase同期形式は変更しない。
- 一覧の表示だけでは学習を開始しない。資格切替前に学習記録と保存待ちのメモ・計画を保存する。入力中の計画は保存／取り消しを案内し、保存できなければ今の画面を維持する。
- オフラインでは取得済みの資格と問題を使う。未取得の教材を利用できるとは保証しない。PWAのIDとスコープは全資格で共通の `/ap-study/` を維持する。

追加後は `tests/qualifications.py` で資格間の同名問題ID・記録・中断の分離、切替・再起動・保存失敗・オフラインを確認する。診断の入口条件は `node --test tests/qualification-features.mjs`。テスト用資格は公開しない。

現行のAP専用 `tests/corpus.py` は収録800問・公式正解・画像・教材確認を維持する。別資格には、その原本・正答・レビュー記録を照合する資格固有のチェックを追加する。公開時は最新main・教材保持・生成ハッシュ・ブラウザ・公開ファイルの一致を確認する。

2026-10-14、第二資格AB-730を174問で登録。`tests/content.py`・`tests/qualifications.py` の架空問題は一時ディレクトリだけに生成する。


## 共通の教材契約（2026-10-13）

[読みやすい実装概要](common-foundation.html)。新しい資格は `qualification.json` と各作成元JSONで追加し、共通画面へ資格IDの分岐を加えない。公開対象はAPとAB-730。非公開の合成テスト教材を実資格の問題として使わない。

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

単一選択と複数選択に対応。記述式は採点保留の草稿のみ。並べ替え・ケース内複数設問は未対応。新しい形式を公開するときは、生成検証→表示→採点→スナップショット検証→Rules→バックアップ／AI Exportを同時に拡張する。単一選択の配列へ無理に押し込まない。

## 問題形式と複数ファイルの取り込み（2026-10-14）

新しい一般教材の形式契約は [question-format.v1.json](../schemas/question-format.v1.json)。既存AP作成元の省略項目は従来のadapterで補完する。問題の `type` と採点方法 `grading.method` は別に保存する。公開用の選択問題は `exactChoiceSet`（正答の組み合わせの完全一致）を使い、部分点は付けない。単一選択で採点方法を省略した既存教材は、この方法として扱う。

| `type` | 作成元JSON | 今回の対応範囲 |
|---|---|---|
| `singleChoice` | `choices` と `correctChoiceId` | 通常学習・診断・模試・保存・同期・AI |
| `multipleChoice` | `choices` と `correctChoiceIds`、`selection` | 同上。チェックボックスで選び、回答ボタンで確定 |
| `freeText` | `referenceAnswer`、`grading: {"method":"deferred"}` | 未確認草稿の保管だけ。受験・正誤判定・公開生成にはまだ使えない |

```json
{
  "id": "stable-question-id",
  "version": 1,
  "type": "multipleChoice",
  "stem": "当てはまるものを2つ選んでください。",
  "choices": [
    {"id": "a", "label": "ア", "text": "選択肢A"},
    {"id": "b", "label": "イ", "text": "選択肢B"},
    {"id": "c", "label": "ウ", "text": "選択肢C"}
  ],
  "correctChoiceIds": ["a", "c"],
  "selection": {"mode": "exact", "count": 2},
  "grading": {"method": "exactChoiceSet"}
}
```

「すべて選択」は `selection: {"mode":"all"}`。正答が1つでも、チェックボックスで複数を選べる設問なら `multipleChoice` とする。`exact.count` は正答数と一致する必要がある。指定数より少ない／多い状態では回答ボタンを無効にする。選択解除は常に可能。余分な選択・選び忘れは不正解。表示順とクリック順を区別し、正答・本人の選択配列は選択肢の表示順へ揃える。

複数選択の作成元へ `correctChoiceId` や数値 `answer` を混在させない。生成時には既存共通処理用の `answer:null` を補い、正答配列・選択条件・採点方法を軽量索引にも保存する。既存APの数値正答と単一選択の保存形式は維持する。選択途中と確定済みの履歴は `selectedChoiceIds` を使う。診断・模試では `currentChoiceId` と `responses[slotId]` が複数選択の場合だけ配列になり、単一選択の文字列／未回答のnullを保持する。

Schemaに加え、ビルダーで正答IDが登録済み選択肢に属すること、ID・配列の一意性、指定数と正答数の一致、対応する採点方法、作成元と補完後の確認ハッシュを照合する。公開する一般教材には従来どおり別担当の内容確認・全選択肢理由が必要。未確認草稿を `reviewed` へ自動昇格させない。

### HTMLを追加する手順

```sh
python tools/import-question-drafts.py \
  --qualification ab730 \
  --collection supplied-originals \
  --output /workspace/scratch/ab730-question-imports \
  incoming/第1回_模擬問題.html incoming/第2回_模擬問題.html
```

今後も同じ資格・同じ `collection`・同じ出力先を指定してファイルを追加する。各 `article.question` の `.qhead small` または `data-question-id` を安定した出典コードとして使用し、IDを作る。出典コードが再利用される別シリーズなら新しいcollectionを指定する。コードがない場合はファイル名を識別に使うため、改名を確認事項として残す。

- `manifest.json`：元ファイルSHA-256・出典コード・問題ID・草稿の版一覧・重複候補・改訂競合・未確認件数。
- `drafts/<問題ID>/<草稿ハッシュ>.json`：本文・形式・提供正答と解説・参照URL・変換内容・要確認事項。すべて `unreviewed` で、アプリの公開問題には入らない。
- `sources/<SHA-256>.html.txt`：元のHTMLをそのまま保存。スクリプトは実行せず、静的な要素だけを抽出する。

同じバイト列のファイルは再取り込みを省略。同じ出典コードで内容が変わったら、元の草稿を保持して新しい版と競合を追加する。本文・選択肢が同じ別コードの問題は、選択肢順が違っても重複候補にする。意味が近い問題や言い換えの重複は自動判定を保証しない。正答・出典の正しさも、この取り込みだけでは保証しない。

`br` と段落を残し、radio／checkboxを区別。提供資料で確認できた注意書きの選択肢への混入は、本文へ移して正答位置を補正し、変換記録を残す。手動表示の選択肢も提供正答と一意に文字一致する場合だけ単一選択へ復元する。これは内容レビューではない。明示的な `data-type="freeText"` は採点保留の草稿として保存。表・画像・未知の形式・選択数不一致などは要確認の草稿に残す。取り込み先の資格やcollection不一致・同一コードの二重掲載・未対応のHTML全体はエラーにし、既存台帳を書き換えない。

形式整備時点の提供AB-730抽出記録は124問（単一111・複数13）、内容確認済み・アプリ公開はいずれも0問。共通形式整備の時点では添付HTML原本は存在せず、前回の抽出記録を `content/ab730/question-drafts/previous-extraction.json` に保持している。その時点の取り込み機能の検証は同構造の合成HTMLで行い、124問を再解析・内容確認したとは記録していない。完全版の教材化は下記を参照。対象版・分類・正答の資料確認・各選択肢理由を整えてから、少数の確認済み教材を資格設定へ登録する。

取り込みCLIはPython標準ライブラリのみ。Schema検証テストには `jsonschema`、ブラウザテストには既存のPlaywright／Chromium、同期テストにはFirebase SDK／Emulatorを使用する。

検証：`python tests/question-import.py`、`python tests/question-type-content.py`、`node --test tests/question-types.mjs`、`python tests/question-type-flow.py`。Firebase Rulesの複数選択はEmulatorで確認し、本番公開はFirebaseコンソールで別途必要。古いアプリは新形式の記録を受け取れないため、複数選択の本番教材を追加する前に各端末のアプリを更新する。


### AB-730完全版と確認済み教材の登録（2026-10-14）

完全版の `script#dataset[type="application/json"]` から187問を抽出。本文と選択肢をHTML化して既存抽出器へ渡し、埋め込みレンダラーは実行しない。`sourceId`を出典コードに使うため、画面のランダム順・GUI番号が変わっても同じ問題を識別する。JSON型・選択肢ID・提供正答の参照・一意性を検査する。この静的抽出は内容承認ではない。

`content/ab730/intake/imports/` は提供原本と未確認抽出を保持し、`authoring/authoring-map.json` が抽出IDと公開ID `ab730-qN-N` をつなぐ。前回124問は完全版に含まれるので再登録せず、新規出典コード63問を区別した。提供元の重要度注記を回答候補から除く処理、製品仕様・設問・正答・全選択肢理由の訂正は、作者の差分記録と独立確認記録を保存して行った。

提供正答と作者草稿を見る前の独立解答→公式資料本文の照合→完成教材と全候補理由の確認→修正後の再確認を実施。187問を分類し、177問を承認、根拠不足10問は草稿、承認済みの意味重複3問は除外。174問を公開した。`progress.json` に実数、保留理由と次の確認対象を保存。全問の文字化や公式試験問題の再現とは扱わない。

```sh
python tools/curate-reviewed-content.py --qualification ab730 \
  --drafts content/ab730/authoring/author-drafts.json \
  --reviews content/ab730/authoring/reviewer/final-reviews.json \
  --exclusions content/ab730/authoring/publication-exclusions.json --register
python tools/build-content.py
python tests/ab730-content.py
python tests/ab730-flow.py
python tests/ab730-sync.py
```

昇格ツールは独立確認・承認状態・完成作成元と公開補完後の両ハッシュ・読んだ資料の保存ハッシュを照合し、非除外の未承認問題があれば登録を止める。確認記録は自動生成しない。抽出草稿は未確認のまま保存し、修正した別レコードの確認を偽って流用しない。追加ファイルは同じcollectionへ取り込み、改訂競合・意味重複・承認ハッシュを再確認する。公開問題のIDは変えない。本文変更の際は版を増やす。

AB-730は4つの学習分野、単一157／複数17。分野均等の30問診断は公式試験の出題比率を再現するものではない。ヒント・紙ペン分類・カード・固定模試は未提供のため入口を作らない。日本語試験への新版適用日は未確認で、教材版は公式資料の確認日を示す。年度／春秋のない資格では該当フィルターを表示しない。
