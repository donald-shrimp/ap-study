# batch-10：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-10 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-10
python tools/ap-lesson-quality.py check batch-10 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r05a-q17 | システム構成・OS | 周期タスクの期限 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q17.webp) |
| r06h-q19 | システム構成・OS | 実行性能の計測ツール | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q19.webp) |
| r03h-q15 | システム構成・OS | 密結合マルチプロセッサ | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q15.webp) |
| r05a-q15 | システム構成・OS | 待機系への切替えと稼働率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q15.webp) |
| r06h-q15 | システム構成・OS | 性能評価のシミュレーション | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q15.webp) |
| r05h-q15 | システム構成・OS | 故障を防ぐ設計と耐える設計 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q15.webp) |
| r06a-q14 | システム構成・OS | 直並列システムの比較 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q14.webp) |
| r05h-q16 | システム構成・OS | 直並列構成の大小比較 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q16.webp) |
| r04a-q19 | システム構成・OS | 複数プリンターへの割当て | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q19.webp) |
| r06h-q17 | システム構成・OS | 資源取得順と循環待ち | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q17.webp) |
| r03a-q15 | システム構成・OS | 重ね合わせ処理のスループット | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q15.webp) |
| r06h-q16 | システム構成・OS | 非プリエンプティブな実行 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q16.webp) |
| r03a-q23 | ハードウェア | GPIOのビット操作 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q23.webp) |
| r03h-q20 | ハードウェア | Hadoopの用途 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q20.webp) |
| r03h-q23 | ハードウェア | Hブリッジの逆転 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q23.webp) |
| r07a-q20 | ハードウェア | LEDと抵抗の消費電力 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q20.webp) |
| r05h-q23 | ハードウェア | LiDARによる測距 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q23.webp) |
| r05a-q21 | ハードウェア | MOSトランジスタ | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q21.webp) |
| r05h-q24 | ハードウェア | NFCの通信範囲 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q24.webp) |
| r07h-q19 | ハードウェア | PLCによる産業制御 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q19.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。

## 独立レビュー

[PR #82](https://github.com/donald-shrimp/ap-study/pull/82)の作者head `29e8d1682f7050acab309dbf75f911c36296252f` を独立確認。20原本画像・9回分の公式解答PDF・80肢・60ヒントを照合し、計算と回路/論理条件を再検証した。20問の最終教材ハッシュをreviews.jsonに保存し、残指摘0。根拠は [review/independent-review.json](review/independent-review.json)。草稿・公開教材は変更していない。内容承認と登録・公開を区別し、未登録・未マージ・未公開。
