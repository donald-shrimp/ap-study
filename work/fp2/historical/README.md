# FP2級・歴史的過去問 草稿生成／検証ツール

## 分割方針

元の巨大Draft [#38](https://github.com/donald-shrimp/ap-study/pull/38) に含まれていた **2025年1月・2024年9月・2024年5月の教材作成元／ツール／アプリ変更**を、現在の `main` と競合させずに分類した。

| 役割 | 分割PR | 試験回 |
| --- | --- | --- |
| 教材 | [#48](https://github.com/donald-shrimp/ap-study/pull/48) | 2025年1月（60学科＋40実技） |
| 教材 | [#49](https://github.com/donald-shrimp/ap-study/pull/49) | 2024年9月（60＋40） |
| 教材 | [#50](https://github.com/donald-shrimp/ap-study/pull/50) | 2024年5月（60＋40） |
| **共通ツール** | このPR | 原本PDFを取得するワークフロー、草稿生成スクリプト、分割後の回別構造検査 |

このPRのツール／ワークフローは **教材をレビュー承認するものではない**。手動実行で元PDFを取得／草稿を生成してアーティファクトに残せるようにする。

### 分割したもの

- `tools/build-fp2-historical-drafts.py`：元#38のスクリプトを同内容で移植。公式PDF取得・テキスト抽出・原本ハッシュ・画像・草稿を再生成する。出力は `deliveries/fp2-jafp-<回>-draft/` であり、**ハンドメイド改訂済み `work/fp2/historical/...` に直接上書きしてはいけない**。
- `.github/workflows/fp2-historical-originals.yml` と `fp2-historical-authoring.yml`：元の単一ブランチ名を対象にした自動push実行をやめ、**`workflow_dispatch` による任意の原本取得／生成**にした。
- `.github/workflows/fp2-historical-progress.yml`：元#38の「2025年1月＋2024年9月が同じブランチに存在する前提」の硬直したテストを廃止。**存在する試験回を個別に検査**し、60＋40件／元PDFハッシュ／出題ID・正答ID・草稿状態／回答欄数を構造確認する。

### 元#38の差分から**意図的に移さないもの**

元#38の`app.js`、`index.html`、`src/ui/views.js`、`src/utils.js`、`styles.css`、`sw.js`には、古いPWAバージョンや旧「解説の太字レンダラー」が含まれている。一方、**現在のmain**ではすでに `src/ui/inline-text.js` と `tests/inline-text.mjs` が太字のHTMLエスケープ付き表示を提供し、`views.js` から利用されている。**古い6ファイルを丸ごと転記すると新しいUI・PWA変更を巻き戻すため、移植しない**。

同様に `tests/answer-format.mjs` は旧 `src/utils.js:answerTextHTML` に依存し、現在のmainの `inlineTextHTML` とテストと重複するためコピーしない。

`docs/content-authoring.md` と `docs/fp2-authoring.md` もmain側に更新済みの新しい作問ガイドが存在するため、古い全文で上書きしない。**解説の合格条件は「何を問う／なぜ答えか／何を覚えるか」、長文を機械的な品質指標にしない**という合意を、各回別READMEに引き継いでいる。

## レビュー担当への残作業

- 生成スクリプトは古い草稿の**再生成器**であり、現在の教材改善を再構成できるとは限らない。生成成果物の `questions.json`・`practical-cases.json` を、手書き改善済みのブランチにコピーしない。
- PDFのSHAは教材PRの `source-files.json` と照合すること。アーティファクト保持期限後の再取得は手動でワークフロー実行。
- 構造検証は**正答の意味・法令適合・画像の品質・説明の教育的品質を確認しない**。3試験回の教材は独立レビューとユーザー承認が必要で、mainへのマージや公開は本PRでは行わない。
- 分割データPRは **mainをベースに独立作成**。共通ツールPRをマージしなくても、レビュー担当は公式PDFと各JSONを直接検証できる。
