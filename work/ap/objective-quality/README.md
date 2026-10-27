# AP科目A：ヒント・解説の品質改訂

800問の旧教材と旧レビューをbaselineへ保存し、先行20問と残り39組×20問へ重複なく分割した。旧レビューの状態を新基準の承認には使わない。

先行20問は19問を部分修正、1問を変更不要として全件の独立確認・登録・実アプリ検証を完了。残り780問のうちbatch-01〜04の80問は4担当で改稿・別担当確認・登録を完了。batch-05〜08の次の80問も改稿・別担当確認・登録を完了し、計180問を新基準で確認済み。残り620問のうちbatch-09〜13の100問は独立レビューを完了し、batch-09の修正後確認を含め内容承認・未登録。残り520問の26組はこのブランチでは未着手。別ブランチで進行中の納品は各PRで確認する。教材は[PR #76](https://github.com/donald-shrimp/ap-study/pull/76)と[PR #77](https://github.com/donald-shrimp/ap-study/pull/77)と[PR #78](https://github.com/donald-shrimp/ap-study/pull/78)に保存し、本番公開はまだ行っていない。

- [全体計画・作者／レビュー／統合の手順](../../../docs/ap-a-content-upgrade.md)
- [800問の固定台帳](inventory.json)
- [担当と進捗のスナップショット](progress.json)
- [旧教材・旧確認記録](baseline/)
- [登録した確認済みの組](registrations.json)

自分に割り当てられた1組だけを担当する。作者はその組のassignment/drafts、確認者はreviewsを使い、共有の年度別教材や全体進捗へ同時に書き込まない。統合担当が承認確認後に順次取り込む。

| 組 | 問数 | 分野 | 担当 |
| --- | --- | --- | --- |
| [pilot-00](batches/pilot-00/README.md) | 20 | 基礎理論、アルゴリズム・プログラミング、コンピュータ構成、システム構成・OS、ハードウェア、インタフェース・マルチメディア、データベース、ネットワーク、セキュリティ、開発技術、プロジェクトマネジメント、サービスマネジメント・監査、システム戦略、経営戦略、企業活動、法務、論理回路 | Codex /root |
| [batch-01](batches/batch-01/README.md) | 20 | 基礎理論 | 作者 1 ／ 確認者 2（独立確認・登録済み） |
| [batch-02](batches/batch-02/README.md) | 20 | 基礎理論、論理回路 | 作者 2 ／ 確認者 3（独立確認・登録済み） |
| [batch-03](batches/batch-03/README.md) | 20 | 論理回路、アルゴリズム・プログラミング | 作者 3 ／ 確認者 4（独立確認・登録済み） |
| [batch-04](batches/batch-04/README.md) | 20 | アルゴリズム・プログラミング、コンピュータ構成 | 作者 4 ／ 確認者 1（独立確認・登録済み） |
| [batch-05](batches/batch-05/README.md) | 20 | コンピュータ構成 | 作者 1 ／ 確認者 2（独立確認・登録済み） |
| [batch-06](batches/batch-06/README.md) | 20 | コンピュータ構成 | 作者 2 ／ 確認者 3（独立確認・登録済み） |
| [batch-07](batches/batch-07/README.md) | 20 | コンピュータ構成、システム構成・OS | 作者 3 ／ 確認者 4（独立確認・登録済み） |
| [batch-08](batches/batch-08/README.md) | 20 | システム構成・OS | 作者 4 ／ 確認者 1（独立確認・登録済み） |
| [batch-09](batches/batch-09/README.md) | 20 | システム構成・OS | ChatGPT作者 ／ Codex確認（20問内容承認・未登録） |
| [batch-10](batches/batch-10/README.md) | 20 | システム構成・OS、ハードウェア | ChatGPT作者 ／ Codex確認（20問内容承認・未登録） |
| [batch-11](batches/batch-11/README.md) | 20 | ハードウェア | ChatGPT作者 ／ Codex確認（4問修正・別担当再確認、20問内容承認・未登録） |
| [batch-12](batches/batch-12/README.md) | 20 | ハードウェア、インタフェース・マルチメディア | ChatGPT作者 ／ 別担当確認（20問内容承認・未登録） |
| [batch-13](batches/batch-13/README.md) | 20 | データベース | ChatGPT作者 ／ 別担当確認（7問修正・20問内容承認・未登録） |
| [batch-14](batches/batch-14/README.md) | 20 | データベース | 未割当 |
| [batch-15](batches/batch-15/README.md) | 20 | データベース、ネットワーク | 未割当 |
| [batch-16](batches/batch-16/README.md) | 20 | ネットワーク | 未割当 |
| [batch-17](batches/batch-17/README.md) | 20 | ネットワーク、セキュリティ | 未割当 |
| [batch-18](batches/batch-18/README.md) | 20 | セキュリティ | 未割当 |
| [batch-19](batches/batch-19/README.md) | 20 | セキュリティ | 未割当 |
| [batch-20](batches/batch-20/README.md) | 20 | セキュリティ | 未割当 |
| [batch-21](batches/batch-21/README.md) | 20 | セキュリティ | 未割当 |
| [batch-22](batches/batch-22/README.md) | 20 | セキュリティ、開発技術 | 未割当 |
| [batch-23](batches/batch-23/README.md) | 20 | 開発技術 | 未割当 |
| [batch-24](batches/batch-24/README.md) | 20 | 開発技術 | 未割当 |
| [batch-25](batches/batch-25/README.md) | 20 | 開発技術、プロジェクトマネジメント | 未割当 |
| [batch-26](batches/batch-26/README.md) | 20 | プロジェクトマネジメント | 未割当 |
| [batch-27](batches/batch-27/README.md) | 20 | プロジェクトマネジメント、サービスマネジメント・監査 | 未割当 |
| [batch-28](batches/batch-28/README.md) | 20 | サービスマネジメント・監査 | 未割当 |
| [batch-29](batches/batch-29/README.md) | 20 | サービスマネジメント・監査 | 未割当 |
| [batch-30](batches/batch-30/README.md) | 20 | サービスマネジメント・監査、システム戦略 | 未割当 |
| [batch-31](batches/batch-31/README.md) | 20 | システム戦略 | 未割当 |
| [batch-32](batches/batch-32/README.md) | 20 | システム戦略、経営戦略 | 未割当 |
| [batch-33](batches/batch-33/README.md) | 20 | 経営戦略 | 未割当 |
| [batch-34](batches/batch-34/README.md) | 20 | 経営戦略 | 未割当 |
| [batch-35](batches/batch-35/README.md) | 20 | 経営戦略 | 未割当 |
| [batch-36](batches/batch-36/README.md) | 20 | 経営戦略、企業活動 | 未割当 |
| [batch-37](batches/batch-37/README.md) | 20 | 企業活動 | 未割当 |
| [batch-38](batches/batch-38/README.md) | 20 | 企業活動、法務 | 未割当 |
| [batch-39](batches/batch-39/README.md) | 20 | 法務 | 未割当 |

batch-09の[PR #81](https://github.com/donald-shrimp/ap-study/pull/81)は[初回レビュー](batches/batch-09/review/independent-review.json)の2件をCodexが修正し、[修正後の別担当確認](batches/batch-09/review/correction-independent-review.json)も完了。20問の内容承認は登録・公開済みを意味しない。残り520問の26組はこのブランチでは未着手。別ブランチで進行中の納品は各PRで確認する。80問の作者と確認者は各組のassignmentに記録し、実際の進捗は[第1回の記録](review/batch-wave-01.json)と[第2回の記録](review/batch-wave-02.json)に保存する。分割・旧教材の配布は内容の承認を意味しない。各組で元の試験回をまたぐ場合があるため、基準日・条件・選択肢に応じて個別に点検する。

第2回で判明したr04a-q13の文字起こし誤記2箇所は、独立確認済みの内容を[訂正台帳](source-corrections.json)で反映し、問題版を3から4へ更新した。旧文字起こし・旧レビュー・baseline・旧学習記録は保持。[訂正後の画面・保存検証](review/source-correction-application/results.json)を保存している。

batch-10は[PR #82](https://github.com/donald-shrimp/ap-study/pull/82)で20問の[独立レビュー](batches/batch-10/review/independent-review.json)を完了。batch-09と合わせ40問が内容承認・未登録。現在の組別・件数別状態はprogress.jsonを参照。

batch-11は[PR #83](https://github.com/donald-shrimp/ap-study/pull/83)で20問の[独立レビュー](batches/batch-11/review/independent-review.json)を完了。4問の不備は修正者と異なる担当が最終確認し、内容承認・未登録。

batch-12は[PR #84](https://github.com/donald-shrimp/ap-study/pull/84)で20問の[独立レビュー](batches/batch-12/review/independent-review.json)を完了。根拠と最終ハッシュは実確認者の記録を保持。batch-13は[PR #85](https://github.com/donald-shrimp/ap-study/pull/85)で7問を修正し、[修正後の別担当確認](batches/batch-13/review/correction-independent-review.json)を含め20問の内容承認を完了。
