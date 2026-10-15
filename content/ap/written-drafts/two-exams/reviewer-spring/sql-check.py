# Independent semantic check of the official q6 SQL completion, using synthetic rows.
import sqlite3,json
from pathlib import Path
con=sqlite3.connect(':memory:')
con.executescript('''CREATE TABLE キャンペーン実施 (キャンペーン番号,キャンペーン種別,キャンペーン実施金額); CREATE TABLE 売上 (売上番号,店舗番号,売上年月日,会員番号,キャンペーン番号,キャンペーン種別); CREATE TABLE 売上明細 (売上番号,商品番号,商品個数,商品単価); CREATE TABLE 商品 (商品番号,商品原価); CREATE TABLE 会員 (会員番号,会員郵便番号); INSERT INTO キャンペーン実施 VALUES(1,'H',100),(1,'H',50),(1,'E',200),(2,'B',500); INSERT INTO 商品 VALUES(1,30),(2,80); INSERT INTO 会員 VALUES(1,'111'),(2,'222'); INSERT INTO 売上 VALUES(1,1,'2026-05-01',1,1,'H'),(2,1,'2026-06-01',2,1,'H'),(3,1,'2026-07-01',1,1,'H'),(4,1,'2026-07-01',2,2,'B'),(5,2,'2026-08-01',2,1,'H'),(6,1,'2024-01-01',2,1,'H'); INSERT INTO 売上明細 VALUES(1,1,2,100),(2,2,1,200);''')
c=json.loads((Path(__file__).parent.parent/'author-spring-2-6/ap-r07h-pm6.json').read_text())
blocks=c['body'].split('```sql')[1:]
sql1=blocks[0].split('```')[0].replace('［c］','FROM').replace('［d］','LEFT OUTER JOIN').replace('［e］','SUM(M.商品個数 * S.商品原価)');a=con.execute(sql1,{'キャンペーン番号':1}).fetchall(); assert sorted(a)==[('E',0,0,0,200),('H',400,140,260,150)],a
sql2=blocks[1].split('```')[0].replace('［f］',"AND U.キャンペーン種別 = 'H'").replace('［g］','ORDER BY 売上実績数 DESC');b=con.execute(sql2,{'店舗番号':1,'一年前年月日':'2025-10-15'}).fetchall();assert b==[('111',2),('222',1)],b
out={'caseId':c['id'],'method':'Python sqlite3で作者本文のSQL2本の空欄を公式例で補完して、合成データで独立実行。実教材のレコードではない。','campaignRows':a,'postcodeRows':b,'checks':['売上ゼロのEを左外部結合で保持','Hの複数回実施金額を150へSUM','売上400、原価140、粗利260を個数×単価/原価から計算','店舗/期間/種別Hで絞って郵便番号別件数を降順集約']};(Path(__file__).parent/'sql-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
