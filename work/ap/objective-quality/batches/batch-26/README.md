# batch-26：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-26 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-26
python tools/ap-lesson-quality.py check batch-26 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r06a-q51 | プロジェクトマネジメント | スコープ管理の活動 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q51.webp) |
| r05a-q51 | プロジェクトマネジメント | スコープ記述書 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q51.webp) |
| r07a-q52 | プロジェクトマネジメント | タックマンの対立段階 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q52.webp) |
| r06a-q53 | プロジェクトマネジメント | チームを同じ場所へ集める | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q53.webp) |
| r07h-q54 | プロジェクトマネジメント | テスト密度と欠陥密度 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q54.webp) |
| r07a-q54 | プロジェクトマネジメント | デシジョンツリーの期待価値 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q54.webp) |
| r05h-q54 | プロジェクトマネジメント | デルファイ法 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q54.webp) |
| r06a-q54 | プロジェクトマネジメント | ファストトラッキング | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q54.webp) |
| r03a-q51 | プロジェクトマネジメント | フェーズゲートの判断 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q51.webp) |
| r05h-q51 | プロジェクトマネジメント | プロジェクト憲章 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q51.webp) |
| r07h-q51 | プロジェクトマネジメント | プロジェクト憲章 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q51.webp) |
| r03a-q53 | プロジェクトマネジメント | リスクの定量分析 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q53.webp) |
| r06h-q53 | プロジェクトマネジメント | リスクの管理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q53.webp) |
| r04a-q52 | プロジェクトマネジメント | リード・ラグの時間計算 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q52.webp) |
| r06h-q54 | プロジェクトマネジメント | 二案の期待金額価値 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q54.webp) |
| r03a-q52 | プロジェクトマネジメント | 二種類のネットワーク図 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q52.webp) |
| r04h-q53 | プロジェクトマネジメント | 作業依存と最短期間 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q53.webp) |
| r03h-q53 | プロジェクトマネジメント | 作業分割で期間を短縮 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q53.webp) |
| r05a-q53 | プロジェクトマネジメント | 作業分割で期間を短縮 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q53.webp) |
| r03h-q55 | プロジェクトマネジメント | 全員の二者面談の組数 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q55.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
