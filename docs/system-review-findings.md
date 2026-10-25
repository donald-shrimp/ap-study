# 全体改善レビュー・初回点検記録

2026-10-25 · 基準 `0e6aeac6453b7cdb015a58438733ffaad2502a6c`。管理 [Issue #57](https://github.com/donald-shrimp/ap-study/issues/57) · [計画](system-review-plan.md) · [測定記録](audits/system-review-20261025.json)。

## 結果と修正順

初回の横断点検で7件を登録した。P0の記録消失・重大な誤採点は今回の再現では確認していない。既存テストの成功を、あらゆる操作・端末での安全性の保証とは扱わない。

| ID | 優先度 | 改善点 | Issue | 状態 |
| --- | --- | --- | --- | --- |
| F07 | P1 | 共通CIの不足と保存系テスト3本の現行仕様とのずれ | [#64](https://github.com/donald-shrimp/ap-study/issues/64) | 初回修正対象 |
| F01 | P1 | ログアウト失敗後、同じUIDのまま全同期が停止する | [#58](https://github.com/donald-shrimp/ap-study/issues/58) | 実装・ローカル検証済み（反映証跡はIssue） |
| F02 | P1 | 保存済み画像も弱回線のネットワーク応答を待つ | [#59](https://github.com/donald-shrimp/ap-study/issues/59) | 実装・ローカル検証済み（反映証跡はIssue） |
| F03 | P2 | 新inventoryから削除しても旧版だけの画像が残る | [#60](https://github.com/donald-shrimp/ap-study/issues/60) | 未修正 |
| F04 | P2 | workspace系同期のカーソルが起動後に引き継がれない | [#61](https://github.com/donald-shrimp/ap-study/issues/61) | 未修正 |
| F05 | P2 | FP実技の同期対象も「科目B」と表示する | [#62](https://github.com/donald-shrimp/ap-study/issues/62) | 未修正 |
| F06 | P2 | 図内参照など6件のbodyRefsが実DOMに解決しない | [#63](https://github.com/donald-shrimp/ap-study/issues/63) | 未修正 |

まずF07で保存と更新の検証を自動化する。その後、F01→F02を別の小PRで直す。F04のカーソル導入は文書保存との整合が必要で、速度だけを理由にカーソルを先に進めない。

## 点検した範囲

| 対象 | 実施内容 | 結果・留保 |
| --- | --- | --- |
| R1 保存・同期 | local/workspace/cardsの保存、送信待ち、CAS、遅いACK、account切替、バックアップの保存順を読んだ。実IndexedDBの通常保存・2タブ競合・故障注入、合成Auth失敗を実行 | storage.py成功。F01/F04。全体バックアップがDB横断で原子的ではない点は既存の部分完了・再試行仕様と区別。本番の本人別端末照合・全Rulesのエミュレーター試験は今回未実施 |
| R2 起動・更新・オフライン | catalog/readJSONのSHA照合、SWのcache経路とリリース更新、offline-storeの保存・削除を読んだ。実SWの遅延応答、PWAの更新・記録保持・オフラインを確認 | PWA成功。F02は保存済みでも1.5秒の合成遅延を1506ms待機。F03はgroup台帳削除後も旧画像が残る。F04は同期処理の負荷であり、画面が必ず同期待ちになるとは断定しない |
| R3 学習体験 | 通常出題・復習・大問キュー、集計の分母、欄ごとの自動判定/自己評価と開示条件を読んだ。科目B・FP実技の一括確定、空欄、支援フラグ、最後に開示、保存と再開を操作 | 関連domain、一括操作と開示条件のブラウザ試験成功。学習効果や合格判定の妥当性を今回測定したものではない。長期の復習間隔・大量履歴での学習バランスは継続点検 |
| R4 共通設計 | src/app.jsの機能接続とアカウント切替、共通cases/queue、資格・科目定義、同期表示を読んだ | F05。app.jsは約72KBで接続責務が集中するが、サイズだけでは分割Issueを作らない。F01等の原因箇所を直す際に責務の境界を検討 |
| R5 教材管理 | build、公開ゲート、レビューSHA、図の順序、原本ハッシュ、生成物、追加手順を確認。AP/FP/共通教材の契約・故障入力の拒否を実行 | 教材ゲート6本成功。128大問・404参照のDOM解決は398件。F06の6件は各item先頭参照ではなく、現在の参照ボタンが6個壊れているという意味ではない。図内文字を含む。新規内容レビュー・現行法令レビューは今回の対象外 |
| R6 UI/操作 | 科目A基準の色・文字・主操作との比較、320/390/1440px、選択のキーボード、入力保持、解説開示を検証 | design-language.py成功。F05/F06。本番端末の読み上げソフト、iOS/Android全ブラウザの実機確認は未実施 |
| R7 開発・検証 | 全workflow、domainテスト36ファイル、保存系ブラウザテスト、生成と公開確認の手順を確認 | Node283件成功。古いテスト3本の失敗を確認しF07へ。Pagesのデプロイ成功と保存・同期CI成功を分けて管理 |

## 初回修正 F07

製品の画面・教材・保存形式・Rulesを変えず、保存系の回帰検証を現行仕様へ戻す。

- `tests/workspace.py`：現行値と同じ値を変更とみなす前提を除き、必ず別のvariant limitに変更する。保存前後はキーの列挙順に依存しないcanonical比較で、出題方針と教材の凍結を検証する。
- `tests/learning-storage-race.py`：資格選択画面ではなくAP科目Aへ入る。同期の入力も実際のv2 wire recordにする。競合しても回答を分岐せず、ヒントと元端末と送信待ちを保持する検証は残す。
- `tests/subject-b-saving.py`：おすすめ順に依存せず対象の公式問を指定する。容量不足時の入力保持→バックアップ救出→再試行→再読込を検証する。
- `Shared application validation`：src/storage・src/syncを含む共通変更でPRとmainの検証を起動。全domainテスト、公開契約、実ブラウザの保存/救出/更新/共通学習画面を実行する。従来のFP草稿検証は保持する。

Rulesの実行にはFirebase Emulatorが必要なので、通常のNode全件からは `tests/firebase-rules.mjs` だけを明示除外する。今回そのテストを成功したものとして数えない。新CIは検証を実行・可視化するもので、既存Pages自動デプロイやブランチ保護の設定自体は変更しない。

## 再現と検証方法

初回の合成Auth失敗・実SW遅延・参照DOM・ストアAPIの観測を再実行するには、PlaywrightとChromiumのある環境で次を実行する。結果は一時フォルダへ出力する。既知Issueを再観測するスクリプトなので、将来の修正後には値が変わる。

```sh
python docs/audits/system-review-20261025.py
```

初回基準で実行した教材チェックは `tools/build-content.py`、`tests/common-content.py`、`tests/written-content.py`、`tests/fp2-content.py`、`tests/fp2-review-gates.py`、`tests/offline-content.py`。すべて成功。公開ゲートの異常入力テストでは意図的な拒否ログが出るため、ログ中のError文字列だけで失敗とせず、各プロセスの終了コードと最終判定を確認した。

実施結果と次の対象は [進捗JSON](system-review-progress.json) に記録する。未公開教材PR、個人記録、本番の認証情報には変更を加えない。
