# batch-09：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-09 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-09
python tools/ap-lesson-quality.py check batch-09 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r03a-q17 | システム構成・OS | ページフォールト発生率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q17.webp) |
| r06a-q18 | システム構成・OS | ページングと領域割当て | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q18.webp) |
| r03a-q16 | システム構成・OS | ページ置換えによる性能低下 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q16.webp) |
| r06a-q17 | システム構成・OS | ページ置換えによる性能低下 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q17.webp) |
| r04h-q18 | システム構成・OS | メモリの断片化 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q18.webp) |
| r04h-q16 | システム構成・OS | 一時ファイルの最大使用量 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q16.webp) |
| r03h-q18 | システム構成・OS | 主記憶管理の方式 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q18.webp) |
| r03h-q14 | システム構成・OS | 二段直列を並列にした稼働率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q14.webp) |
| r05h-q18 | システム構成・OS | 仮想記憶の用語 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q18.webp) |
| r03a-q19 | システム構成・OS | 仮想記憶の補助記憶 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q19.webp) |
| r04h-q14 | システム構成・OS | 修復時間を短くする機能 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q14.webp) |
| r06a-q16 | システム構成・OS | 優先度と飢餓 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q16.webp) |
| r07a-q15 | システム構成・OS | 処理時間順のジョブ | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q15.webp) |
| r03a-q18 | システム構成・OS | 分散型バージョン管理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q18.webp) |
| r06a-q19 | システム構成・OS | 分散型バージョン管理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q19.webp) |
| r05a-q18 | システム構成・OS | 別のCPU向けのコンパイル | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q18.webp) |
| r03h-q16 | システム構成・OS | 到着順とターンアラウンド | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q16.webp) |
| r04a-q18 | システム構成・OS | 割込みとタスク優先度 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q18.webp) |
| r04h-q19 | システム構成・OS | 同時処理数と終了時刻 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q19.webp) |
| r06h-q18 | システム構成・OS | 同時処理数と終了時刻 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q18.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。

## 独立レビューの現在地

[PR #81](https://github.com/donald-shrimp/ap-study/pull/81)の作者head `c9127642c7e50748071e46033adcc5a591604cef` を原本・公式解答から独立確認。20問・80肢・60ヒントを確認し、18問の最終教材ハッシュを `reviews.json` に承認済みとして保存。r06a-q17とr04a-q18は第2段ヒントの開示判定を修正待ち。指摘・根拠・採点処理での再現は [review/independent-review.json](review/independent-review.json) を参照。作者による修正後に別担当が再確認し、20問全件が承認されるまでaccept・公開しない。今回のレビューでは草稿・公開教材を変更していない。

2026-10-27追記：上記2件はCodex /rootがフラグと設計メモを修正し、別担当が原本・公式解答・最終教材・採点を独立再確認した。[修正後の確認記録](review/correction-independent-review.json)を保存し、reviews.jsonは20件の最終承認。初回指摘は履歴として保持。未登録・未マージ・未公開。
