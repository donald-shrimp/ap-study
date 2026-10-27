# batch-04：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-04 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-04
python tools/ap-lesson-quality.py check batch-04 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r07a-q6 | アルゴリズム・プログラミング | 二段階の線形探索 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q6.webp) |
| r04h-q6 | アルゴリズム・プログラミング | 再入可能なプログラム | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q6.webp) |
| r03h-q7 | アルゴリズム・プログラミング | 分割統治法 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q7.webp) |
| r04a-q5 | アルゴリズム・プログラミング | 剰余のハッシュ衝突 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q5.webp) |
| r06a-q6 | アルゴリズム・プログラミング | 剰余のハッシュ衝突 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q6.webp) |
| r05a-q5 | アルゴリズム・プログラミング | 双方向リストへの挿入 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q5.webp) |
| r05a-q6 | アルゴリズム・プログラミング | 整列の途中状態の判定 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q6.webp) |
| r04a-q6 | アルゴリズム・プログラミング | 流れ図の整列方式 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q6.webp) |
| r06h-q5 | アルゴリズム・プログラミング | 流れ図の終了条件 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q5.webp) |
| r06a-q7 | アルゴリズム・プログラミング | 統計解析用の言語環境 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q7.webp) |
| r05h-q6 | アルゴリズム・プログラミング | 線形探索の平均比較回数 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q6.webp) |
| r04h-q5 | アルゴリズム・プログラミング | 配列とポインタのリスト | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q5.webp) |
| r03h-q6 | アルゴリズム・プログラミング | 配列による二分木と走査 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q6.webp) |
| r03a-q7 | アルゴリズム・プログラミング | 静的型付けのスクリプト言語 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q7.webp) |
| r05h-q8 | コンピュータ構成 | CPIの計算 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q8.webp) |
| r07h-q9 | コンピュータ構成 | DMAの役割 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q9.webp) |
| r03h-q10 | コンピュータ構成 | GPUと深層学習 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q10.webp) |
| r04a-q8 | コンピュータ構成 | GPUと深層学習 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q8.webp) |
| r07a-q11 | コンピュータ構成 | HPCの総演算性能 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q11.webp) |
| r07a-q13 | コンピュータ構成 | MTBFとMTTR | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q13.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
