# batch-01 独立確認結果

確認者: Codex /root/ap_wave01_author_2
作者: Codex /root/ap_wave01_author_1

原本20画像を全件view_imageで開き、作者draft・正答解説を見る前に全20問の独立解答を `independent-reviewer-2.json` へ保存した。その後、公式正答（contextとdata/answer-keys.json）・最終draft全体を比較した。20問の全80肢の理由・全60ヒント・summary/explanation/takeaway/designを読んだ。独立解答と公式正答は全件一致。

指摘3件は作者へ返し、作者修正後に全文を再確認した。

- r03h-q1: NOR/AND/ORを肢別理由で日本語定義し、独立した条件説明に修正。
- r07h-q4: H3へ期限10msと応答9ms/11msの具体的比較を追加し、前段から増える情報を確保。全段trueは正答定義をH1で渡すため適切。
- r04h-q3: ア1.25倍の理由を系内時間比0.75/0.60と具体化し、サービス除外の待ち時間との相違を説明。

重点項目は、ATM2問の処理能力不変が原文の暗黙前提であることを限定して明示した説明、n=1の実際最大1桁と一般上限2nとの区別、交差検証H1とリアルタイム全段の開示を確認した。原問は変更していない。

独立したPython計算で、桁交換4入力、nextの全256入力、カルノー図の1セル6個、ハミング全肢の検査結果と別問の誤り位置、平方の境界n=1..6、待ち時間比2と系内時間比1.25を再検算した。

全sourceHashesを実ファイルSHA256で検証し、inventoryのbaselineLessonSHA256/baselineQuestionSHA256を使用。最終lessonのcanonical JSON SHA256と実確認UTC日時をreviews.jsonへ記録した。`python tools/ap-lesson-quality.py check batch-01 --reviewed` は20件成功、approvedForRegistration:true。

IPA公式解答PDFの再アクセスと実地初心者試用は行っていない。独立承認は公開確認を意味しない。

## 補助コードの独立点検

- tests/ap-lesson-quality.py: setUpClassのremaining39組リセットはTemporaryDirectory内だけを対象とする。固定baselineのlessonへ復元し、author/reviewerはnull、decisionはpending、designはnull、reviewsは空配列に戻す。固定ID/baseVersion/baseLessonSHA256は保持する。実担当・改稿・登録状態による合成fixtureへの混入を防ぐ変更として整合。独立実行で29テスト成功。
- work/ap/objective-quality/review/browser-wave-01.py: batch-01..04の80問を実アプリで開き、全240ヒントを段階開示し、全320理由と要約・解説の表示を照合する。開示警告・結果・回答後ヒント・オフライン・各幅/倍率を検証。80件に追加の合成3件を加えbackup83件の出力/読込を照合し、旧版の終了済み記録と中断記録の2問からsnapshot/結果保持と最新版別試行を検証する。既存本人データは使用しない。重大な問題は見つからなかった。
- .github/workflows/system-validation.yml: PlaywrightとChromium導入済みbrowser-storageジョブへ当該スクリプトを追加し、work配下変更も起動対象。追加の実行場所・依存関係は整合。

ブラウザスクリプト自体は親の統合作業との競合を避け、この確認者は実行していない。コードの静的確認と29件の合成契約テスト実行を、実画面検証済みとは混同しない。

最終コード再読: ブラウザの追加例を今回80問内のr07h-q4（H1開示・旧assisted）、r03h-q2（H2累積開示）、r05a-q1（旧中断→新別試行）へ変更した版も確認。baselineのフラグが順に[false,false,false]、[false,false,true]、[false,false,true]、最終draftが[true,true,true]、[false,true,true]、[false,false,false]であることを実データで再確認した。83件の内訳は80件＋開示2件＋回答後ヒント1件のまま。

確認した最終コードSHA256:

- tests/ap-lesson-quality.py: f158435aa0067c3f346a756736ffe97d289cd1ebf5cc064064c0072e0646397f
- work/ap/objective-quality/review/browser-wave-01.py: 621d40f417374c825f3e5a6d2e63359b4394d2ef3eb6f01469272e730c49efb9
- .github/workflows/system-validation.yml: 9189be047b324fb8637c89e584dc261ee3ea4d0a2466b932accfe69dd562be21
