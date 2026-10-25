# FP2級 過去問の原本・図の復元と検証

作成済み草稿：[2025年1月 PR48](https://github.com/donald-shrimp/ap-study/pull/48)・[2024年9月 PR49](https://github.com/donald-shrimp/ap-study/pull/49)・[2024年5月 PR50](https://github.com/donald-shrimp/ap-study/pull/50)。各回の `questions.json`・`practical-cases.json`・`source-files.json` を正本とする。作問・独立レビュー・公開は [共通手順](../../../docs/content-authoring.md)と[FP仕様](../../../docs/fp2-authoring.md)に従う。

## 原本と図を揃える

```sh
python -m pip install 'pymupdf>=1.24,<2'
python tools/prepare-fp2-delivery.py work/fp2/historical/202501 --output /tmp/fp2-202501-delivery
```

草稿のあるブランチで実行する。出力先は新しいフォルダを指定する。公式PDFを取得して `source-files.json` のSHA-256と照合し、草稿JSONをバイト単位でコピーする。本文・解説・版・法令確認状態・既存台帳を書き換えない。完成した納品物は既存の `tools/check-fp2-delivery.py` で検証する。失敗時は完成出力を残さない。

原本が手元にある場合は `--source-dir /path/to/delivery-root` を指定できる。その配下の `sources/fp2/` から読み、同じSHA照合を行う。

既存の図が草稿フォルダ・`--source-dir`・リポジトリにあればコピーする。旧草稿の `assets/fp2/<回>/qNN-pNN.png` と `assets/written/fp2/<回>/qNN-pNN.png` は、該当する学科／実技の問題PDFから復元する。旧PR38の切り出し条件（1始まりの頁番号、PDF座標 `[52,77,幅-48,高さ-67]`、倍率1.5）を使用し、ページ・座標・PDF／画像SHA・PyMuPDF版を `recovery.json` に残す。他の欠損画像は推測で補わず停止する。

復元画像は原本ページの機械トリミングであり、学習に必要な図の切り出し・文字起こしが完成したことを意味しない。レビュー担当が範囲・対応ラベル・欠落・オフライン表示を確認する。

## GitHubから実行する

Actionsの **FP2 source and figure recovery** を手動実行し、草稿のブランチ／コミットとフォルダを指定する。ツール側とは別に草稿を取得し、完成納品物をartifactとして保存する。JSONをログへ転送する処理や草稿の再作成処理は持たない。

通常のFP検証CIも、このフォルダに存在する各回を同じツールで準備・検証する。JSON欠落、不正な数値・選択肢参照・図のanchor・法令情報・PDF／画像の欠落は既存契約で検査する。`summary`・`takeaway` は任意。`legalReview` は内容承認と別に扱い、`current`／`outdated` は根拠情報が必要。

形式検証は内容の承認ではない。教材PRは独立レビュー後に統合し、復元物を本番へ自動反映しない。PR51では教材・公開pack・画面コードを変更しない。
