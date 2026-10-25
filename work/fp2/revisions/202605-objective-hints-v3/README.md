# FP2級・2026年5月公表 学科60問 — ヒント追加

全60問に問題別の2段ヒント、計120件を追加する。[全資格共通ルール](../../../../docs/hint-authoring.md)に従い、入口で知識や見方を教え、次に定義・制度要件・公式・途中式へ進む。

- 作者：Codex `/root`。確認者：作者と別エージェントの `/root/fp2_202605_hint_reviewer`。
- 原本：`sources/fp2/g2_202605_qa.pdf`。法令基準は2025-04-01。原本・法令状態・全問題文・全肢・正答・既存解説・図は変更しない。
- 各問は旧版から1増やすため、完成版のversionは3または4。フォルダ名は今回の改訂段階名であり、版を全問同じ数に揃えるものではない。
- 第1ヒントは全問非開示。第2ヒントは7問（14・26・27・28・33・55・57）で最後の計算・比較・人数判断を残し、53問で正答と実質同じ知識を教えるため `revealsAnswer:true` とする。

## 作成・確認記録

- `author-hints-qXX-qYY.json`：作者が各問のヒント・開示判定・設計メモを記述。
- `prepare-drafts.py`：作者の記述と旧版から未確認草稿を作成する。内容承認やレビュー記録を生成しない。
- `drafts/`、`author-notes-*.json`：問題別の未確認時点の草稿と設計メモ。
- `review/previous-publication-questions.json`、`previous-publication-reviews.json`：直前の公開問題と旧レビューを保持。
- `review/source-index.json`：レビュワーが公式PDFから独立抽出した問番号・ページ・正答の対応。
- `review/independent-*.json`、`publication-reviews-*.json`：10問単位の独立内容確認と公開用台帳。
- `review/final-integrity.json`：全60問の最終版・正規化後ハッシュ、原本・図の保持、許可差分を照合した総括。
- `accepted-questions.json`：別担当の承認ハッシュと一致する採用版。
- `progress.json`：作成・レビュー・検証・公開の実際の進捗。

レビューで問8の所得控除前後の表現、問17の火災保険の対象範囲、問20の原本にない前提、問46の高さ表現を修正し、修正後に再確認した。未変更の既存解説等は差分がないことと従来の確認記録を照合した。完全盲検、初学者による試用、現行法令の網羅確認とは称さない。

進行中の歴史問題PR48・49は既存担当の作業を維持し、今回の追加対象に含めない。

## 検証

```sh
python tools/build-content.py
python tests/fp2-content.py
python tests/fp2-review-gates.py
python tests/fp2-revision-published.py
```

内容承認とは別に、実画面で全120ヒントの表示、開く前の開示表示、採点、途中の選択・ヒント保持、オフライン保存、バックアップと旧版保持を確認する。旧版のヒントが0件でも、確認済みの新教材へ移る既存の「最新のヒントで続ける」を使えるようにする。旧記録の回答・支援履歴は書き換えない。
