# FP2級：外注する教材の仕様

基盤は共通エンジンを使う。2026年5月・2025年5月公表分と2025年1月・2024年9月実施分の各学科60問・日本FP協会実技40問を独立レビュー・修正後に登録済み（計学科240問・実技160問・274欄）。収録範囲と原本は [FP2級の出典](FP2-SOURCES.md)。これは教材作成の依頼仕様であり、未確認教材の公開許可ではない。

## 外注へ渡す依頼

共通の入口は [土台づくり→各問題の作成](content-authoring.md)。新規・既存教材のヒントは [全資格共通ルール](hint-authoring.md)とその作問・レビュー手順を使い、FP固有の禁止事項や段数要件は増やさない。FP2級の土台は実装済みなので、追加する科目・試験回・問番号と既存草稿を確認して再利用する。未対応形式の改修は土台担当が行い、作者へは今回の範囲と納品先を渡す。

> 対象は〈科目ID・試験回・問番号〉、納品先は〈今回のフォルダ〉。`docs/content-authoring.md`、`docs/hint-authoring.md`、この仕様と `content/fp2/qualification.json` に合わせ、公式公表問題から教材JSONを作成してください。公開済みの2026年5月公表分や既存草稿を重複登録しないでください。原本と公式解答を保存し、各問題の本文・図表・全選択肢／全回答欄・正答・理由・問題固有の解説を作成してください。本文の表・数式・強調を保持し、推測で補完しないでください。通常の選択問題の解説はインライン太字のみ、caseの解説は既存の数式・表・コードも使えます。要約・要点は重複して埋めず、解説の重要な条件だけ`**…**`で強調してください。法令基準日は公式資料で確認できた日だけ記載し、不明ならnull。現行法令の確認根拠がなければunverified。納品はdraftで行い、レビュー担当や確認ハッシュを架空に作らず、根拠・担当・保留事項・次の対象を残してください。

一次資料： [日本FP協会の公表問題・解答](https://www.jafp.or.jp/exam/mohan/) ／ [きんざいの2級試験要綱](https://www.kinzai.or.jp/ginou/fp/2kyu/index.html)。問題の利用条件は各公開元で確認し、出典・加工内容を表示する。第三者の図・引用資料は別途扱いを確認する。検索結果やOCRだけで原文・正答を確定しない。

## 納品構成

```text
delivery/
  content/fp2/
    questions.json           # 学科の草稿配列
    practical-cases.json     # 実技の草稿配列（今回未作成なら[]）
    source-files.json        # {"sources/fp2/xxx.pdf":"完全SHA256"}
    question-reviews.json    # 作成担当の納品時は[]
    practical-reviews.json   # 作成担当の納品時は[]
  sources/fp2/               # 問題・公式解答の原本PDF
  assets/written/fp2/        # 実技で必須の図表・選択肢図（png）
  assets/fp2/                # 学科で必須の図表・選択肢画像
```

既存の公開作成元は [`content/fp2/`](../content/fp2/README.md)。構成を参照し、未確認の追加分は指定の納品フォルダに分離する。納品物に個人の学習記録を入れない。公開用 `data/qualifications/` とHTMLは編集しない。

### 科目・分野

識別子は資格設定を正本とし、後から名前や年度が変わってもIDを変更しない。

| 科目ID | 教材 | 1記録の単位 |
|---|---|---|
| `objective` | 学科 | 公式1問の選択問題 |
| `jafp-practical` | 日本FP協会・資産設計提案業務 | 原則として公式1問を1case |
| `kinzai-personal` | きんざい・個人資産相談業務 | 1設例を1case、小問をitems |
| `kinzai-business` | きんざい・中小事業主資産相談業務 | 同上 |
| `kinzai-life` | きんざい・生保顧客資産相談業務 | 同上 |
| `kinzai-nonlife` | きんざい・損保顧客資産相談業務 | 同上 |

分野ID：`life-planning`、`risk-management`、`financial-assets`、`tax`、`real-estate`、`inheritance`。

問題ID例：`fp2-202605-objective-q01`。実技は `fp2-202605-jafp-q01`。版は`version:1`から始め、本文・正答・基準日・現行法令の確認情報を改訂したら増やす。同じ問題の修正で新しいIDを作らない。原本の問番号は`number`・表示名へ残す。公表セット名を`packLabel`へ入れる。

## 学科

解説の役割（`summary`＝何を問うか／`explanation`＝なぜその答えになるか／`takeaway`＝類題で使える知識）と、`**重要部分**` による限定的な太字強調は、**FP2固有ではなく全資格共通**の [解説表示仕様](explanation-presentation-spec.md)・[教材記述ルール](explanation-authoring-rules.md) に従う。`summary`・`takeaway` は任意とし、短い解説で足りる問題を引き延ばさない。共通の表示対応は公開済み。追加教材はこの記述ルールで草稿を作り、内容の独立レビューを経て公開する。

[`question-format.v1.json`](../schemas/question-format.v1.json) と [共通教材契約](content-authoring.md) に従う。

- `type: "singleChoice"`、4つの`choices`と`correctChoiceId`。単独○×も同形式の2択で表現できる。
- 納品時は `enrichment: "draft"`。`stem`、`explanation`、選択肢と同数の`choiceReasons`を必須にする。
- 各選択肢は安定した`id`と`label`、`text`または`image`。正答は表示順の番号ではなくIDを指す。
- `qualificationId: "fp2"`、`examPartId: "objective"`、`topicId`、`sourceKind: "official"`、`source`、`questionUrl`、`answerUrl`を明記する。`uses: ["practice"]`から始める。
- 図だけを切り出し、学習に不要なページ全体の画像を必須にしない。本文の限定Markdownは共通手順に従う。

## 実技：本文 → 小問 → 回答欄

[`case-material.v2.json`](../schemas/case-material.v2.json) と [`case-field.v1.json`](../schemas/case-field.v1.json) に従う。納品時は `status: "draft"`。

- `body`は共通本文、`items`は小問、`fields`は個別の回答欄。1case全体で最大20欄。
- 問1が（ア）〜（エ）の○×4欄なら、1case・1item・4fieldsにする。4問として数えない。
- ○×・4択・語群は`singleChoice`欄。`choices`は`{id,label,text}`。`referenceAnswers`は正答の表示labelを1つ入れる。`grading:{"method":"exactText"}`。選択肢の図はラベルと対応させて`bodyFigures`に含める。
- 短答は`shortText`、自由記述は`freeText`。字数制限を`maxLength`へ。自由記述は`grading:{"method":"self"}`。短答の登録例以外は自己評価へ回る。
- 各欄に`explanation`と`rubric`を用意する。他の欄の解説を流用せず、その回答の根拠を説明する。
- 必須の図・表は `bodyFigures:[{image,anchor,alt,caption}]`。`body`の該当箇所に一意のanchor文字列を置き、`bodyFigures`を本文に現れる順に並べる。空・未配置・重複・順序不一致は草稿の検証でも拒否する。原本ページは`sourceImages`へ置けるが学習に必須ではない。

### 数値欄

```json
{
  "id": "amount",
  "label": "金額",
  "type": "numeric",
  "maxLength": 100,
  "numeric": {"unit": "円", "decimalPlaces": 0, "rounding": "none"},
  "grading": {"method": "exactDecimal"},
  "referenceAnswers": ["1490000"],
  "explanation": "この欄の計算式と根拠。",
  "rubric": ["単位と計算結果を確認する。"]
}
```

正答は**数値型ではなく文字列**。区切り・単位・指数表記を入れない。単位は欄ごとに固定し、複数欄で単位が違う場合は分ける。小数`0.435`なら`decimalPlaces:3`。正答の小数桁は指定以下にする。

`rounding`は原本の計算指示：`none`、`halfUp`（四捨五入）、`floor`（負の無限大方向）、`ceil`（正の無限大方向）、`truncate`（0方向）。**作者が指示どおり計算した最終値を登録する。入力への自動丸めはしない。**

採点は十進文字列の値の完全一致。`1,490,000`・`1490000`・全角数字は同じ値として受理し、末尾の小数0や先頭の0も同値として扱う。浮動小数点の近似比較を使わない。単位換算はしないため、円の欄の`149`は不正解。`149万円`・不正な区切り・指数表記など未対応形式は自動断定せず自己評価へ。誤った数値は自動で不正解になる。

公式配点が非公表の実技に、独自の100点換算・合否判定・推定部分点を付けない。問題数・小問数・回答欄数を区別する。

## 原本の時点と現行法令を分ける

すべての学科問題・実技caseに次の2つを付ける。[Schema](../schemas/legal-context.v1.json)。

```json
{
  "sourceRecord": {
    "publisher": "日本FP協会",
    "publishedAt": null,
    "legalAsOf": null,
    "questionUrl": "https://example.com/question.pdf",
    "questionSha256": "実際のPDFの完全SHA256（64文字）",
    "answerUrl": "https://example.com/answer.pdf",
    "answerSha256": "実際の解答PDFの完全SHA256（64文字）",
    "modifiedFromOriginal": true,
    "modificationNote": "表示用に文字起こし。図を切り出し、解説を追加。"
  },
  "legalReview": {"status": "unverified", "checkedAt": null, "sourceRefs": [], "note": ""}
}
```

上は項目説明用であり、日付・URL・ハッシュを実際の資料に置き換える。`publishedAt`は原本の公表日。日まで確認できなければnullとし、公表年・月は`packLabel`等へ残す。架空の日付を補わない。`legalAsOf`は原本が指定する法令基準日であり、公表日や作成日から推測しない。不明ならnull。

`legalReview.status`は`unverified`／`current`／`outdated`。確認済み状態には確認日・現行法令の一次資料URL・具体的な確認内容が必要。基準日不明のまま確認済みにしない。`outdated`でも当時の公式正答を現行制度の答えへ書き換えない。差異は`note`と解説注記へ記載する。開始済みの学習記録は旧版の本文・正答・基準日を保持する。

過去問の内容確認と正誤判定は原本の法令基準で行う。現行法令との全問照合は、過去問として公開するための必須条件ではない。原本の基準日と、現行法令を確認したかどうかは別々に記録する。

`legalReview.checkedAt`を最終法令チェック日、`status: outdated`を法令改正確認済みのフラグとして使う。項目を重複して追加しない。未確認・確認済みの日付は学習画面に表示せず、原本の法令基準日だけを表示する。改正確認済みの問題を含めて学ぶ場合は「法令改正あり（学習非推奨）」を表示する。

設定の「法令改正のある問題を除外」は既定でオン。通常出題・計画からの推薦・復習候補・問題一覧・新しい診断・記述問題の新規選択から、改正確認済みの教材だけを外す。未確認の教材は対象に残す。固定模試は設問を抜かず、対象問題を含むセットの新規開始を止める。過去の記録・開始済みの回・中断時の入力は保存し、記録から参照・再開できる。除外設定は資格と所有者ごとの端末設定としてバックアップに保存する。

## 検証と受け入れ

caseの試験回・原本問番号は資格設定の `caseCatalogSource` に登録する。[実技・科目Bの出題範囲とカタログ](case-study-navigation.md)を参照。本文と確認台帳を変えずに、試験回別・分野別・おすすめの入口を構成できる。

このリポジトリ側で、納品フォルダを指定する。

```sh
python tools/check-fp2-delivery.py /path/to/delivery
```

形式・単位・数値正答・法令情報・必須画像・実PDFハッシュを検査する。**draftの内容が正しいことや、独立レビュー済みであることは保証しない。** このコマンドは納品物を書き換えず、カタログにも追加しない。

作者とは別担当が、原本・公式解答から全本文・全図表・全選択肢・全欄・数値計算・解説・基準日を確認する。修正後の版とハッシュへ再確認記録を付ける。学科レビューは共通契約、実技は既存caseレビューと同じ形式。両方とも`sourceHashes`に使った原本・解答のリポジトリ相対パスと完全SHA256を保存する。原本に`sourceRecord`の両SHAが含まれることを機械照合する。

独立確認後に、学科を`enrichment: "reviewed"`、実技を`status: "reviewed"`へ変更し、実際の別担当による確認台帳を添えて検証する。`--reviewed`は全問題の確認状態と台帳を照合し、`topic-guide`や状態省略によるレビューの省略を認めない。FP2級の設定では`requiresReviewedContent: true`を指定し、公開ビルドでも未レビュー問題を拒否する。

```sh
python tools/check-fp2-delivery.py /path/to/delivery --reviewed
```

統合時に担当者が作成元・原本・図・確認台帳を取り込み、共通ビルダーと回帰テストを通してから公開資格へ登録する。未確認の教材やレビュー記録の不足は生成を停止する。科目の公開件数が0なら入口を生成しない。FP2級の枠だけでは資格一覧に空のボタンを増やさない。
