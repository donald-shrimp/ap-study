# batch-07：20問

この組だけを担当する。公開用データへの統合は統合担当が行う。品質基準と共通の納品・レビュー手順は [作業手順](../../../../../docs/ap-a-content-upgrade.md) を読む。

- `assignment.json`：対象IDと担当。
- `context.json`：問題文・全選択肢・公式正答・原本参照。画像を開き、全文と図を確認する。
- `drafts.json`：改稿の納品先。初期値は旧教材のコピーであり、新基準の確認済みではない。
- `reviews.json`：別担当の確認台帳。作者は承認を記入しない。

```sh
python tools/ap-lesson-quality.py claim batch-07 --author '実際の担当名'
python tools/ap-lesson-quality.py check batch-07
python tools/ap-lesson-quality.py check batch-07 --reviewed
```

## 対象

| ID | 分野 | 論点 | 原本画像 |
| --- | --- | --- | --- |
| r06a-q12 | コンピュータ構成 | 待機系とセッション | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q12.webp) |
| r05h-q12 | コンピュータ構成 | 有機ELの表示原理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q12.webp) |
| r07a-q12 | コンピュータ構成 | 構成をコードで管理 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07a/r07a-q12.webp) |
| r05a-q8 | コンピュータ構成 | 異なる種類のコア | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q8.webp) |
| r07h-q13 | コンピュータ構成 | 直並列の稼働率グラフ | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q13.webp) |
| r03a-q11 | コンピュータ構成 | 磁気ディスクの読取り時間 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q11.webp) |
| r07h-q12 | コンピュータ構成 | 稼働率と故障・修復時間 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q12.webp) |
| r03a-q8 | コンピュータ構成 | 符号付き加算のオーバーフロー | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03a/r03a-q8.webp) |
| r03h-q8 | コンピュータ構成 | 統計解析用の言語 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r03h/r03h-q8.webp) |
| r06h-q8 | コンピュータ構成 | 重なる領域のブロック転送 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q8.webp) |
| r06h-q9 | コンピュータ構成 | 量子ビットと重ね合わせ | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06h/r06h-q9.webp) |
| r06a-q9 | コンピュータ構成 | 量子超越性 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r06a/r06a-q9.webp) |
| r04a-q11 | コンピュータ構成 | 電気泳動型電子ペーパー | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q11.webp) |
| r05h-q14 | システム構成・OS | CPUとディスクの使用率 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q14.webp) |
| r05h-q17 | システム構成・OS | FIFOのページ表 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05h/r05h-q17.webp) |
| r05a-q14 | システム構成・OS | IaCの構成記述 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q14.webp) |
| r07h-q15 | システム構成・OS | LRUのページ置換え | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q15.webp) |
| r05a-q19 | システム構成・OS | Linuxカーネルの役割 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r05a/r05a-q19.webp) |
| r04a-q14 | システム構成・OS | MTBFとMTTRの同倍率変更 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r04a/r04a-q14.webp) |
| r07h-q16 | システム構成・OS | OSSライセンスの公開範囲 | [原本](https://donald-shrimp.github.io/ap-study/assets/questions/r07h/r07h-q16.webp) |

## 作者への依頼文

この組の20問について、原本画像・公式正答・全選択肢を読み、現在のヒントと解説を点検してください。`docs/hint-authoring.md` と `docs/explanation-authoring-rules.md` を正本とし、各問を keep／revise／rewrite に分類してください。使える文章を残し、つまずき・各段階の新情報・本人に残る判断・開示フラグの理由を design に記録します。3段のヒント、全4肢の理由、要約・解説・要点を一緒に確認します。答えを実質的に教える段階はtrue。文量・装飾・段数を埋めるための改稿はしません。作者名を実名または実際の一意な担当IDで記録し、この組の drafts.json のみを改稿してください。原本・基準・計算を確認できない問題は保留理由を別記し、未確認のまま完成させないでください。公開JSON・共通ルール・baseline・他の組は変更しません。

## 別担当レビューへの依頼文

作者とは別の担当として、原本から解き直した後、修正後の全20問・全4肢の理由・全60ヒントと設計メモを読み直してください。用語や式を知らない人が新しい情報を得られるか、前段との組合せも含め答えを渡すかを確認します。計算・図・単位・条件・出題時点を再照合し、指摘は作者へ返し、修正後に再確認します。実際に読んだ最終版だけに、手順書の契約に従った実ハッシュ・確認日時・根拠・作者と異なる確認者を reviews.json へ記録してください。keepにも新基準の確認が必要です。自分で教材を直した場合、その項目を自分で独立承認しません。

原本画像を開けないなどの不足があれば、実施できなかった内容と対象IDを残して保留します。形式チェックの成功を内容承認と呼びません。
