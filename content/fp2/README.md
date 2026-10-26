# FP2級の作成元

日本FP協会の2026年5月公表分と2025年1月26日実施分を、各学科60問・実技40問ずつ収録。合計は学科120問・実技80問（136回答欄）。2026年5月の学科法令基準は2025-04-01、実技は推定せずnull。2025年1月の学科・実技は原本指定の2024-10-01。

学科の公開作成元は `questions.json`、確認台帳は `question-reviews.json`。実技は `practical-cases.json` と `practical-reviews.json`。元の草稿と確認経緯は学科を `delivery/`、実技を `deliveries/fp2-jafp-202605-samples/` に保持する。公開範囲・出典は [FP2級の出典](../../docs/FP2-SOURCES.md) を参照。

学科の解説改訂版は `work/fp2/revisions/202605-objective-v2/` の草稿・修正来歴・独立レビューを正本とし、確認済み60問を公開作成元へ反映した。初回公開の確認台帳も同フォルダの `review/previous-publication-reviews.json` に保持する。問題ID・原文・正答・原本と法令基準はそのまま、教材版を1増やしている。

作成・納品形式は [外注用手順](../../docs/fp2-authoring.md)。ヒントの新規作成・既存教材の改稿は [共通ルール](../../docs/hint-authoring.md)を使う。科目ID・分野IDは `qualification.json` を使う。

学科60問に共通ルールによる2段ヒント120件を追加した。最新のヒント改訂と独立レビューは [`work/fp2/revisions/202605-objective-hints-v3/`](../../work/fp2/revisions/202605-objective-hints-v3/README.md)を参照。上記の解説改訂版と直前の公開問題・レビューは保持する。

2025年1月分は [`work/fp2/historical/202501/`](../../work/fp2/historical/202501/README.md) の最終草稿と独立確認台帳を正本とする。公開元には状態だけをreviewedにした同一内容を追加し、既存2026年5月分のID・版・全内容と確認台帳を保持した。学科は2段ヒント120件を追加。実技の学習用図8点・9配置を採用し、原本ページ画像は任意のオンライン参照へ分離。各試験回はカタログとオフライン保存でも分けている。
