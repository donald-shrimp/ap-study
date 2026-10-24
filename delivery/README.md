# FP2級 2026年5月公表・学科60問 Draft納品

学科の公式全60問を、`delivery/content/fp2/questions.json` に登録。240選択肢・240個別理由、6分野分類、法令情報を記録。問55の設問本文を原本に合わせて修正済み。

- 問題原本と正答が同じPDFに併載： https://www.jafp.or.jp/exam/mohan/files/g2_202605_qa.pdf
- 原本SHA-256：`525d190bb489b4187d39d6782eac999fc4b14bfdd1f489842b96685465b804ef`（688,291バイト）
- ハッシュ実測のGitHub Actions証跡：https://github.com/donald-shrimp/ap-study/actions/runs/40083735407
- 法令基準日：2025-04-01（公式問題表紙）。公表の具体日付は不明なので `publishedAt:null`。現行法令の照合は未実施で `unverified`。
- 出典：日本FP協会 ２級FP技能検定 2026年5月公表問題。加工：表示用にテキスト化し、表整形・図切出し・問題固有解説・各選択肢理由を追加。
- 公式利用条件：https://www.jafp.or.jp/exam/mohan/files/exam_riyou.pdf

## 受入状況

**原本PDFと問55の家族関係図PNGはGitツリーへ格納済み。** このブランチをチェックアウトし、リポジトリルートから `python tools/check-fp2-delivery.py delivery` を実行できる納品一式です。SHA-256は原本から実測したものです。PDFと図を含む完全ZIPもチャット成果物として作成しています。

原本同梱のローカル完全納品に対する `python tools/check-fp2-delivery.py <delivery>` は、`questions=60, cases=0, fields=0, mode=draft structure only; not approved` を返し成功。ただし**内容の独立レビューを意味しません**。

確認台帳は空配列にしてあります。レビュー担当・reviewedハッシュ・現行法令の確認情報は捏造しません。作者以外の独立検証が済むまで公開カタログ、HTML、`content/fp2/` の公開用作成元を変更しないでください。
