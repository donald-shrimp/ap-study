"""Reviewer/root's independent Q6 window-SQL experiment before official answer lookup."""
import sqlite3,datetime
c=sqlite3.connect(':memory:');c.execute('CREATE TABLE 在庫推移状況(年 INT,月 INT,日 INT,倉庫コード TEXT,商品コード TEXT,在庫数 INT,売上個数 INT)');by_group={}
for w,p,k in [('W1','P1',1),('W1','P2',2),('W2','P1',3)]:
 rows=[]
 for i in range(12):
  d=datetime.date(2022,12,25)+datetime.timedelta(days=i);stock=100*k+i*3;sales=k+i%4;row=(d.year,d.month,d.day,w,p,stock,sales);c.execute('INSERT INTO 在庫推移状況 VALUES(?,?,?,?,?,?,?)',row);rows.append(row)
 by_group[(w,p)]=rows
sql='''SELECT 年,月,日,倉庫コード,商品コード, AVG(在庫数) OVER 期間定義 AS 平均在庫数,SUM(売上個数) OVER 期間定義 AS 期間内売上個数 FROM 在庫推移状況 WINDOW 期間定義 AS (PARTITION BY 倉庫コード,商品コード ORDER BY 年,月,日 ASC ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)'''
result=c.execute(sql).fetchall();assert len(result)==36
for year,month,day,w,p,average,total in result:
 seq=by_group[(w,p)];i=next(i for i,r in enumerate(seq) if r[:3]==(year,month,day));window=seq[max(0,i-6):i+1];assert abs(average-sum(r[5] for r in window)/len(window))<1e-10 and total==sum(r[6] for r in window)
print('PASS 36 rows / 3 warehouse-product partitions / 7-row moving window / year-month boundary / partial initial windows')
