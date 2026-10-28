# batch-07 作者納品記録

実作者：Codex /root/ap_wave02_author_3

対象20問のみ。全20原本webpをview_imageで開き、原文・全80肢・数式・表・図を確認して解き直した。contextのIPA公式解答URLから9期分PDFを取得し、pdftotextの問番号別正答を全20問照合した。原本画像は既存のSHA-256と一致。

計算対象は手計算に加えて独立な小規模計算で確認した。磁気ディスク15.1ms、直並列稼働率p[1−(1−p)^2]とp=0.5の0.375、同倍率変更の不変性、ジョブ時間25sと使用率15/25・17/25、ブロック転送4候補のメモリ状態、LRUの番地ごとの置換えを追跡。FIFOは6参照の表、符号付き加算は各誤肢を満たす反例16,384+16,384で確認した。各問の具体的根拠はdrafts.design.sourceNotesに記録。

20件revise、keep/rewriteは0件。論点を示すsummaryへ修正20件、hints17件、explanation10件、choiceReasons7件、takeaway1件。十分な本文・肢別理由は維持した。MTBF/MTTR・FIFO/LRU・EL/CRT/DMD等の略語補足、ヒントの段階差、正答を確定する累積情報を点検。特にOSS H2はa=GPL,d=BSDだけでもアが一意になるのでtrue、FIFO H2と稼働率比H2もtrueにした。

補助一次資料としてMozilla MPL FAQのQ1/Q8/Q9を読み、ファイル単位の義務と結合プログラム全体を区別した。R公式入門とGNU LGPL本文への補助アクセスは503で取得できず、確認資料には数えなかった。この二つへのアクセスを前提にした新規の断定は追加していない。公式原本と正答の確認は完了している。

PDF・抽出全文・補助HTML・計算用作業は /workspace/scratch/ap-a-quality-wave-02/author-3/。repoには必要な根拠とURL/hashのみ。原問疑義・保留なし。レビュー承認・登録・公開・初学者試用は未実施。

形式確認：python tools/ap-lesson-quality.py check batch-07 成功（20問、reviewed=0）。
