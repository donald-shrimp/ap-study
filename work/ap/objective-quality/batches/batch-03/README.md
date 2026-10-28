# batch-03：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-03 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-03
python tools/ap-lesson-quality.py check batch-03 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r03h-q25 | 論理回路 | フィードバック回路の状態 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q25.webp) |
| r05a-q22 | 論理回路 | フィードバック回路の状態 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q22.webp) |
| r05a-q23 | 論理回路 | 三入力多数決回路 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q23.webp) |
| r04a-q23 | 論理回路 | 入力が一致する論理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q23.webp) |
| r03a-q22 | 論理回路 | 半加算器の二出力 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q22.webp) |
| r06h-q21 | 論理回路 | 論理回路と真理値 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q21.webp) |
| r07h-q6 | アルゴリズム・プログラミング | AVL木の挿入 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q6.webp) |
| r05a-q7 | アルゴリズム・プログラミング | JSONの構造 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q7.webp) |
| r07a-q7 | アルゴリズム・プログラミング | Scala | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q7.webp) |
| r04a-q7 | アルゴリズム・プログラミング | XMLの省略可能な文字コード | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q7.webp) |
| r04h-q7 | アルゴリズム・プログラミング | インデントによるブロック | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q7.webp) |
| r05h-q7 | アルゴリズム・プログラミング | クイックソートの分割追跡 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q7.webp) |
| r03h-q5 | アルゴリズム・プログラミング | スタックの出力順序 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q5.webp) |
| r03a-q5 | アルゴリズム・プログラミング | バブルソート | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q5.webp) |
| r06h-q7 | アルゴリズム・プログラミング | バブルソート | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q7.webp) |
| r03a-q6 | アルゴリズム・プログラミング | プログラムの性質 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q6.webp) |
| r05h-q5 | アルゴリズム・プログラミング | ベストフィットの空き領域管理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q5.webp) |
| r07a-q5 | アルゴリズム・プログラミング | ベストフィットの空き領域管理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q5.webp) |
| r06a-q5 | アルゴリズム・プログラミング | 二分探索木からの削除 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q5.webp) |
| r06h-q6 | アルゴリズム・プログラミング | 二分木の再帰走査 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q6.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
