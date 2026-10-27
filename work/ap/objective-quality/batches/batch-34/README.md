# batch-34：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-34 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-34
python tools/ap-lesson-quality.py check batch-34 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r07h-q73 | 経営戦略 | コンピテンシーモデル | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q73.webp) |
| r06a-q69 | 経営戦略 | コ・クリエーション | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q69.webp) |
| r04a-q68 | 経営戦略 | ターゲットリターン価格 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q68.webp) |
| r03a-q71 | 経営戦略 | デジタルツイン | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q71.webp) |
| r05h-q73 | 経営戦略 | デジタルツイン | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q73.webp) |
| r06h-q70 | 経営戦略 | デジタルツイン | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q70.webp) |
| r06h-q73 | 経営戦略 | ナッシュ均衡 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q73.webp) |
| r04h-q69 | 経営戦略 | バイラルマーケティング | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q69.webp) |
| r03a-q67 | 経営戦略 | バリューチェーン分析 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q67.webp) |
| r07h-q69 | 経営戦略 | ビジネスモデルキャンバスのVP | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q69.webp) |
| r04a-q71 | 経営戦略 | ファブレスの事業形態 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q71.webp) |
| r03h-q73 | 経営戦略 | フィルターバブル | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q73.webp) |
| r03h-q68 | 経営戦略 | フォロワー戦略 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q68.webp) |
| r07h-q70 | 経営戦略 | フリーミアムの収益 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q70.webp) |
| r07h-q68 | 経営戦略 | プライスライニング | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q68.webp) |
| r05a-q73 | 経営戦略 | マシンビジョンの目的 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q73.webp) |
| r07h-q72 | 経営戦略 | マシンビジョンの目的 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q72.webp) |
| r06h-q71 | 経営戦略 | マスカスタマイゼーション | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q71.webp) |
| r03a-q69 | 経営戦略 | リーンスタートアップ | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q69.webp) |
| r03h-q66 | 経営戦略 | レベニューシェアの報酬 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q66.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
