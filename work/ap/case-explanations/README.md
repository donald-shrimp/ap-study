# 大問全体の解説草案

応用情報・科目Bの大問全体解説を、大問ごとのMarkdownに蓄積する。原問の知識を初学者が知っていると仮定せず、本文の条件から答案へ進む過程を丁寧に説明する。

- 事実確認・出題時点の厳守・強調記法（`**太字**`のみ）の原則は[解説記述ルール](../../../docs/explanation-authoring-rules.md)に従う。
- ただし、**科目Bの大問全体解説における文体・章立て・説明の深さは、短文JSON用のルールではなく、本READMEの「解説の書き方」を正本とする**（「短い説明で済ませる」「専用の見出しを足さない」「だ・である調」は適用しない）。

| 試験回 | 草案と確認記録 | 今の範囲 |
| --- | --- | --- |
| 2025年秋期 | [作成状況](2025-autumn/README.md) | 全11題の内容確認済み保存版あり。添削済み作業版の再承認とは区別する。最新の添削状態は同ディレクトリの進捗を参照 |
| 2025年春期 | [既存11題](pilot-2025-spring/README.md) | 既存の草案。別作業でMarkdown・対応情報の改稿が進んでいるため、旧レビューを現在の文章への再承認とは扱わない |
| 2024年秋期 | [作成状況](2024-autumn/README.md) | 全11題99欄の内容確認済み保存版あり。問1～問3の添削済み作業版は旧承認と区別し、最新の添削状態は進捗を参照 |
| 2024年春期 | [作成状況](2024-spring/README.md) | 全11題・95欄を別担当確認済み。次の試験回は2023年秋期 |
| 2023年秋期 | [作成状況](2023-autumn/README.md) | 問1〜問7は外部添削済み。問8〜問11は再執筆と共通ページへの反映を完了 |
| 2023年春期 | [作成状況](2023-spring/README.md) | 全11題の再執筆と共通ページへの反映を完了 |
| 2022年秋期 | [作成状況](2022-autumn/README.md) | 全11題・101欄を別担当確認済み。 |
| 2022年春期 | [作成状況](2022-spring/README.md) | 全11題・98欄の独立レビュー済み保存版あり |

 ## 解説の書き方（執筆・改稿・内部レビューの共通基準）

新規草案および改稿の文体・構成・説明量は、2025年春期および2025年秋期の原稿を手本にする。
2023年春期・秋期のリライトは[引き継ぎのリライト方針](../../../docs/HANDOFF.md)を優先する。本文の見出しは内容で付け、設問との対応は対応JSONに記録する。
- 手本：[2025年春期 問1](pilot-2025-spring/ap-r07h-pm1.md)・[2025年秋期 問1](2025-autumn/reviewed-originals/ap-r07a-pm1.md)・[2025年秋期 問3](2025-autumn/reviewed-originals/ap-r07a-pm3.md)・[2025年秋期 問9](2025-autumn/reviewed-originals/ap-r07a-pm9.md)

### 1. 文体と分量
- 全文を**「です・ます」調**で統一し、初めてこの分野・問題を読む人に語りかける落ち着いた調子で書く（「だ・である」調や体言止めの連発は不可）。
- 1大問あたり**90〜140行程度**を目安とし、50〜70行程度の要約メモのような短文化をしない。

### 2. 構成の流れ（いきなり設問1から始めない）
    冒頭2段落のあらすじだけで直ちに `## 設問1` へ入るフラットな構成はとらず、次の3部構成を基本とする。

1. **導入と全体整理（設問に入る前の `##` 節）**
    - `## この問題は、何を考える問題だった？` などの見出しで、事例の背景と大問全体のテーマを示す。
    - 続けて `## まず、…を整理しよう` などの見出しで、複数の設問で共通して使う図表・登場機器・ルール・前提知識を先に整理する。
2. **設問ごとの解説（テーマ別の `##` ＋ `### 設問...`、または `## 設問...`）**
    - 見出しには設問番号・回答欄に加えて判断の手掛かりを入れる（例：`### 設問2 a｜PC-Pへの攻撃をログから見分ける`）。
    - 表に1行ずつ理由を押し込んで「〜だから答えは○○です。」とぶつ切りで終わらせず、「問題文・図表のどこに着目し → どの知識を使い → どう考え・計算して答えに至るか」を段落の文章として順序立てて書く。
    - 記述問題では「考えた内容をどのように指定字数・指定語句の答案にまとめるか」の組み立て方も説明する。
3. **末尾のまとめ（`## 次の問題でも使うこと` など）**
    - 最後に、本文の単なる言い換えではなく、類題でも使える見分け方や判断の軸を箇条書きで簡潔に残す。

### 3. 避けるべき表現（AIレビュワー向けの予防線・言い訳の禁止）
内部レビューを通すための不自然な免責文・予防線を本文に混ぜない。
- **書かないこと**：「これは仕組みを示す架空の例であり原問にはない」「実際にN秒という意味ではない」「距離の具体的な単位は指定されていない」「全ての攻撃を必ず防げるという意味ではない」といった、読者の理解を妨げる言い訳。
- **代わりの書き方**：理解を助ける具体例を出すときは「例えば、〜という場合を考えてみましょう」と自然に導入し、本文の事実と混同させない書き方にする。

### 4. 見出しリンクと検証スクリプト（`verify-*.py`）の作り方
- `explanation-links.json` の `heading` には、各回答欄に対応する設問見出し（`##` または `###` の見出し文字列）を登録する。
- 検証スクリプト（`verify-*.py`）で見出しを検査する際は、`2025-autumn/verify-content.py` と同様に `re.findall(r"^#{2,3} (.+)$", draft, re.M)` の中に `explanation-links.json` の各 `heading` が1回ずつ現れることを確認する方式とし、**導入・全体整理・まとめの `##`見出しやテーマ見出し＋`### 設問...` の階層構造を妨げないこと**（`re.split(r"^## (.+)\n")` が `explanation-links.json` と完全一致することを求めるような、導入見出しを禁止するアサーションを書かない）。

## 作成から実装まで

1. 作者が原本・全図表・公式解答・講評を読み、上記の「解説の書き方」に沿って大問ごとのMarkdownと全回答欄への対応情報を作る。
2. 別担当が原本から解き直し、内容と**文章品質（です・ます調の統一、導入・まとめの有無、中間説明の十分さ、不自然な予防線がないこと）**を確認する。別担当は重箱の隅をつく免責文の追加を要求せず、初学者が誤解なく読めるかを基準に確認する。作者が修正した場合は最終版を再確認し、レビューを最終ファイルのハッシュへ結び付ける。
3. 内容確認済みの原稿を各回の`reviewed-originals/`へ保存し、作業用Markdownを[外部担当者用の指示文](editing-brief.md)と一緒に渡す。
4. 外部担当者が読みやすさを添削する。添削後全文・主な変更理由・内容の要確認事項を受け取り、元の原稿を残す。
5. 添削前後を比較し、条件・用語・計算・答案の意味が保たれているか確認する。見出しを変えた場合は対応情報も再確認する。
6. 内容確認と外部添削を済ませた文章を、別工程でアプリへ実装・検証する。草案の追加だけで公開教材や学習記録は変更しない。

内容確認、外部添削、実装、公開は別の状態。文面変更後に以前の内容承認を自動的に引き継がない。`reviewed-originals/`は確認時点の保存版で、添削で上書きしない。

## ページの更新

リポジトリのルートから次を実行する。

```sh
node work/ap/case-explanations/build-preview.mjs
python work/ap/case-explanations/2024-autumn/verify-content.py
python work/ap/case-explanations/2024-autumn/verify-batch-02.py
python work/ap/case-explanations/2024-autumn/verify-batch-03.py
python work/ap/case-explanations/2024-autumn/verify-batch-04.py
python work/ap/case-explanations/2024-autumn/verify-batch-05.py
python work/ap/case-explanations/2024-autumn/verify-batch-06.py
python work/ap/case-explanations/2024-spring/verify-batch-02.py
python work/ap/case-explanations/2024-spring/verify-batch-03.py
python work/ap/case-explanations/2024-spring/verify-batch-04.py
python work/ap/case-explanations/2024-spring/verify-batch-05.py
python work/ap/case-explanations/2024-spring/verify-batch-06.py
python work/ap/case-explanations/2023-autumn/verify-batch-06.py autumn
python work/ap/case-explanations/2023-spring/verify-batch-06.py
python work/ap/case-explanations/2022-autumn/verify-batch-06.py autumn
python work/ap/case-explanations/2022-spring/verify-batch-06.py
python work/ap/case-explanations/2025-autumn/verify-content.py
python work/ap/case-explanations/2025-autumn/verify-batch-02.py
python work/ap/case-explanations/2025-autumn/verify-batch-03.py
python work/ap/case-explanations/2025-autumn/verify-batch-04.py
node work/ap/case-explanations/verify-preview.mjs
```

試験回と収録IDは`catalog.json`で指定する。各回のMarkdownと`explanation-links.json`を読み、既存pilotの共通レンダラで全体ページを生成する。小問リンク、設問文の確認、一覧への復帰、直接URL、履歴、キーボードの操作を共用する。新しい年度のために本文表示を複製しない。

ブラウザ確認にはNodeから参照できるPlaywrightとChromeが必要。今回のWindows環境では、PythonはMicrosoft Storeの別名ではなくCodexの同梱実行ファイルを使い、Nodeの`NODE_PATH`へ同梱パッケージのディレクトリを指定した。

```powershell
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2024-autumn/verify-content.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2024-autumn/verify-batch-02.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2024-autumn/verify-batch-03.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2024-autumn/verify-batch-04.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2024-autumn/verify-batch-05.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2024-autumn/verify-batch-06.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2025-autumn/verify-content.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2025-autumn/verify-batch-02.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2025-autumn/verify-batch-03.py
& 'C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' work/ap/case-explanations/2025-autumn/verify-batch-04.py
$env:NODE_PATH='C:/Users/EBIHARA/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
node work/ap/case-explanations/verify-preview.mjs
```

`browser-checks.json`は、記録したページ版についてのリンク・全回答欄・画面幅320／390／1440pxと文字倍率1／1.4の確認結果。スクリーンショットはJSONに記録した一時ディレクトリにある。これは編集用ページの検証で、学習アプリへの統合・初学者の理解度の試用とは区別する。

数式はアプリと同じKaTeXの表示とローカルのCSS・フォントを使う。設問文の照合は数式の原式も比較し、補助用MathMLと視覚表示が二重に表示されないことを確認する。

従来の春期専用ページと生成コマンドも維持する。全体ページへの追加で、春期のMarkdownや専用HTMLを自動的に書き換えることはない。

2024秋の第6組では、添削中の既存作業版を保持して秋全11題と2024春問1の対応を確認する。新規2題の字数・仮例の確認は`verify-batch-06.py`を使用し、以前の数値例の確認は保存済み証跡に残す。添削で数値例の書き方が変わった原稿に、過去の式抽出チェッカーがそのまま適用できるとは限らない。旧内容承認を添削後へ引き継がない。
