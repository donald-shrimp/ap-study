# batch-01 作者確認記録

作者: Codex /root/ap_wave01_author_1。対象20問をrevise。独立承認は付けていない。

## 実施内容

AGENTS.md、docs/ap-a-content-upgrade.md、docs/hint-authoring.md、docs/explanation-authoring-rules.md、およびbatch-01のREADME/assignment/context/draftsを読んだ。contextにある20枚の原本webpを全件view_imageで実際に開き、本文・全80肢・図・式を照合した。公式答えはcontextとbaseline/answer-keys.jsonの年度・期・問番号で20件一致を確認。補助外部一次資料や初学者による試用は使用・実施していない。

十分な既存本文・各肢理由を保持し、summaryを論点へ変更した。変更キー内訳はsummary20、hints14、explanation10、choiceReasons1、takeaway0、checkedAgainst0。全60ヒントを前段と選択肢込みで再判定しtrueは26件。問題固有の設計判断・原本参照・解答根拠はdraftsのdesignに記録した。

## 実際のPython検算

- r05a-q1: x=0,1,2,3について交換式の結果0,2,1,3。
- r05h-q1: n=0..255の全数照合。四肢の正解条件一致数は256,0,1,0。アのみ全数一致。
- r04a-q2/r07a-q1: 全16入力の図との一致数はア11、イ15、ウ12、エ16。エのみ全セル一致。
- r04h-q4: 受信1110011の検査結果(1,1,1)。候補ア〜エの三式の結果は(0,0,0),(1,0,0),(0,1,0),(0,0,1)。
- r06h-q4: 1000101の検査値(1,1,0)、誤り位置3。1010101の検査値(0,0,0)。
- r04h-q3: Fractionで(0.40/0.60)/(0.25/0.75)=2を計算。
- r04a-q1: n=1..8で最大平方のbit_lengthは1,4,6,8,10,12,14,16。

接線式からのニュートン法の更新式、XOR相補の真理値表、ATMのWq式への代入は手計算でも確認した。

## 独立レビューの重点

- r03a-q2/r06h-q2: 原問は統合後Tsのみを明示し、統合前後のサービス時間同一を明言していない。公式答えエを再現する前後同じ平均サービス時間の想定を解説に明示。原問は変更していない。追加前提が必要な点はdesignにも記録。
- r04a-q1: n=1の実際の最大値は1ビット、n≥2で2nビットを達成する。既存解説の境界例と公式答えイを維持。
- r05h-q4 H2: 動く対象と濃度/含有率の違いにより他三肢を排除する累積判断でtrue。
- r06a-q2 H1: 「評価する」という分類軸が四肢でエだけに当たるためtrue。
- r07h-q4: 既存H1が期限内応答の定義そのものなので、累積して全段true。

形式確認: python tools/ap-lesson-quality.py check batch-01 成功（questions=20、reviewed=0、approvedForRegistration=false）。作者自己点検であり、独立レビュー・登録・公開は未実施。

独立確認の指摘に基づき、r03h-q1のNOR/AND/ORを各肢で定義、r07h-q4 H3を9ms/11msの具体例へ改稿、r04h-q3アを系内時間比1.25との混同として説明した。修正の最終独立承認は確認者へ戻した。
