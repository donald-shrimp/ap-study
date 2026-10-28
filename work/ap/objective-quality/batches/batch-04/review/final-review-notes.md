# batch-04 独立確認記録

確認者: Codex /root/ap_wave01_author_1。作者はCodex /root/ap_wave01_author_4で別担当。

原本webp20枚をview_imageで全件実際に開き、作者教材を読む前に解き直しをindependent-first-pass.mdへ5問ずつ保存した。その後、contextと公式答え台帳を照合し、全20問の答えが独立解答と一致した。全80肢の理由、全60ヒントの本文・累積開示・design、要約・解説・要点を全文読んだ。計算/トレースはindependent-calculations.pyと同jsonに保存した。

## 作者への差戻しと再確認

- r04h-q6: H3がH2の作業領域分離の再述だった。作者がタスクAの途中値10をタスクBの初期化が壊す例へ変更。修正後lesson/design全文を再読し、前段にない具体例が増えたと確認した。
- r03h-q7: H3が分割→処理→結合の再述だった。作者が貪欲法の局所選択との対比を追加。修正後全文で比較軸とtrueの整合を確認した。
- r03h-q10/r04a-q8: H3が行列高速化の再述だった。作者が独立積和/行列各行を並列計算する具体的理由と、CPUも浮動小数点演算可能である対比を追加。修正後全文を再読した。
- 最後にGPU2問のCPUとDMA問ヒント内のMPUの略語補足を作者へ依頼。作者の補足後、対象3問の最終lesson/design全文を再読して定義の位置と内容を確認し、その最終ハッシュをreviews.jsonに記録した。

自分で作者draftを修正していない。各最終lessonのハッシュはUTF-8、キーソート、ensure_ascii=False、separators=(',',':')で計算。独立レビューを初学者実地試用や学習効果測定とは呼んでいない。外部Web資料は使っていない。

最終確認: python tools/ap-lesson-quality.py check batch-04 --reviewed 成功（questions=20,reviewed=20,approvedForRegistration=true）。これは登録可能な独立確認済み草稿であり、登録・公開は実施していない。未解決指摘/読取不能/原問保留はなし。
