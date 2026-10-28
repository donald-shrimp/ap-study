# batch-15：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-15 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-15
python tools/ap-lesson-quality.py check batch-15 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r07a-q29 | データベース | 複数の版と同時実行 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q29.webp) |
| r03a-q30 | データベース | 複製への透過性 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q30.webp) |
| r05h-q30 | データベース | 親の削除と連動する参照制約 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q30.webp) |
| r07h-q27 | データベース | 親の削除と連動する参照制約 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q27.webp) |
| r03a-q26 | データベース | 関係の和集合 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q26.webp) |
| r04a-q27 | データベース | 関係の差集合 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q27.webp) |
| r05a-q30 | データベース | 障害時のundoとredo | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q30.webp) |
| r04a-q33 | ネットワーク | /29のアドレス範囲 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q33.webp) |
| r03h-q36 | ネットワーク | 2.4GHzのチャネル干渉 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q36.webp) |
| r03a-q32 | ネットワーク | ARPで解決する対応 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q32.webp) |
| r06a-q36 | ネットワーク | ARPキャッシュの確認 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q36.webp) |
| r07h-q34 | ネットワーク | Base64によるサイズ増加 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q34.webp) |
| r06h-q30 | ネットワーク | CSMA/CDの送信 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q30.webp) |
| r04a-q31 | ネットワーク | DHCPの配布情報 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q31.webp) |
| r06a-q33 | ネットワーク | DNSのレコードと逆引き | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q33.webp) |
| r03a-q31 | ネットワーク | Ethernetのブロードキャスト | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q31.webp) |
| r06a-q34 | ネットワーク | ICMPの役割 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q34.webp) |
| r03h-q33 | ネットワーク | IEEE 802.11acの帯域 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q33.webp) |
| r06h-q31 | ネットワーク | IPv4のアドレス種別 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q31.webp) |
| r04h-q31 | ネットワーク | IPv6の省略表記 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04h/r04h-q31.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。

## 独立レビューと修正

作者head `d9a51576009008ee3b43f807f5c8d2bf0d408986` の20原本・10回分の公式解答PDF・80肢・60ヒントを別担当が独立確認。初回草稿と実ハッシュを固定した後、主担当がr03a-q32・r06a-q36・r06h-q30・r06a-q34の第1ヒントを解答開示へ訂正した。修正者とは別担当が最終20件を確認し、reviews.jsonへ最終ハッシュを保存した。[初回記録](review/independent-review.json)と[最終確認](review/correction-independent-review.json)を参照。SQL/集合演算/回復図/CIDR/Base64/アドレスを検算し、全20問×ヒント0〜3段の80通りで採点と回答後の結果保持を確認した。未登録・未マージ・未公開。
