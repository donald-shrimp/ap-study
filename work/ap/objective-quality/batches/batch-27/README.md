# batch-27：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-27 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-27
python tools/ap-lesson-quality.py check batch-27 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r04a-q54 | プロジェクトマネジメント | 加重総和による評価 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q54.webp) |
| r07h-q55 | プロジェクトマネジメント | 可用性目標と短縮時間 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q55.webp) |
| r03a-q54 | プロジェクトマネジメント | 問題管理の活動 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q54.webp) |
| r04a-q55 | プロジェクトマネジメント | 問題管理の目的 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q55.webp) |
| r03h-q54 | プロジェクトマネジメント | 好機の強化戦略 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q54.webp) |
| r07a-q53 | プロジェクトマネジメント | 引継ぎを含む増員費 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q53.webp) |
| r07a-q55 | プロジェクトマネジメント | 故障原因と確率の分析 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q55.webp) |
| r05a-q55 | プロジェクトマネジメント | 是正処置と再発防止 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q55.webp) |
| r06h-q52 | プロジェクトマネジメント | 最早結合点時刻 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q52.webp) |
| r03a-q55 | プロジェクトマネジメント | 月単位のバックアップ保管 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q55.webp) |
| r04a-q53 | プロジェクトマネジメント | 生産性を換算した工程期間 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q53.webp) |
| r05h-q55 | プロジェクトマネジメント | 継続的改善 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q55.webp) |
| r03h-q51 | プロジェクトマネジメント | 計画のプロセス群 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q51.webp) |
| r06h-q55 | プロジェクトマネジメント | 課金案の年間利益 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q55.webp) |
| r05h-q53 | プロジェクトマネジメント | 配分モデルと進捗率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q53.webp) |
| r04h-q57 | サービスマネジメント・監査 | DAとDBAの分担 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q57.webp) |
| r06h-q57 | サービスマネジメント・監査 | GHGのスコープ1 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q57.webp) |
| r04a-q58 | サービスマネジメント・監査 | ISMSのリスク受容基準 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q58.webp) |
| r05a-q60 | サービスマネジメント・監査 | ITへの対応と内部統制 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q60.webp) |
| r05h-q57 | サービスマネジメント・監査 | IaaS・PaaSの運用分担 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q57.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
