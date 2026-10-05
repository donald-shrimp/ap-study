# 学習支援・学習体験の調査メモ v0.2

調査日：2026-10-05。前回の本文未確認メモを更新。

## 調査の方法と範囲

今回は外部資料を取得でき、下記の公式資料・公開本文・抄録を直接確認した。学習研究のレビューとメタ分析、ADHD支援指針、認知アクセシビリティの設計指針、試験の一次資料を中心にした、目的を絞った文献調査。網羅的なシステマティックレビューではない。

論文の全文を確認したものと、公開抄録までのものを区別する。一般の学生への学習研究、ADHD診療の環境調整、幅広い認知特性へのデザイン指針は対象が異なる。このアプリがADHDの成人の学習成果を改善するという直接の効果検証は行っていない。

設計への具体的な対応は [学習体験の設計案](learning-design.md)、開発範囲は [要件定義](requirements.md) に記載。

調査時には取得した資料の本文を作業用キャッシュで確認した（公開リポジトリには第三者サイトの本文を転載していない）。HTTP 200でも本文を取得できていないページは根拠として採用していない。

## 確認した知見

### A. ADHDへの支援：時間を一律に決めず、環境を調整する

NICEは環境調整を本人の状況・必要に応じて決めるものとし、刺激を減らすこと、短い集中区間と体を動かす休憩、口頭の依頼を文字でも示すことなどを例示している [R1]。

> “shorter periods of focus with movement breaks”

これを参考に、短い学習単位、静かな画面、いつでも休憩できる操作、段階的な文字のヒントを採用する。25分や5分を全員に最適な時間として固定する根拠にはしない。

NIMHの成人向け資料は、注意、整理、先延ばし、時間管理、大きな課題を終えることなどに困難が生じ得ると説明している [R2]。今回確認したページの題名は *ADHD in Adults: 4 Things to Know*。前回メモの題名を修正した。このページに存在しない小分け学習・リマインダーの具体的な推奨を引用しない。

### B. 記憶：答える練習と、間隔をあけた復習を中心にする

Dunloskyらのレビューは練習テストと分散学習をhigh utilityと評価している [R3]。自己説明や交互学習は適切な場面で有望としつつ、当時の根拠の範囲に限界がある。

Agarwalらの教室研究のレビューは50実験、合計5,374人を扱い、様々な教育段階・内容・テスト形式で想起練習の利益を報告している [R4]。ただし、日本やADHDの成人に限定した研究ではない。抄録には非WEIRD諸国の実験が6%だったとの制限もある。

Cepedaらは317実験をまとめ、適切な学習間隔と保持したい期間が関連することを報告している [R5]。したがって「翌日・3日・7日・14日」はアプリの初期ルール案であって、誰にでも最適な間隔ではない。

間隔をあけて「違う内容を少しずつ勉強すること」と「同じ重要な内容を後日再び確かめること」は区別する。復習機能では後者を実現する [R11]。

### C. ヒント：支援を使って理解し、後から自力で確かめる

IESの実践ガイドは解法例と自分で解く演習を組み合わせることを勧める [R6]。PDFのRecommendation 2の根拠評価はModerate。学習者がまだ知らない概念に対して、毎回自力解答だけを要求する設計は採用しない。

KoedingerとAlevenは支援を与える／控えるバランスを“assistance dilemma”と呼び、適切な条件・量は未解決と明記する [R7]。これを理由に、3段階のヒントや固定の待ち時間が最適だとは断定しない。

採用案は本人が必要時にヒントを開けること、利用を記録すること、後日の復習はヒントを閉じて始めること。正答を実質的に明かした支援は解答閲覧として記録する。

### D. 解説：間違えた理由と、次に使える手順を伝える

Wisniewskiらは435研究、61,000人超を扱うメタ分析で、フィードバックの平均効果をd=0.48と報告している [R8]。同時に大きな異質性があり、伝える情報の内容によって効果が変わるとする。

本文の“Effects of Different Forms of Feedback”では、どこを間違えたか、なぜか、次にどう避けるかを理解する情報の重要性を述べている。アプリでは正誤に加え、判断手順と選んだ誤答の理由を示す。情報量の多さを、そのまま画面の長文量に置き換えない。

この平均効果はアプリによる得点上昇の予測値ではない。また、即時／遅延のどちらが常に優れるとの結論は採用しない。回答後に解説を示すのはこのアプリの学習フローの設計判断。

### E. 操作：現在地が分かり、途中から戻れ、任意の手順を減らす

W3CのCOGA資料は、短い主要操作経路、不要な情報・割込みの抑制、現在地の表示、保存、明確な手順を示す [R10]。

> “Separate out optional steps that are supplemental but not required.”

これに対応して、設定なしの1問開始、任意の自信入力、自動保存、現在地の復元、通知・音・動きの制御を設ける。支援指針に従うことと、学習効果やWCAG適合が実証されることは別。COGAは2021年のWorking Group Noteであり、WCAGの必須適合要件ではない。

### F. 教材：例を読んだ理解を、別の問題への適用につなげる

Weinsteinらのレビューは、具体例、想起、分散、交互学習などを扱い、初学者が例の表面的特徴を覚えやすいことと、異なる例を使って一般化を支援する考え方を説明する [R11]。

教材には概念と関連問題の対応を持たせる。同じ問題での正解を、その概念全体の習熟と同一視しない。似た概念の使い分けを後の演習に含める。このアプリの最適な例数や出題の混ぜ方は検証課題。

### G. ゲーム化：可能性はあるが、必須の中心機能にはしない

SailerとHomnerのメタ分析は、認知、動機づけ、行動の成果について平均的に正の効果を報告している [R9]。厳しい方法上の条件を満たした研究の分析では、動機づけと行動の効果は認知の効果ほど安定していない。効果の異質性もある。

ゲーム化を一律に無効・有害とは扱わない。初期版では学習上の前進を示す小さな反応を優先し、連続利用記録、音、報酬を追加する際は本人の負担と学習結果を確かめる。特定の方式がADHDに最適との根拠にはしない。

## 利用目的に合わせた範囲

利用者は2026年中に受験する。目的は過去問を収集し、ヒント・解説を加え、効率的に学習するツールを作ること。制度変更や年度別シラバスの比較は要件・追加調査の対象から外す。以前確認した制度の資料R12・R13は調査履歴として残し、アプリの必須要件の根拠には使わない。

## 出典と確認範囲

| ID | 出典 | 確認範囲 |
|---|---|---|
| R1 | [NICE NG87 Recommendations](https://www.nice.org.uk/guidance/ng87/chapter/recommendations) | 公式本文。Terms used in this guideline → Environmental modifications、成人の支援に関する箇所 |
| R2 | [NIMH, ADHD in Adults: 4 Things to Know](https://www.nimh.nih.gov/health/publications/adhd-what-you-need-to-know) | 公式本文。成人の日常生活への影響 |
| R3 | [Dunlosky et al. (2013), Improving Students' Learning With Effective Learning Techniques](https://pubmed.ncbi.nlm.nih.gov/26173288/) | PubMedの書誌・抄録。DOI: 10.1177/1529100612453266。論文全文は未取得 |
| R4 | [Agarwal, Nunes & Blunt (2021), Retrieval Practice Consistently Benefits Student Learning](https://link.springer.com/article/10.1007/s10648-021-09595-9) | 出版社の書誌・抄録。本文は購読対象 |
| R5 | [Cepeda et al. (2006), Distributed Practice in Verbal Recall Tasks](https://pubmed.ncbi.nlm.nih.gov/16719566/) | PubMedの書誌・抄録。DOI: 10.1037/0033-2909.132.3.354。論文全文は未取得 |
| R6 | [IES (2007), Organizing Instruction and Study to Improve Student Learning](https://ies.ed.gov/ncee/wwc/PracticeGuide/1)／[PDF](https://ies.ed.gov/ncee/WWC/Docs/PracticeGuide/20072004.pdf) | 公式ページとPDF。推奨一覧と根拠評価、Recommendation 1・2の本文を確認 |
| R7 | [Koedinger & Aleven (2007), Exploring the Assistance Dilemma in Experiments with Cognitive Tutors](https://link.springer.com/article/10.1007/s10648-007-9049-0) | 出版社の書誌・抄録。本文は購読対象 |
| R8 | [Wisniewski, Zierer & Hattie (2020), The Power of Feedback Revisited](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.03087/full) | 公開本文。抄録、フィードバック種類の議論、限界、結論 |
| R9 | [Sailer & Homner (2020), The Gamification of Learning: a Meta-analysis](https://link.springer.com/article/10.1007/s10648-019-09498-w) | 公開本文。抄録・方法・議論。オンライン公開は2019年、巻号は2020年 |
| R10 | [W3C (2021), Making Content Usable for People with Cognitive and Learning Disabilities](https://www.w3.org/TR/coga-usable/) | Working Group Note。現在地、手順、保存、割込み、短い経路、情報量のパターン |
| R11 | [Weinstein, Madan & Sumeracki (2018), Teaching the science of learning](https://cognitiveresearchjournal.springeropen.com/articles/10.1186/s41235-017-0087-y) | 公開本文。分散、想起、具体例、交互学習の説明と適用上の限界 |
| R12 | [IPA, 応用情報技術者試験](https://www.ipa.go.jp/shiken/kubun/ap.html) | 公式本文。2026年度の形式と制度変更の案内 |
| R13 | [IPA, 試験制度の見直しについて](https://www.ipa.go.jp/shiken/minaoshi/index.html) | 公式案内本文。2027年度への移行予定と公開資料の案内 |

## 残る検証

- 成人ADHDに特化した学習支援介入の研究を追加する。現在の提案の根拠には、一般学習者からの外挿が含まれる。
- 過去問と公式解答を収集し、図表を含む問題の再現性と追加するヒント・解説の品質を確認する。
- 3段階のヒント、学習単位、復習間隔、支援の表示量をプロトタイプ利用で確かめる。
- 後日の保持と別問題での応用を測り、同じ問題の正答記憶を分ける。
- 教材の転載・加工・図表の利用条件は公開前に確認する。今回の資料取得は教材配信の許諾確認ではない。

前回候補に挙げたRoediger & Karpicke (2006)の本文は今回直接確認していない。想起練習の根拠にはR3・R4・R6・R11を使う。PMCのフィードバック論文URLはブラウザ確認画面だったため採用せず、出版社の公開本文R8を確認した。
