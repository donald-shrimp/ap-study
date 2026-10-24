# PR35 レビュー修正

初回確認対象: `bab5814cf82b82aaa4596eac45dd5023d5aad1e1`。外部作者の学科60問を `/root` が公式原本34ページから確認し、正答60件・選択肢240件との一致、解説と全選択肢理由を点検した。以下の3件を修正した。

| 問題 | 指摘と修正 | 根拠 |
| --- | --- | --- |
| 14 | 新旧個人年金を「合算できない」という理由を、両方適用時の合計上限4万円へ訂正。旧制度単独5万円を選び、旧一般5万円と合わせて10万円。 | 公式PDF p8、国税庁No.1140 |
| 35 | 主解説と理由1の起算点を借入日から初回返済に訂正。初回返済月から最終返済月までが10年未満となった年以後は控除不可。 | 公式PDF p21、国税庁No.1225注2とQ1/A1 |
| 55 | 親族関係図を補足原本用のsourceImagesから、通常表示・事前保存の対象となるimageへ移動。正確なimageAltを追加し、不要になった画像参照文を除去。 | 公式PDF p31と切出しPNG、現行の表示・保存処理 |

3問をversion 2へ更新した。全60問の選択肢と公式正答ID、他57問のオブジェクト、原本PDFとPNGは不変。

## 修正後の確認

修正担当 `/root` と異なる `/root/review_pr35_corrections` が3問の原本画像と完成図を直接開き、全文・図・全選択肢理由・修正後ハッシュを再確認。問14と55を独立検算し、問35の起算点・適用停止年は国税庁の本文とQAで照合。追加指摘なし。

- 最新mainとPRブランチそれぞれの `tools/check-fp2-delivery.py` による構造・画像・実PDFハッシュ検査が成功（60問、実技0件）。
- 現行の `requiredQuestionAssets(q55)` は図PNG1件を返す。
- カタログへ登録しない専用プレビューで実際の共通学習レンダラーを使用。320・390・1440pxで図が通常表示され、4選択肢が表示され、横はみ出しがないことを確認。
- 実際の `createOfflineStore` とブラウザCache Storageで図をハッシュ検査して保存。通信を切った後も保存済み判定と888×364pxのPNG復号に成功。アプリ全体のオフライン再起動の検査とは区別する。
- ブラウザJavaScriptエラーなし、`git diff --check` 成功。

確認の経緯・各問のハッシュと根拠は [pr35-review-evidence.json](pr35-review-evidence.json)。これは修正レビューの監査記録であり、公開生成用の承認台帳ではない。全問の現行法令照合は未実施で、`enrichment: draft` / `legalReview: unverified` を維持する。

## 一次資料

- [日本FP協会公式問題・正答PDF](https://www.jafp.or.jp/exam/mohan/files/g2_202605_qa.pdf)（法令基準2025-04-01）
- [国税庁 No.1140 生命保険料控除](https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1140.htm)
- [国税庁 No.1225 対象となる住宅ローン等](https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1225.htm)
- [国税庁 No.1225 Q1 臨時弁済](https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1225_qa.htm#q1)
