# Firebase接続：最後の設定

2026-10-06：プロジェクト `hito-mon` とWebアプリ設定を受領し、Googleログイン・回答／ヒント履歴／中断状態の同期コードを実装した。公開ドメイン `donald-shrimp.github.io` の登録と未認証アクセスの拒否を確認した。本番のルール配備と、本人によるGoogleログイン・実機同期は未確認。

## 1. アクセスルールを公開する

[FirebaseのFirestoreルール画面](https://console.firebase.google.com/project/hito-mon/firestore/rules)を開く。

1. リポジトリの [firestore.rules](https://github.com/donald-shrimp/ap-study/blob/main/firestore.rules) を開き、ファイル全体をコピーする。
2. Firebaseの「ルール」欄をその内容で置き換え、「公開」を押す。

本人のUID・資格別の学習記録だけ許可する。全員に読取／書込を許可するテストモードは使わない。確定した回答・問題・教材の書換、古いリビジョン、他人の記録、削除を拒否する。Web設定は公開用であり、管理者権限は含まないため、この環境から本番ルールは配備していない。

管理用CLIを自分の環境で使える場合は、コンソールの代わりに次を実行できる。

```sh
npm ci
npx firebase deploy --only firestore:rules,firestore:indexes --project hito-mon
```

## 2. 大きな教材スナップショットを検索対象から外す

Firestoreの「インデックス」→「単一フィールド」から、コレクションID `attempts`、フィールド `payload` のインデックス除外を追加する。教材の本文・画像参照は検索しないため、その配下を含めてインデックス不要。並び順と差分取得に使う `updatedAt` は除外しない。CLIなら `firestore.indexes.json` がこの設定を行う。

## 3. アプリで試す

1. [ひと問](https://donald-shrimp.github.io/ap-study/)を開き、「表示・データ」→「Googleでログイン」。旧PWAが表示される場合は同じ設定内の「更新して再読み込み」を押す。
2. ログイン前の履歴を使う場合だけ、「ログイン前の記録を取り込む」。元の端末内記録は残り、取り込みの繰り返しでも重複しない。
3. 1問解くか、中断して「今すぐ同期」。表示が「同期済み」になることを確認する。
4. 別ブラウザ・端末でも同じGoogleアカウントでログインし、「今すぐ同期」。履歴と「再開する」を確認する。

ログインできない場合：AuthenticationのGoogleを有効にし、サポートメールと承認済みドメイン `donald-shrimp.github.io` を確認する。ポップアップがブロックされた場合はChromeで許可する。Android Chrome・インストール済みPWAのGoogleログインは実機確認が必要。広告ブロックを使う場合は、以前と同様にこのサイトを除外する。

## 保存と費用

- ログインなしでも従来どおり使える。ログイン後は別のアカウント用保存先へ切り替わる。
- 記録はまずIndexedDBへ保存。通信失敗・無料枠の上限・権限不足でも端末に残す。未送信を別UIDへ送らない。
- 同期するのは試行の履歴、選択、ヒント、答え閲覧、自信、中断状態、記録時点の問題と教材。原本画像はURLのみで、画像・PDFそのものは送らない。
- 読書メモ、読んだ範囲のメモ、個人教材の編集内容そのもの、表示設定、画面位置は端末別。ただし個人教材で解いた場合、その試行の教材スナップショットは履歴の一部として送る。
- 別端末からの中断再開は継続UUIDを発行し、同時回答を両方保持。確定回答は再採点しない。回答後のヒントは履歴だけ追加し、解答前の支援判定を変更しない。
- 変更は短時間まとめ、通常の自動同期は最短15秒間隔。表示中は最大60秒間隔で差分確認。「今すぐ同期」は任意に実行可能。常時購読・スクロール通信・Cloud Functions・SMS認証・Analyticsは使わない。
- Firestoreの900KBを超える試行は端末に保持し、同期できないことを表示する。
- クラウド記録の削除は今回提供しない。アカウント使用中の初期化・置換インポートは表示しない。端末内記録のJSON書き出しはログイン中も使える。クラウド削除・アカウント削除のUIは別工程。

Spark無料枠はプロジェクト内で共有される。[公式料金](https://firebase.google.com/pricing)で実際の利用量を確認する。

## 開発時の確認

Firebase SDK 12.19.0はAuth・Firestoreだけを固定版でローカル配布する。SDKの再生成は `npm ci && npm run build:firebase`。学習の起動はSDK通信を待たず、認証・Firestore通信をサービスワーカーでキャッシュしない。

ローカルHTTPサーバーを4173番で起動し、別ターミナルで次を実行する。

```sh
node --test tests/study-domain.mjs tests/sync-engine.mjs
npm run test:sync
```

Auth／Firestore Emulatorは localhost の `?firebase-emulator=1` のときだけ使う。本番URLのクエリからEmulatorへ切り替えることはできない。Google OAuthの実サービス・Android実機の確認をEmulator結果で代用しない。
