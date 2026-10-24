# FP2級 日本FP協会・実技 代表４問（作成者Draft）

このフォルダは `docs/fp2-authoring.md` に準じた **未レビュー教材の作業納品** です。公開・マージを意図しません。

## 対象
2026年5月公表、日本FP協会2級実技「資産設計提案業務」。問1・問2・問4・問5を正式な問番号のまま1問1caseとして作成しました。

| 公式問 | 型 | 回答欄 | 公式正答 |
|---|---|---:|---|
| 問1 | ○×（4欄） | 4 | ×・×・○・○ |
| 問2 | 4択 | 1 | 4 |
| 問4 | 数値（％、切捨） | 1 | 0.435 |
| 問5 | 数値（％・倍、四捨五入） | 2 | 35.71・1.35 |

合計：4cases、8fields。公式の40問を回答欄数に読み替えません。

## 原本・証跡
- 公式問題：https://www.jafp.or.jp/exam/mohan/files/j2_202605_q.pdf
  - SHA-256：`3760b39cbeffc2062de054639a2910b615df63d8b9f592e8dd3e1b368a0d02ef`
- 公式模範解答：https://www.jafp.or.jp/exam/mohan/files/j2_202605_a.pdf
  - SHA-256：`9c3508ba491a84ce97b96157942d63f865084ef2b098359fb425f68728334abd`
- GitHub Actionsによるダウンロードと検証：[実行ログ](https://github.com/donald-shrimp/ap-study/actions/runs/40086059591)。公式PDFの原本バイト列は同RunのArtifactに保存。
- PDFはこのブランチのGitツリーへは **まだ格納していません**。`delivery/sources/fp2/`に2ファイルを配置する場合、必ずハッシュ照合してください。完全な原本を含むZIPはチャット納品物としても作成済み。

`publishedAt`・`legalAsOf`は資料で厳密な日付を確認できていないためnull。現行法令の確認は `unverified` です。

## 検査
作成者のローカル検証：`python tools/check-fp2-delivery.py <delivery>` → `{questions:0,cases:4,fields:8,mode:'draft structure only; not approved'}`。チェックは原本PDF2件を同梱したローカル納品ディレクトリで実行したものであり、上記のPDF欠落状態のGitツリーで同じ検証が通ると主張するものではありません。

## 実施していないこと
- 独立レビュー、`reviewed`昇格、正式な法令の現行確認
- 公式配点の推定、100点換算・合否判定
- 公開資格カタログや本番HTMLの変更、実技問3／問6～40の作成

原本の設問を教材化し、解説・採点説明を追加しています。出典と加工の事実を表示し、第三者引用物は別途取扱いを確認します。
