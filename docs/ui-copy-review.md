# GUIの文言・補足表示の点検

GUI表示の調査結果。確認したコードは ca29ed0（2026-10-13）。改善候補26件：P0 8件、P1 12件、P2 6件。アプリの画面や動作は、この調査では変更していない。

## 表示の方針

- 日常画面は「今の結果」と「次に押す操作」を中心にする。

- 正常な保存・同期は一か所に集約し、異常時は次に取れる操作を示す。

- 出題・集計・同期の詳細は、必要な人が開く説明へ。

- 自力正答率の期間・母数、答えを含むヒントの警告、保存失敗、競合、削除・置換の確認は残す。

## 最初に直す範囲

まず01〜08。同期は文言だけでなく、正常への状態遷移・部分失敗の扱いも整理する。単語帳・ヒント・AIの操作説明を短くし、現在の全800問に共通する教材状態の表示を省く。

## P0：普段の操作を圧迫する

### 01. 表示・データ：正常な同期を5行に分けている

> 同期済み／計画・診断も同期済み。／学習設定も同期済み。／単語帳の自己評価も同期済み。／メモ・再開位置も同期済み。

**表示条件**：ログイン後、5系統の同期状態をそれぞれ表示。

**問題**：保存先の内部区分がそのままGUIへ出ている。利用者が知りたいのは他端末で続きを使えるか。

**候補**：正常時は「同期済み」1行へ統合。未送信・一部失敗・競合があれば総合表示を変更し、その対象だけ詳細を出す。通常演習だけ成功して全体を同期済みと見せない。

[templates/study.html:23](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L23) · [src/sync/account.js:13](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/sync/account.js#L13) · [src/ui/planning.js:20](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L20) · [src/features/learning.js:4](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/learning.js#L4) · [src/features/cards.js:29](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L29) · [src/features/personal.js:7](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/personal.js#L7)

### 02. 表示・データ：同期対象を列挙する長文

> 回答・ヒント履歴・中断状態と、受験日・計画・診断・模試を同期します。紙ペン指定・先送り・問題の開始入口と継続範囲も同期します。…

**表示条件**：設定のアカウント欄で常時表示。

**問題**：スクリーンショットの大半を占める。細かい保存単位を読む必要が生まれている。

**候補**：表面は「ログインすると別の端末でも続けられます」。同期対象・端末だけの設定・ログアウト後の扱いは「同期について」の中へ。

[templates/study.html:23](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L23)

### 03. ホーム・計画・診断：正常状態の同期説明が各画面へ再掲される

> 計画・診断も同期済み。／この端末に保存します。別端末で使うには…

**表示条件**：計画・診断一覧は statusHTML() を常時挿入。ホームは pending 時に挿入し、onStatus() が synced の段落へ置換する経路がある。

**問題**：ホームは通常描画なら正常表示を抑えているが、同期待ち→同期済みの更新では行が残りうる。文言を短くするだけでは解消しない。

**候補**：通常画面は正常時の同期表示を省く。正常への遷移で行そのものを消す。保存失敗・競合など次の操作に関わる時だけ表示。

[src/ui/planning.js:21](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L21) · [src/ui/planning.js:29](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L29) · [src/ui/planning.js:37](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L37) · [src/features/planning.js:145](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/planning.js#L145)

### 04. 単語帳：学習中に再出題と同期の仕様を長く説明

> 「もう一度」は別のカードを3枚挟んで再確認します。枚数が少ない分野では間隔を短くします。自己評価は四択の正答率・計画の実績に含めません。…

**表示条件**：カードの下に常時表示。

**問題**：用語を覚える流れの中へ、実装上の間隔や集計・同期の説明が入る。

**候補**：通常画面から長文を外す。必要なら「単語帳の使い方」にまとめ、「もう一度で後から再確認できます」程度にする。

[src/features/cards.js:16](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L16)

### 05. 単語帳：進捗の前置きと同期表示が重複

> 自己評価の記録 · 確認済み …／単語帳の自己評価も同期済み。

**表示条件**：進捗欄と card-sync-detail。同期状態は設定にも同時表示。

**問題**：確認した枚数は役立つが、「自己評価の記録」と保存系統名は毎回不要。

**候補**：「確認済み 3 / 681枚 · もう一度 3枚」など件数に絞る。正常な同期はカード画面から外す。

[src/features/cards.js:16](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L16) · [src/features/cards.js:29](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L29) · [src/features/cards.js:30](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L30)

### 06. 通常学習：ヒントの表示状態と集計仕様を毎回説明

> 全ヒントを表示済み。／解答後のヒント閲覧は、解答前の記録に加えません。

**表示条件**：全ヒントを開いた時と採点後に表示。

**問題**：3/3という表示と重複し、採点後も内部集計ルールを読み続ける。

**候補**：全表示済みの文章を省く。採点後の閲覧ルールは記録の集計説明へ。次のヒントが答えを含む警告は残す。

[src/ui/views.js:91](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L91)

### 07. AIに聞く：クリップボード対策の実装を説明

> コピー完了後、少し待って同じタブでAIを開きます。

**表示条件**：AI選択ダイアログの操作ボタンの下。

**問題**：遅延と遷移先のタブは、利用者に読ませる必要がない。

**候補**：「開いたAIに貼り付けてください」だけにする。コピー失敗時の手動操作と、自動送信ではないことは必要な場所に残す。

[templates/study.html:28](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L28) · [templates/study.html:37](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L37)

### 08. 問題を探す：全問同じ解説有無を繰り返している

> 個別ヒント・解説あり／個別解説あり（絞り込み）

**表示条件**：各問題行と絞り込み。現在の通常800問はすべて reviewed・individual。

**問題**：同じ情報が20行並び、現在のAPではフィルターを押しても候補が変わらない。

**候補**：その資格の教材に差がある時だけ解説有無を表示・絞り込みに使う。個人編集した問題の印は必要なら残す。

[src/ui/views.js:112](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L112) · [src/ui/views.js:115](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L115)

## P1：説明や異常時の案内を整理する

### 09. 実力診断：開始前に教材制作・配分を説明

> 現在の診断専用派生問題は…問。分野配分を保ち、不足は既存過去問で補います。

**表示条件**：診断一覧の開始カード。

**問題**：利用者は受ける条件より先に、教材の制作状況や選出方式を読む。

**候補**：開始前は「30問・ヒントなし・中断可能・終了後に採点」に絞る。既存／派生の構成は詳細や結果へ。

[src/ui/planning.js:38](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L38)

### 10. 診断・模試結果：結果の先頭に内部カウントを詰め込む

> 支援なし。表示した…問・スキップ…問。既に見た問題…問。…既出はアプリ内の履歴のみです。

**表示条件**：終了結果の正答率直下。

**問題**：回答数・正解・未回答と並んで、露出や既出の管理指標も主役になる。

**候補**：先頭は点数・回答数・未回答・分野別結果。表示／既出／母問題の経験は「出題の内訳」にまとめる。AI Exportの情報は保持。

[src/ui/planning.js:48](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L48) · [src/ui/views.js:54](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L54)

### 11. 診断結果・記録：断定しない方針と出題版を何度も説明

> 出題方針：版…／分野全体の習熟・合格可能性は断定しません。

**表示条件**：診断の出題構成は折りたたみ。結果の末尾にも注意文。通常・推移グラフにも集計説明。

**問題**：慎重な集計方針は妥当だが、宣言が重複すると結果の読みにくさになる。

**候補**：母数と期間は見えるままにし、注意と詳細は一か所へ集約。方針の版番号は詳細だけに置く。

[src/ui/planning.js:48](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L48) · [src/ui/views.js:58](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L58) · [src/ui/learning-trend.js:8](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/learning-trend.js#L8)

### 12. 分野別に解く：出題条件と集計範囲の実装用語

> 記録：直近…日 · 出題条件によらず全記録

**表示条件**：分野一覧の上部。

**問題**：出題条件という語の意味を解釈しないといけない。分野を選ぶ前の補足として長い。

**候補**：「直近28日の記録」を基本にする。紙ペン条件でグラフを絞らない点はグラフの詳細へ。

[src/ui/views.js:44](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L44)

### 13. 解答後・解き直し：復習予定に内部カウンターを併記

> 別の日の自力正解：…回。／翌日が復習目安です。

**表示条件**：解答後の次の復習目安の下。

**問題**：次の日付が分かれば次の行動は決まる。翌日説明や成功日数は出題計算の根拠。

**候補**：「次の復習：10/14」に絞る。間隔と判定理由は復習画面の詳細へ。

[src/ui/views.js:97](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L97) · [src/ui/views.js:101](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L101)

### 14. 紙ペン指定：一つの操作を3か所で長く説明

> 今後の「身軽に1問」から外して中断します。…／原本確認済みの候補は再び…

**表示条件**：紙ペン必要ボタンの補足・押した後の通知・ホームの解除説明。

**問題**：候補・原本確認・保存済みなどの内部語が重複。ボタンの用途を知るための一文は必要。

**候補**：赤いボタンは維持。補足は「中断して、書いて考える1問へ」。通知は一度だけ短く。解除説明の「原本確認済み」は省く。

[src/ui/views.js:40](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L40) · [src/ui/views.js:93](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L93) · [src/app.js:250](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/app.js#L250) · [src/app.js:251](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/app.js#L251)

### 15. ホームの計画：計画のローカル保存を繰り返している

> この端末の計画です。／受験日・計画は、必要なときに登録できます。

**表示条件**：ゲストで計画登録済み／計画未登録のホーム。

**問題**：計画カードは残日数・実績・今日の操作が主目的。ログイン案内がカード内を圧迫。

**候補**：保存範囲はアカウント設定へ。計画未登録は「計画を登録」の入口を中心にし、任意である説明は初回の編集時に一度。

[src/ui/planning.js:29](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L29)

### 16. 学習計画：各編集ブロックで実績の算定を説明

> 目標は解き直し・解答閲覧を含む取り組み回数。…／予定の完了では回数は増えません。

**表示条件**：計画概要の詳細、フェーズ編集、週別目標、予定編集。

**問題**：同じ数え方を繰り返し、計画入力より説明の分量が増える。

**候補**：入力は「目標：取り組む回数」など短いラベルへ。週別・予定の扱いも「目標の数え方」に一度だけまとめる。

[src/ui/planning.js:31](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L31) · [src/ui/planning.js:34](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L34) · [src/ui/plan-targets.js:17](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/plan-targets.js#L17)

### 17. 学習計画：未登録表示が何段も続く

> 計画の前提は未登録です。／フェーズは未登録です。／週別目標は未登録です。／予定は未登録です。

**表示条件**：未登録の項目がある時。それぞれのセクションや詳細に出る。

**問題**：未入力の説明で空間が増える。保存内容を見たい人には情報がない。

**候補**：内容がない読取専用ブロックは省く。追加ボタンとフォームのプレースホルダーは残す。結果ゼロなど必要な空状態と区別する。

[src/ui/plan-context.js:7](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/plan-context.js#L7) · [src/ui/planning.js:24](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L24) · [src/ui/plan-targets.js:17](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/plan-targets.js#L17) · [src/ui/plan-history.js:12](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/plan-history.js#L12)

### 18. 計画の同期競合：使う内容の選択を生JSONに頼っている

> この端末の内容／クラウドの内容の下にJSONを表示

**表示条件**：計画の変更が競合した時だけ。

**問題**：衝突の解決に、キー名や配列構造を読み取る必要がある。

**候補**：試験日・期間・目標・重点分野の差を人間向けに比較。JSONは追加詳細へ。どちらを採用するかの操作は保持。

[src/ui/planning.js:22](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L22)

### 19. 同期・ログインの異常：利用者へFirebase管理者の作業を指示

> Firebaseのアクセスルールを確認してください。／FirebaseでGoogleログインを有効にしてください。

**表示条件**：permission-denied 等の時。設定内にもFirebase設定手順へのリンク。

**問題**：一般利用者には管理画面を操作できない。エラー時でも、利用者が取れる行動が分かりにくい。

**候補**：一般向けは「同期できません。記録はこの端末に残っています」＋再試行や書き出し。Firebaseの原因・設定手順は管理者向け詳細へ。

[src/sync/account.js:18](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/sync/account.js#L18) · [src/sync/account.js:24](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/sync/account.js#L24) · [src/ui/planning.js:20](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L20) · [src/features/learning.js:4](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/learning.js#L4) · [src/features/cards.js:29](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L29) · [templates/study.html:23](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L23)

### 20. 読込・取り込みの異常：内部の整合性エラーをそのまま表面へ出す

> 教材パックの件数が一致しません。／教材一覧の件数が一致しません。／移動中の学習教材を確認できません。

**表示条件**：読込・検証の失敗時。catch が error.message を通知へ流す。

**問題**：何をすべきかより、内部検証のどこが失敗したかを知らせている。

**候補**：「問題を読み込めません。接続後にもう一度お試しください」など操作に合わせた案内へ。原因コードや詳細は調査用に残す。失敗自体は隠さない。

[src/content/catalog.js:54](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/content/catalog.js#L54) · [src/content/catalog.js:63](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/content/catalog.js#L63) · [src/content/catalog.js:92](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/content/catalog.js#L92) · [src/app.js:193](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/app.js#L193)

## P2：入口と詳細を整理する

### 21. 問題を探す：全行の教材編集と教材書き出し

> 教材を編集／教材を書き出す

**表示条件**：検索結果の全問題行と検索画面下部。

**問題**：問題を解きたい人に、編集・作成向け操作が同じ重さで並ぶ。個人編集は既存の利用機能。

**候補**：解く操作を主役にし、編集は問題の詳細／オプションへ。教材書き出しは設定や管理用入口へ。個人編集自体は維持。

[src/ui/views.js:112](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L112) · [src/ui/views.js:115](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L115)

### 22. 出典・教材案内：教材の制作状況と注意を繰り返す

> 学習ガイド・個別ヒントと解説は独自作成です。…公式解説ではありません。／詳しい個別解説は…問に追加済みです。

**表示条件**：問題の出典詳細・教材の出典詳細・全画面フッター。詳細はすでに折りたたみ。

**問題**：制作進捗は学習のたびに読む情報ではない。現状は詳細なので優先度は低い。

**候補**：出典・原本リンクは保持。制作進捗や共通の説明は教材についてのページへ集約。全800問が解説済みの今、進捗としての表示価値は小さい。

[src/ui/views.js:93](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L93) · [src/ui/views.js:115](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/views.js#L115) · [templates/study.html:21](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L21)

### 23. 設定・診断・単語帳：データ管理の入口が画面ごとに分散

> 診断を書き出す／診断を取り込む／単語帳の記録を保存・取り込む／学習記録を書き出す

**表示条件**：設定、診断結果一覧、単語帳の詳細。

**問題**：保存形式に合わせた入口が増え、ユーザーがどれを使えばよいか迷う。カード記録は現状別ファイル。

**候補**：入口は「表示・データ」へまとめる案。全体バックアップに含まれる範囲を確認してから整理し、カード等が欠落する状態にはしない。

[templates/study.html:23](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L23) · [src/ui/planning.js:38](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/ui/planning.js#L38) · [src/features/cards.js:16](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/features/cards.js#L16) · [src/app.js:311](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/app.js#L311)

### 24. 表示・データ：ログイン前の取り込みを常に大きく出す

> ログイン前の記録を取り込む

**表示条件**：adopt.hidden=!user のため、ログイン済みなら取り込み可能な内容の有無にかかわらず表示。

**問題**：通常のアカウント操作の一部を占める。取り込める記録がない場合も出る。

**候補**：通常学習・カード・メモ・計画などの取り込み対象がある時だけ表示。取り込み済み判定や、別人の記録を自動採用しない扱いも必要。

[src/sync/account.js:21](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/sync/account.js#L21) · [src/app.js:392](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/src/app.js#L392)

### 25. 表示・データ：インストール済みでも起動方法を説明

> ホーム画面から起動しています。

**表示条件**：standalone 起動時のホーム画面追加欄。

**問題**：利用者が今まさに行った操作を説明している。

**候補**：インストール済みなら案内を省く。更新がある時の操作、未インストール時の導入案内、保存失敗は残す。

[pwa.js:27](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/pwa.js#L27) · [templates/study.html:23](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L23)

### 26. 画像拡大：操作から分かるスクロールを説明

> 画像をスクロールして読めます。

**表示条件**：画像拡大ダイアログのボタンの横。

**問題**：拡大・縮小の操作に補足が重なり、スマホの横幅を使う。

**候補**：通常表示では省く候補。切れた画像の端やスクロール領域で操作可能性を示す。拡大・閉じるボタンは保持。

[templates/study.html:25](https://github.com/donald-shrimp/ap-study/blob/ca29ed0950c48c3947c03778b5e1a795bc200d6e/templates/study.html#L25)

## 整理時に残すもの

点数・正答率の母数・集計期間、回答・正解・解説、復習の日付、分野・問題の識別、紙ペン必要の赤い操作、原本参照、AIへの貼り付け案内。保存失敗・未送信・競合・データ削除の確認を正常時の補足と一緒に消さない。

## 表示条件の補足

ホームの計画は通常描画でsyncedを挿入しない。一方、pendingの段落が存在するとonStatus()がsynced文言へ置換するため、次の全体描画まで残る経路がある。03は単なるコピーの短文化ではなく、表示状態の整理も必要。旧教材の更新案内、オフラインで未取得の問題、少数の回答の母数などは条件と意味があるため、一律の削除候補にはしなかった。

## 確認方法

共通テンプレート、src/ui の表示関数、features/sync の状態更新、src/app.js とPWAの案内を確認。ログイン済み表示は提供画像とコードを照合。ホームの同期待ち→同期済みは、実際の表示更新関数を使った独立した小さな再現で確認。常時表示・条件付き表示・すでに折りたたまれた説明を区別した。通常800問の教材状態も実数で確認した。
