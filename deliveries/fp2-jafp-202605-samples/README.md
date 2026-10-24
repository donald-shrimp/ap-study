# FP2級 日本FP協会・実技 2026年公表分 全40問

PR36の外部草稿を原本から独立レビューし、指摘箇所を修正・再確認した納品物。**40cases / 40items / 68回答欄**（選択46・数値22）。公開登録は未実施で、公開用の作成元・カタログ・HTML・学習記録は変更していない。`status:draft`を保ち、受け入れた草稿全40件のハッシュを保存している。

## レビューと修正

- 確認担当：Codex `/root`（外部作成者とは別担当）。公式問題32頁・模範解答1頁を実表示し、全文・条件・図表・全選択肢・68正答・全解説を照合。数値22欄は単位・端数処理まで再計算した。
- 修正作成担当：Codex `/root/pr36_corrections`。主担当が完成した全25修正caseと23図を原本へ再照合した。公式正答の変更は0件。
- 問14・20の「最も不適切」という誤った欄名を修正。問15の役職限定加入、問27の配偶者居住権の説明を訂正。問10の指定日の説明を精密化し、問36の未確認法令に関する定型注意書きを削除。
- 問16の個人賠償責任特約、問39の表前半、問33の次頁バランスシートを補完。既存の22PNGは保持し、新しい版の図23枚（既存画像から20枚、欠落のPDF補完3枚）へ参照を変更した。
- 二重表示していたOCR表、次問や本文断片の混入、余白を整理。本文の該当位置へ図を配置し、問15の表も復元した。変更caseはversion2。

記録：[`review/pr36-review-evidence.json`](review/pr36-review-evidence.json)、[`review/progress.json`](review/progress.json)。元・完成case、原本PDF、各図のSHA-256と実際の担当を記録。図の矩形・倍率・補完理由は[`review/correction-provenance.json`](review/correction-provenance.json)。旧版はGit履歴と既存PNGに残る。

## 原本と利用条件

| 公式原本 | 保存先 | SHA-256 |
| --- | --- | --- |
| [問題PDF](https://www.jafp.or.jp/exam/mohan/files/j2_202605_q.pdf) | `sources/fp2/j2_202605_q.pdf` | `3760b39cbeffc2062de054639a2910b615df63d8b9f592e8dd3e1b368a0d02ef` |
| [模範解答PDF](https://www.jafp.or.jp/exam/mohan/files/j2_202605_a.pdf) | `sources/fp2/j2_202605_a.pdf` | `9c3508ba491a84ce97b96157942d63f865084ef2b098359fb425f68728334abd` |

公式URLから取得し直したファイルとバイト一致。出典：日本FP協会「2級ファイナンシャル・プランニング技能検定 実技試験（資産設計提案業務）2026年公表分」。画面表示用の文字起こし、case・回答欄への分割、図表の切り出し、個別解説・評価基準の加筆を行った。[協会の利用条件](https://www.jafp.or.jp/exam/mohan/files/exam_riyou.pdf)は出典・加工の明記を求め、申請不要としている。確認した条件PDFは`review/sources/exam-riyou.pdf`へ保存。

過去問は原本の条件で確認した。法令基準日・公表日は推定せずnullを維持し、現行法令との全問照合はしていない。`legalReview.status:unverified`を保持する。現行法令の確認は過去問公開の必須条件ではない。公式の欄別配点は非公表なので、独自の100点換算・合否判定は作らない。

## 検証

リポジトリルートから：

```sh
python tools/check-fp2-delivery.py deliveries/fp2-jafp-202605-samples
python deliveries/fp2-jafp-202605-samples/review/verify-answers.py deliveries/fp2-jafp-202605-samples
node deliveries/fp2-jafp-202605-samples/review/verify-grading.mjs deliveries/fp2-jafp-202605-samples/content/fp2/practical-cases.json
python deliveries/fp2-jafp-202605-samples/review/verify-figures.py deliveries/fp2-jafp-202605-samples
```

最後の図検証にはPyMuPDFとPillowが必要。納品チェッカーは40cases / 68fieldsで成功し、draftとして構造を検証する。公開承認台帳の代用にはしない。

- [再計算](review/calculations.json)：68公式正答と一致、22数値欄の独立計算・単位・端数処理。
- [採点](review/grading.json)：137選択経路、22数値欄の正誤・全角・桁区切り・単位付き入力の扱い。
- [図](review/figure-check.json)：23枚を旧PNG矩形／公式PDFレンダーと独立に画素照合。
- [画面](review/browser-results.json)：非公開プレビューで40caseを描画し、68欄を実入力して正解を確認。幅320/390/1440、必須23図、事前保存後のオフライン描画を検証。プレビューの状態変更は納品物や本番へ反映していない。

公開登録時は受け入れハッシュと一致する草稿だけを使い、`status:reviewed`への変更後に正式台帳と公開データを生成して再検証する。今回のレビューで未解決の内容指摘は0件。
