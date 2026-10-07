# 診断専用の派生問題を追加する

2026-10-07に追加基盤を実装しました。公開の派生問題は現在 **17問（各17分野1問）**。前回の草稿17問を2026-10-08の別実行で解き直し、原本・公式解答・全4択の理由と照合して追加しました。確認待ちは **0問**、作成時の17草稿は変更せず履歴として保存しています。新規30問診断は初期状態で派生17問と既存13問を選びます。ここで扱う派生問題は普段の演習・検索・復習候補には入りません。

## 作成から公開まで

1. 元のIPA問題画像・条件・公式解答を読む。過去問道場の独自解説はコピーしない。
2. 計算問題なら数値を変え、条件・丸め・図・正解の一意性も検算する。用語問題なら場面や問う方向を変え、紛らわしい定義や複数正解を避ける。選択肢の順番だけ変えたものを理解の診断問題と扱わない。
3. 正解・解答解説・全選択肢の理由をセットで作る。元問題と異なる独立IDを付け、元問題との関係と変更内容を記す。診断中は支援なしなので、派生問題にヒントを用意することは必須ではない。
4. 作成と分離した確認実行で元問題から解き直し、変更後の問題を確認する。別の担当者が確認した場合と、同じ担当者の別実行の場合を記録で区別する。今回のユーザー指定は後者であり、別人・別エージェント・独立コンテキストによる盲検確認と称さない。指摘を修正した後、完成した問題オブジェクトのハッシュに対する確認記録を残す。確認欄を自動で真にするツールは用意しない。
5. 資格別の問題・確認記録へ追記し、教材生成と検証を通してからGitHub Pagesへ公開する。追加された問題は新しい診断から使う。中断中や終了済みの診断は更新しない。

## ファイルと形式

応用情報の作業ファイルは以下です。

- [content/ap/diagnostic-questions.json](../content/ap/diagnostic-questions.json)：独自問題の配列（現在17問）
- [content/ap/diagnostic-reviews.json](../content/ap/diagnostic-reviews.json)：完成問題に対する確認記録の配列（現在17件）
- [qualification.json](../content/ap/qualification.json)：`diagnosticQuestionSource` と `diagnosticReviewSource` の参照、分野別配分

問題は共通教材のJSONを使います。必要な項目は `id`, `version`, `packId`, `packLabel`, `number`, `title`, `topicId`, `source`, `stem`（または原本相当の `sourceImages` と `imageSizes`）, `choices`, `correctChoiceId`, `enrichment:"reviewed"`, `summary`, `explanation`, `takeaway`, `choiceReasons`, `diagnosticOnly:true`, `parentQuestionId`, `adaptation`。`choices` の各項目は `id`, `label`, `text` または `image`。`hints` は省略すると空配列、図は既存と同じローカルassets参照で、元問題の図を変更する必要があれば別ファイルにします。

`parentQuestionId` は同資格の通常教材に存在するID。分野と試験パートは元問題と同じにし、教材対応パートだけを扱います。`source` は「IPA公式の○年度問○をもとに作成した、ひと問独自問題」などと記し、IPA公式問題そのものとは区別します。`adaptation` は変えた数値・条件・問う方向を記します。問題の訂正時は `version` を上げ、再確認します。

確認記録は次の形式です。以下は説明用であり、実在の確認記録ではありません。

```json
{
  "questionId": "ap-diagnostic-example-001",
  "version": 1,
  "sha256": "完成した問題オブジェクトのSHA-256",
  "author": "作成者の識別名",
  "reviewer": "実際の確認実行の識別名（確認方法と担当の関係をnotesへ明記）",
  "checkedAt": "2026-10-07T00:00:00Z",
  "checks": {
    "source": true,
    "answer": true,
    "calculation": true,
    "choices": true,
    "wording": true
  },
  "notes": "独立に求めた正解・検算・図や誤答理由の確認・指摘と修正の根拠"
}
```

ハッシュは問題オブジェクト全体（選択肢・解説も含む）を、キー順でソートし、UTF-8・余分な空白なしのJSONへ直して計算します。確認済みの完成内容に対して次を実行し、出力したハッシュを記録してください。確認記録自身はハッシュ対象ではありません。

```sh
python tools/diagnostic-hash.py content/ap/diagnostic-questions.json
python tools/build-content.py
python tests/content.py
python tests/diagnostic-content.py
python tests/diagnostic-pool.py
node --test tests/planning-domain.mjs
```

生成処理は未確認・同じ実行識別名による確認・ハッシュ不一致・元問題不明・分野／パート不一致・通常問題集への混入を拒否します。構造検証は人間や別担当による内容確認の代わりにはなりません。上記の診断専用テストは、公開しない合成問題集で構造と挙動を検証しています。

## 配分を増やす

初期の上限は **各分野1問の派生問題**。分野を巡回し、同じ枠では「未着手の派生 → 未着手の既存 → 既出の派生 → 既出の既存」の順に選びます。未着手はアプリ内の取り組み履歴に基づくもので、アプリ外の経験は分かりません。同じ元問題の派生を複数、または元問題と派生を同じ診断には出しません。

教材が充実した分野は、資格定義の `diagnosticBlueprint.variantLimits` に分野IDと整数（0〜30）を指定して上限を増やせます。例えば `{"database":2}`。0はその分野の派生を使わない指定です。分野の出題枠自体を増やす指定ではありません。同じ元問題の派生だけが大量にある場合は充実と扱わず、実際の異なる元問題・内容の範囲を確認して配分を増やします。配分変更時は `diagnosticBlueprint.version` も上げます。

件数に応じた自動切り替えはありません。開始時の方針・配分・問題・教材版を保存し、結果とExportに既存／派生の件数・回答数・正解数、元問題の既出状況も出します。派生への回答は診断結果に計上し、通常履歴・復習候補・計画の取り組み回数には混ぜません。学習へ戻る操作は元問題を開き、別の通常試行として記録します。

独立した元問題が30問に満たないなど、出題条件を満たせない場合は開始せず理由を表示します。教材の取得・確認失敗も黙って過去問へ置き換えません。通常学習はそのまま使えます。


## 初回17問の公開と次の作成（2026-10-08）

**公開17問／未確認草稿0問／履歴として保存した草稿17問**。全17分野が公開1問ずつです。元問題は17種類で重複なし。ただし16問は2025年春、論理回路1問は2025年秋のため、次周は2021〜2024年の別の元問題・別の内容を優先します。分野別の出題上限は1問のままです。

- [進捗台帳](../content/ap/diagnostic-progress.json)：公開・確認待ち・元年度の件数、元問題ID、草稿と完成版のハッシュ、次の着手。
- [作成時の草稿](../content/ap/diagnostic-drafts/20261008-first-round.json)：変更せず保存。`enrichment:draft` のままで、診断へ直接読ませません。
- [作者の自己検算](../content/ap/diagnostic-drafts/20261008-first-round-author-checks.json)：前回作成実行による自己検算のみ。確認記録へ転記していません。
- [今回の先行解答](../content/ap/diagnostic-drafts/20261008-first-round-review-solutions.json)：問題文・4択の抽出後、草稿の正解・解説との比較前に保存した解答と根拠。
- [完成教材](../content/ap/diagnostic-questions.json)・[確認記録](../content/ap/diagnostic-reviews.json)：全4択・原本・公式正解・変更点を照合した完成オブジェクトと一致するSHA-256。

前回作者は `codex-author-run-20261007T164320Z`、今回確認は `codex-review-run-20261008-scheduled-continuation`。**同じ1担当の別実行**で、子エージェントや並列ワーカーは使用していません。会話要約を引き継いでいるため、正解を全く知らない独立コンテキストでの盲検確認とは扱いません。名前だけを変えた自己確認ではなく、新しい解答記録・原本再視認・公式解答PDF照合・再計算を残しています。

今回の17問は、草稿と解き直した正答が全て一致しました。全4択の理由・条件・変更内容にも訂正を要する誤りは確認されず、本文を保持して `enrichment` のみ `reviewed` にしました。確認記録はその完成版のハッシュです。

次は **基礎理論 → 論理回路 → 残りの15分野**の順で1問ずつ進めます。現在は全分野1問で同数なので、この順を起点にします。2021〜2024年の独立した元問題を優先します。同一実行で新しく作った問題は草稿として残し、次の確認実行まで出題しません。教材の数だけを理由に上限を増やしません。

```sh
python tools/read-diagnostic-drafts.py content/ap/diagnostic-drafts/20261008-first-round.json
python tools/verify-diagnostic-first-round.py
python tests/diagnostic-first-round.py
python tests/diagnostic-ap.py
```

最初のコマンドは問題文・4択だけを表示します。2番目は保存された作成時の自己検算の再現で、確認・承認を行いません。3番目は今回の完成17問・確認ハッシュ・再計算・進捗を検証します。4番目は実際のAP教材をブラウザで解き、混在・重複回避・支援なし・オフライン中断再開・全4択の理由・結果とAI出力・通常学習への非混入を確認します。これらの自動検証は内容を読む確認の代わりではありません。
