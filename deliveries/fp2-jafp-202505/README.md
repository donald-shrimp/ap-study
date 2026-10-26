# FP2級 2025年5月公表分

日本FP協会の学科60問・実技40問（68回答欄）を、[PR #37](https://github.com/donald-shrimp/ap-study/pull/37)で独立レビュー・修正後に統合する。

- 原本：学科問題・正答一体、実技問題、実技模範解答の3点を `sources/fp2/` に保存。[完全SHA-256](content/fp2/source-files.json)。学科の原本法令基準は2024-04-01。実技の基準日・公表の暦日は確認できないためnull。
- 作成元：`content/fp2/questions.json` と `practical-cases.json` は最終確認したdraft。公開元へは `enrichment` / `status` だけをreviewedにした同一内容を追加する。納品時の空の確認台帳は保持し、独立確認済みの台帳は `review/` に分離。
- 原本の本文・全240肢・公式正答、実技全68欄・表の全行列と脚注・図・計算・解説・確認ポイントを作者と別担当が照合。[初回指摘](https://github.com/donald-shrimp/ap-study/pull/37#pullrequestreview-5648119784)を修正し、最終版を再確認。学科・実技のIDと公式正答・採点契約は保持。
- 学科問10の問いと当期純利益800百万円を復元し、問10・28の表を本文へ構造化。全肢理由の計算・制度説明、問59の適用条件を修正。新規ヒントは未設置（任意）。
- 実技は前問が混入した48配置のページ画像を任意の原本参照へ分離。本文の表を構造化し、必要な土地図・保険証券・親族図だけを5枚切り出した。各辺・ラベル・脚注・空欄を原本と再確認。問29の年次、問18の一時所得と総所得算入額、回答欄名・各肢説明・確認ポイントも修正。
- 図・本文・解説はオフライン保存、PDFと原本ページ画像は任意のオンライン参照。出典・加工表示は [FP2級の出典](../../docs/FP2-SOURCES.md)。過去問は原本の基準で評価し、現行法令の全問照合・実際の初学者試用はこの内容レビューに含めない。

## 確認記録

| 対象 | 最終内容確認 | 公開用確認台帳 |
| --- | --- | --- |
| 学科1–30 | [別担当の最終記録](review/objective-final-01-30.json) | [学科60問](review/objective-publication-reviews.json) |
| 学科31–60 | [別担当の最終記録](review/objective-final-31-60.json) | 同上 |
| 実技1–20 | [別担当の最終記録](review/practical-final-01-20.json) | [実技40問](review/practical-publication-reviews.json) |
| 実技21–40 | [別担当の最終記録](review/practical-final-21-40.json) | 同上 |

原本との図の切り出し位置・拡大率・PNGの完全SHAは [実技1–20](review/practical-01-20-crops.json)・[実技21–40](review/practical-21-40-crops.json)。初回記録、修正来歴、原本の指示の保持は同じ `review/` に残す。[統合・ローカル確認](review/publication-integration.json)と[進捗](review/progress.json)はコミット時点の記録。マージ後のCI・Pages・公開ファイルと画面の確認結果はPR本文に追記する。

```sh
python tools/check-fp2-delivery.py deliveries/fp2-jafp-202505
python tools/check-fp2-delivery.py . --reviewed
python tests/fp2-content.py
python tests/fp2-202505-published.py
```

最初はdraftの形式検査、2つ目以降は統合後の台帳・原本・図のハッシュと実画面を検証する。形式検査だけで内容確認を代用しない。旧2026年5月・2025年1月の教材と台帳、AP・AB-730、個人記録は保持する。
