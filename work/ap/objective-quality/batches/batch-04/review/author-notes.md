# batch-04 作者確認記録

作者: Codex /root/ap_wave01_author_4
対象: 固定20問。drafts.jsonのみ教材を改訂。独立承認は未実施。

原本画像20問をすべてview_imageで実際に開き、問題文・条件・全80肢・図と配列値を確認し、context.jsonの公式正答と解き直しを照合した。各問の具体的な再解答はdraft.design.sourceNotesに記録。

20問revise、keep 0、rewrite 0。十分な解説や選択肢別理由を維持した上で、19問のsummaryを正答中心の文から問う論点へ修正。変更キーの件数はsummary 19、explanation 6、choiceReasons 5、takeaway 1、hints 13。ヒントは具体的な知識を補い、用語問題と累積前段を含む答えの開示を再判定した。

補助検算としてPythonで剰余一致⇔差が法の倍数（n=1..11,a,b=1..29）、バブルソート2巡の状態、M=1..9の右流れ図の積=M!、CPI=1.25、HPC=2000ノード/640TFLOPSを再確認。20問のid/baseVersion/baseLessonSHA256不変と、design.changesがHEADの旧lessonとの実差分キーに一致することも検査。

`python tools/ap-lesson-quality.py check batch-04` 成功（20問、reviewed=0、approvedForRegistration=false）。これは形式検査であり独立承認ではない。読取不能・原問疑義・保留なし。外部Web資料や学習者試用は実施していない。
