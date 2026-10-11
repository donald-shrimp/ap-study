# 文字起こしキュー（ChatGPT作成 → 手動指示でCodexレビュー）

## 目的

OpenAI APIや常駐サーバーを使わず、ChatGPTが原本画像を読んだ**未レビュー草稿**をGitHubのDraft PRとして蓄積する。Codexは利用者からレビューを指示されたときだけ処理する。未確認草稿はmainの公開教材へ直接反映しない。

既存ルール：[原本の文字起こし](transcription-authoring.md) と [AGENTS.md](../AGENTS.md) が優先。進捗の正本は `data/transcription-progress.json`。このファイルのレビュー済み、画像維持、未処理数を毎回再読込し、チャット上の古い件数を信じない。

## キューのルール

- 一つのPRは**同じ試験回の1〜20問**。通常は10問。作成ブランチは `transcription/<batchId>`、例 `transcription/r05a-q21-30`。
- **予約状態はGitHubの「開いているtranscription/ブランチのPR」から取得する**。専用DBも更新競合する共有キューファイルも持たない。
- PRには `data/transcription-queue/<batchId>.json` と `data/transcription-drafts/chatgpt_<batchIdのハイフンをアンダースコアに置換>.json` を入れる。
- マニフェストは回答テキストを含まない予約情報。草稿は従来の `hitomon-markdown-math-v1` 形式。草稿を確認済み教材と偽らない。
- 草稿化が困難な問題は `skipProposals` に対象IDと具体的な理由を記録する。これは**スキップ提案**であり、Codexの判断前に正式な画像維持・レビュー済み数へ計上しない。
- ブランチは最新mainから作る。レビュー済み問題、画像維持済み問題、他の開いているキューPRの予約済み問題を重複登録しない。
- PRをマージせず閉じた場合は予約解除となり、再び未処理候補になる。処理済みとなるのは、レビューや画像維持処理がmainに正式反映された場合だけ。
- GitHub APIが利用不能、PRの予約ファイルが不正、二重予約、進捗の件数が不整合なら**失敗として止める**。他のPRを確認できない状況で勝手に次の問題を確定しない。
- 同時に二つの作成者が候補を確保する操作は原子的ではない。基本はChatGPTの単一作成者で運用し、PR作成直後にも重複チェックを行う。

## ChatGPT側の操作

```sh
node tools/transcription-queue.mjs status
node tools/transcription-queue.mjs next --count 10
```

`status` / `next` / `check` はGitHubの最新mainのSHAを取得し、同じSHAの `data/transcription-progress.json` とカタログ、GitHubにある全open PRを読み、次の問題ID、推奨ブランチ名、マニフェストの雛形をJSON表示する。取得中にmainが変わったら停止する。ローカルの古い進捗を最新として扱わない。**表示するだけでPR・教材・学習記録は変更しない**。

Node.js 24.5以上を推奨。プロキシ設定がある環境では、継承したHTTP_PROXY / HTTPS_PROXYを標準APIで使用する。対応していないNodeでは直接通信へ逃げず、エラーで停止する。

例（2026-10-12のmainを参照した場合）：

- 確認済み498問、画像維持2問、処理済み合計500問、残り300問
- 最初の候補は `r05a-q21`〜`r05a-q30`

次に原本画像を読み、1問ずつ原文と選択肢を草稿に保存する。見えない文字・図は推測せず、理由付きskip提案とする。未処理のみを作業ブランチへコミットし、**Draft PR**を作成する。PR本文には収録ID、原本参照、未確定箇所、Codex確認事項を記す。リリースコードやFirebase、既存問題の採点情報は変更しない。

マニフェストの例：

```json
{
  "format": "hitomon-transcription-queue",
  "version": 1,
  "batchId": "r05a-q21-30",
  "questionIds": ["r05a-q21", "r05a-q22", "r05a-q23", "r05a-q24", "r05a-q25", "r05a-q26", "r05a-q27", "r05a-q28", "r05a-q29", "r05a-q30"],
  "author": "ChatGPT",
  "status": "awaiting-review",
  "draftFile": "data/transcription-drafts/chatgpt_r05a_q21_30.json",
  "skipProposals": []
}
```

草稿レコードのフィールドは従来の `docs/transcription-authoring.md` に従う。元画像のSHA-256を記録し、レビューではそれを**実ファイルと照合**する。

## Codex側の操作（利用者が明示指示してから）

```sh
node tools/transcription-queue.mjs status
node tools/transcription-queue.mjs check --manifest data/transcription-queue/r05a-q21-30.json --draft data/transcription-drafts/chatgpt_r05a_q21_30.json
node --test tests/transcription-queue.mjs tests/transcription-queue-cli.mjs
```

`check` は予約ID、草稿の件数・形式・選択肢・記録済み原本ハッシュの**構造だけ**を検証する。正しい文字起こしであることは証明しない。Codexは作成者とは独立にIPA原本を開き、全文・数式・表・図・選択肢を照合し、必要なら修正する。

確認できた草稿だけ既存の `data/transcriptions/` と `data/transcription-reviews/` に統合し、`tools/apply-transcriptions.py` で公開教材へ反映する。その後、少なくとも以下を実行する。

```sh
python tests/transcriptions.py
python tests/corpus.py
python tests/content.py
```

失敗したらマージしない。画像維持・スキップの最終判断もCodexで独立に確認し、進捗の正本へ反映する。レビュー結果、適用スクリプトの実行結果、既存教材・採点・画像・学習記録の保持をPRに記録する。テスト成功・レビュー完了・コンフリクト解消後にだけマージし、GitHub Pagesのデプロイ結果を確認する。

## オフライン診断

`--offline` はローカル進捗を使い、GitHub PRを読まずに候補を試算するための診断専用。出力の `safeToEnqueue` は `false` となる。これを根拠に作成PRを確定してはいけない。

GitHubの公開APIは追加のOpenAI API課金を必要としない。利用枠、APIのアクセス制限、ネットワークや実機の制約は別途考慮する。

## 当面の使い方

ChatGPTへ「ひと問の文字起こしを次の10問キューに入れて」と依頼する。ChatGPTはその応答内で草稿・PRを作る（応答後にバックグラウンド処理は続けない）。利用者が任意のタイミングでCodexへ「未レビューのtranscription/ PRを古い順にレビューし、確認できた分のみ反映・マージして」と依頼する。
