# 初学者向けヒントの点検作業

**入口はこのファイル。** [点検基準・得点・重大度](../../../docs/hint-foundations-audit.md)を読み、同じPRの共有ブランチ `audit/ap-a-hint-foundations` へ追記する。[一覧](REPORT.md)は集計時点の表示で、個別レコードが正本。最新一覧はPRの **Hint foundation audit** チェックの成果物にも生成される。

このPRは土台と候補の収集をまとめる。土台作成時の初期状態は **800問未点検、候補0、実点検0**。改稿・登録・マージ・本番公開は行わない。PR #112は別PRとして保持する。旧800問の内容承認や旧担当を、この点検の完了・担当へ読み替えない。

## 最初の区切り

最初は `unit-01` の20問で基準を試す。候補の点数だけでなく、引用・初学者が止まる理由・必要な説明を統合担当と確認する。校正を終えたことを記録してから、複数ワーカーが一人一組20問ずつ進める。今回、校正や全800問点検を開始した扱いにはしない。

`units.json` は既存40組のID分割だけを再利用する。`inventory.json` は今回のmainの教材版・全本文/全肢/全ヒントを含む正規化SHAと元パックを固定する。`manifest.json` は対象main、基準版、基準文書と分割のSHAを保持する。

## 役割と書き込み先

| 役割 | 変更するもの |
| --- | --- |
| 点検担当 | 自分が予約した組の `records/<unit>/<UUID>.json` を一問ずつ追加 |
| 別の確認担当 | `reviews/<UUID>.json` に対象レコードSHAへひも付く確認を追加 |
| 統合担当 | 予約の調整、担当交代、一覧・PR本文の集計更新、指摘の裁定 |

全員が `manifest.json` / `inventory.json` / `units.json`、教材・原問・生成パック・旧レビュー・個人記録を保持する。予約・提出・確認は公開後に編集/削除せず、新しいファイルを追記する。候補を直す場合も元の提出を残し、`supersedes` に直前のレコードSHAを渡す。異なる人の採点を平均したり、強い指摘だけを残したりしない。

## 同時作業での予約

ローカルの排他作成は同じファイルシステム内だけに効く。別端末・別worktree間の担当予約は、**同じ共有ブランチへのコミットが非forceで保存され、予約の担当名を再取得で確認できてから成立**する。

1. 共有ブランチの最新headをfetchし、`report` で未予約の組を選ぶ。専用worktree/ローカルブランチで作業し、進行中の他者のツリーを変更しない。
2. `claim` で一組だけ予約する。予約ファイルだけを、取得したheadを親にしたコミットとして共有ブランチへ保存する。
3. 同じ組を二人が取った場合は先に保存できた予約が有効。保存失敗時はfetchして予約を読み直し、他者が取っていればその組で作業を始めない。
4. 保存した予約を再取得し、担当が自分であることを確認してから本文を読む。`submit` は取得済みrefに同じ予約が存在することも検証する。

```sh
git fetch origin audit/ap-a-hint-foundations
# 作業用ブランチは毎回異なる名前にする。既存の作業ブランチは上書きしない。
git switch -c audit-local/alice-01 origin/audit/ap-a-hint-foundations
python tools/hint_foundations_audit.py report
python tools/hint_foundations_audit.py claim unit-01 --worker '実担当名・実行を識別できる名前'
git add work/ap/hint-foundations/claims/unit-01.json
git commit -m 'Reserve hint foundation audit unit-01'
git push origin HEAD:audit/ap-a-hint-foundations
git fetch origin audit/ap-a-hint-foundations
```

GitHub接続ツールから保存する場合も、最新共有headを唯一の親として新規ファイルを含むtree/commitを作り、`expected_sha` に取得したhead、`force:false` で同じrefへ更新する。競合した予約をそのままrebaseして押し込まない。最新予約を読んで別組を選び直す。

## 一問ずつ提出する

```sh
python tools/hint_foundations_audit.py show unit-01
```

元パックには本文・全肢・ヒント・図の参照がある。必要な図や画像本文は実際に開く。回答後の解説を、回答前から教わっていた知識として扱わない。判読できない図や不十分な文脈は `uncertain` とし、読めなかった項目の `reviewed` をfalseにする。

提案JSONを作業用の一時ディレクトリへ用意する。下記は書式の説明用で、実点検結果ではない。引用や理由の仮文をそのまま提出しない。

```json
{
  "assessment": "candidate",
  "scores": {"foundation": 1, "prerequisites": 0, "progression": 0},
  "axisReasons": {
    "foundation": "不足する意味と、後段でどこまで補われるかを記入",
    "prerequisites": "式・条件・手順を辿れる根拠を記入",
    "progression": "段階を追って理解できる根拠を記入"
  },
  "criticalOverride": false,
  "confidence": "medium",
  "reviewed": {"question": true, "choices": true, "allHints": true},
  "evidence": [{
    "axis": "foundation", "hintStep": 1,
    "quote": "対象ヒント本文からの正確な短い引用",
    "missingKnowledge": "何の意味・仕組みを知らないと止まるか",
    "learnerBlock": "引用と問題・選択肢を合わせ、どの判断をできないか",
    "neededExplanation": "意味・仕組み・例・対応のうち何を補う必要があるか"
  }],
  "cumulativeReason": "H1→H2→H3で学べることと、それでも残る不足を記入",
  "supersedes": null
}
```

全軸0の `clear` も一問ずつ根拠を残す。`evidence` は空配列でよいが、`support:{"hintStep":2,"quote":"実ヒントからの短い引用","enables":"何を学び、どの判断ができるか"}`を必須とする。`uncertain` は全得点null、`criticalOverride:false`、`missingContext`に保留理由を記す。`critical` は各ヒントの引用と、全段でも足場がない具体的な `criticalReason` が必要。合計・重大度・教材SHA・予約SHA・日時・UUIDは提出コマンドが付ける。

```sh
git fetch origin audit/ap-a-hint-foundations
python tools/hint_foundations_audit.py submit r07h-q1 --worker '予約した実担当名' --file /tmp/自分専用/提案.json
python tools/hint_foundations_audit.py check --against origin/audit/ap-a-hint-foundations
```

一問から保存してよい。20問未満を組完了と数えず、`uncertain`や教材変更で再確認が必要な問を含む組も完了にしない。「組完了」は一次点検提出済みであり、候補の独立確認や修正完了ではない。追加・訂正は直前の提出SHAを `supersedes` に渡す。古い確認は新しい提出へ自動継承しない。

保存先は同じ共有ブランチだけとする。自分の新規JSONだけをstageする。別組の追加でpushが拒否された場合、最新headから自分の新規ファイルだけを載せ直し、予約・直前提出SHAを再確認して非forceで保存する。同じ問の提出枝が分かれた場合は統合担当へ戻す。`git add .`、force push、他者のファイルを削る競合解消は使わない。

## 別担当の確認と担当交代

確認者は実際に同じ版の本文・全肢・全段を読み、問題の足場を辿る。点検担当と異なる実担当名で、公開済み提出のSHAを指定する。

```sh
python tools/hint_foundations_audit.py review 提出SHA --worker '別の実確認担当名' --decision confirmed --reason '原文と累積ヒントで実際に確認した根拠'
```

`confirmed` / `dismissed` / `needs_more_context` を使う。確認が割れた場合は `disputed` のまま表示し、後から来た人の意見で上書きしない。形式検証は、担当名が異なることやSHAの整合を確認するだけで、実際の独立読了を保証しない。

担当者が離れる場合は、統合担当が作業停止と提出済み範囲を確認し、最新ref上の予約・既存提出を確かめて交代する。自動期限切れ・無断取り直しはしない。

```sh
python tools/hint_foundations_audit.py transfer unit-01 --worker '新担当名' --coordinator '実統合担当名' --reason '交代理由・作業停止の確認'
```

交代ファイルは旧予約SHAと保存済み提出SHAを固定する。交代後も既存提出・確認を保持し、旧担当による後からの提出を拒否する。新担当は交代記録の共有ブランチへの保存を確認してから続ける。役割名の記入はアクセス制御の代わりではなく、同じGitHub書き込み権限を持つ担当間の運用記録である。

## 集計・教材更新

```sh
python tools/hint_foundations_audit.py check --against origin/audit/ap-a-hint-foundations
python tools/hint_foundations_audit.py report
# 以下の共有一覧を書き換えるのは統合担当だけ。
python tools/hint_foundations_audit.py report --markdown --output work/ap/hint-foundations/REPORT.md
```

候補は重大度→得点の順で並ぶ。確度、別担当確認、原文引用、必要な説明も追える。CIは最新集計を成果物へ生成するので、ワーカー同士で共有一覧を同時編集しなくてよい。未点検は0点と区別し、保留や教材更新後の旧判定を現在の候補数へ混ぜない。

教材が更新された場合、固定パックの旧判定を残し、現在の教材SHAとの差を `stale` と表示する。旧判定を新教材の承認へ読み替えず、新しい点検ラウンドを統合担当が準備する。点検基準を変更する場合も既存判定の点数を黙って再計算せず、基準版を分ける。
