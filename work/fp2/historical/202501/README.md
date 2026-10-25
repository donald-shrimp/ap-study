# FP2級 2025年1月 — PR #48 の内容レビューと修正

対象は日本FP協会の2025年1月26日実施分、**学科60問・実技40ケース／68回答欄**。学科には2段ヒント120件がある。学科・実技とも、作者とは別担当が原本と照合し、修正後の最終版を内容承認した。

**学習アプリへの統合・mainへのマージ・公開はまだ行っていない。** このフォルダのJSONは `draft` を保持する。現在の状態は [review-progress.json](review-progress.json)、受入結果は [review/](review/) を参照する。過去の作者台帳にある未完・改善件数は各時点の履歴であり、現在の判定は今回の最終レビューを正本とする。

## 今回の修正

- 学科：27問を改訂。原本20問26肢に残っていた欠字・誤転記を復元。問17の「最長10年→1年」の誤転記と連動解説、問19のがん保険の待機期間、問16の保険料の損金処理などを修正。問26の資料を列対応のある表にした。
- ヒント：問19・28・44・51・54の第1段が実質的な答えを教えていたため、説明を保持して `revealsAnswer:true` へ訂正。第2段で計算・比較を本人に残す問23・26は `false` を保持した。全120件を [共通ルール](../../../../docs/hint-authoring.md) で個別確認。
- 実技：35ケースを改訂。問33の年齢、問36の復興特別所得税を考慮しない指示、問37の家族関係と単位を復元。問24の計算途中値、問2の個人データの毀損の説明を修正。
- 図表：隣問まで含む学習用ページ画像58か所を廃止。必要な図・複雑な表だけを**8画像／9配置**として切り出し、他の数表はMarkdown表へ整形した。旧ページ画像は任意の原本参照 `sourceImages` へ移し、オフライン教材から外す。必須画像の合計は593,784バイト。
- 正答60件／68回答欄、採点設定、ID、原本4点のSHA、法令情報は保持。変更した教材だけ旧版+1。未変更は学科33問・実技5ケース。

## 独立レビュー

- 学科：[最終確認](review/objective-final-review.json)／[統合用の確認台帳](review/objective-publication-reviews.json)。全60問・240肢と理由・120ヒント、原本本文・公式正答・数値を確認。
- 実技：[最終確認](review/practical-final-review.json)／[統合用の確認台帳](review/practical-publication-reviews.json)。原本全37頁、公式全68欄、各条件・計算・表・全8画像を確認。
- [学科の修正一覧](review/objective-correction-log.json)／[実技の修正一覧](review/practical-correction-log.json)／[図の切り出し位置とSHA](review/learning-figure-crops.json)。修正途中で生じた本文欠落や見出しの端切れも、復元後に別担当が再確認して解消した。
- 台帳のSHAは、実際に確認した最終草稿と、`enrichment/status` だけを `reviewed` にした将来統合用の内容へ結び付ける。形式チェックを内容承認の代わりにしていない。

法令基準日は原本指定の **2024-10-01**。過去問は当時の基準で確認した。現行法令の網羅照合・実学習者による効果測定は実施していない。`legalReview` は元の状態を保持し、未実施の確認日や承認を作らない。

実画面の受入は [runtime-verification.json](review/runtime-verification.json) に記録。隔離したゲスト環境で全100問・120ヒント・68欄・必要画像8点、オフライン・保存再開・合成記録のバックアップ入出力を確認した。320／390／1440pxとアプリの学習文字200％で横にはみ出さず、JavaScript例外は0件。本番アカウントの端末間同期確認とは別の検証である。

## 再現方法

原本PDFと旧ページ画像は [共通ツール](../../../../tools/prepare-fp2-delivery.py)で復元する。新しい切り出し画像はこのフォルダの `assets/` に保存してある。出典PDF4点の完全SHAは [source-files.json](source-files.json)。

```sh
python tools/prepare-fp2-delivery.py work/fp2/historical/202501 --output /tmp/fp2-pr48-delivery
python work/fp2/historical/202501/review/verify.py /tmp/fp2-pr48-delivery
python work/fp2/historical/202501/review/verify-browser.py --delivery /tmp/fp2-pr48-delivery
```

`verify.py` は別担当の最終ハッシュ・原文訂正・図・原本と、統合用台帳を一時ディレクトリで検査する。ブラウザ検証はこの教材だけの隔離サイトを作り、全問の表示・採点・ヒント・学習文字200％・320/390/1440px・オフライン・中断入力・合成記録のバックアップを確認する。本番の教材・DB・個人記録は変更しない。

公開時は既存2026年5月分を保持して作成元・確認台帳・原本・必要画像・試験回カタログを統合し、最新mainの生成と回帰検証、Pagesと公開ファイル・画面の一致まで確認する。この草稿PRのCI成功だけを公開完了とは扱わない。

## 以前の作者記録

[解説と原文の点検](explanation-audit.md)／[実技の解説点検](practical-explanation-audit.md)／[ヒントの改稿履歴](hint-rework-inventory.md)。元の一括PR #38を再レビューせず、#48の最終版を確認している。
