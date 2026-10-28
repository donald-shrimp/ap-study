# pilot-00：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim pilot-00 --author '実際の担当名'
python tools/ap-lesson-quality.py check pilot-00
python tools/ap-lesson-quality.py check pilot-00 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r07h-q1 | 基礎理論 | 含意の真理値 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q1.webp) |
| r07h-q5 | アルゴリズム・プログラミング | スタックの出力順序 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q5.webp) |
| r07h-q8 | コンピュータ構成 | CPIと実行時間 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q8.webp) |
| r07h-q14 | システム構成・OS | プリエンプションとタスク状態 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q14.webp) |
| r07h-q18 | ハードウェア | D/A変換の出力電圧 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q18.webp) |
| r07h-q22 | インタフェース・マルチメディア | ユーザビリティ評価の参加者 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q22.webp) |
| r07h-q25 | データベース | 多重度と参照制約 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q25.webp) |
| r07h-q31 | ネットワーク | 最長一致の経路選択 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q31.webp) |
| r07h-q35 | セキュリティ | CRYPTREC暗号リスト | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q35.webp) |
| r07h-q45 | 開発技術 | デザインレビューの目的 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q45.webp) |
| r07h-q52 | プロジェクトマネジメント | EVMの三つの効率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q52.webp) |
| r07h-q56 | サービスマネジメント・監査 | IaaS・PaaSの運用分担 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q56.webp) |
| r07h-q64 | システム戦略 | 活動基準の費用配賦 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q64.webp) |
| r07h-q67 | 経営戦略 | PPMの二つの軸 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q67.webp) |
| r07h-q76 | 企業活動 | 回転率と利益率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q76.webp) |
| r07h-q78 | 法務 | 生成画像と著作権侵害 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q78.webp) |
| r07a-q22 | 論理回路 | タイミング図と論理ゲート | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q22.webp) |
| r03a-q3 | 基礎理論 | 多層ニューラルネットワーク | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q3.webp) |
| r06h-q1 | 基礎理論 | ベイズの定理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q1.webp) |
| r07h-q7 | アルゴリズム・プログラミング | 階乗の再帰定義 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q7.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
