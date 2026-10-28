# batch-24：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-24 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-24
python tools/ap-lesson-quality.py check batch-24 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r06a-q47 | 開発技術 | マイクロサービスの利点 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q47.webp) |
| r06h-q46 | 開発技術 | モジュール結合度の分類 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q46.webp) |
| r06a-q50 | 開発技術 | レスポンシブ表示 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q50.webp) |
| r07h-q46 | 開発技術 | 二環境を使うリリース | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q46.webp) |
| r04h-q46 | 開発技術 | 低い結合度 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q46.webp) |
| r05h-q46 | 開発技術 | 低い結合度 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q46.webp) |
| r06a-q48 | 開発技術 | 使用性の評価目標 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q48.webp) |
| r07h-q47 | 開発技術 | 保守性の指標 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q47.webp) |
| r06h-q47 | 開発技術 | 信頼度成長の曲線 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q47.webp) |
| r05h-q47 | 開発技術 | 値引きの決定表 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q47.webp) |
| r07a-q46 | 開発技術 | 典型的な利用者像 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q46.webp) |
| r04h-q47 | 開発技術 | 分岐網羅と条件網羅 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q47.webp) |
| r04a-q48 | 開発技術 | 命令網羅と分岐網羅 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q48.webp) |
| r03h-q48 | 開発技術 | 命令網羅の最小ケース数 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q48.webp) |
| r04h-q48 | 開発技術 | 文書整備と保守分類 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q48.webp) |
| r05a-q48 | 開発技術 | 文書整備と保守分類 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q48.webp) |
| r04a-q46 | 開発技術 | 机上での成果物の確認 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q46.webp) |
| r05h-q49 | 開発技術 | 特許の実施許諾 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q49.webp) |
| r03h-q47 | 開発技術 | 状態遷移表の追跡 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q47.webp) |
| r04h-q50 | 開発技術 | 統合開発環境 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q50.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。

## 独立内容レビュー

原本20画像・公式解答・全80肢理由・60ヒント・解説と設計メモを独立確認。初回草稿と確認記録を固定し、主担当の訂正2問を別担当が最終確認した。不変18問も最終ハッシュを照合済み。[初回記録](review/independent-review.json)と[最終記録](review/correction-independent-review.json)を参照。未登録・未マージ・未公開。
