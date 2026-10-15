from author import *
import sqlite3
cx=sqlite3.connect(':memory:')
cx.executescript('''
CREATE TABLE 国民の祝日(祝日 TEXT,祝日名 TEXT);
CREATE TABLE 会社記念日(会社番号 TEXT,会社記念日 TEXT,会社記念日名 TEXT);
CREATE TABLE 従業員(会社番号 TEXT,従業員番号 INTEGER,従業員氏名 TEXT,部署番号 INTEGER);
CREATE TABLE 部署(会社番号 TEXT,部署番号 INTEGER,部署名 TEXT,管理者番号 INTEGER);
INSERT INTO 国民の祝日 VALUES ('2024-04-01','期首境界'),('2025-03-31','期末境界'),('2025-04-01','対象外');
INSERT INTO 会社記念日 VALUES ('001','2024-06-01','創立'),('002','2024-06-01','他社創立');
INSERT INTO 従業員 VALUES ('001',3,'三郎',2),('001',2,'次郎',1),('001',1,'一郎',1),('002',1,'他社',1);
INSERT INTO 部署 VALUES ('001',1,'一部',9),('001',2,'二部',9),('001',3,'三部',8),('002',1,'他社一部',9);
''')
c=json.loads((DEST/'ap-r06h-pm6.json').read_text());body=c['body'];snips=body.split('```sql\n');sql1=snips[1].split('\n```')[0].replace('［b］','BETWEEN :年度開始日 AND :年度終了日').replace('［c］','ORDER BY');sql2=snips[2].split('\n```')[0].replace('［d］','EMP.部署番号 = DEP.部署番号').replace('［c］','ORDER BY')
r1=cx.execute(sql1,{'会社番号':'001','年度開始日':'2024-04-01','年度終了日':'2025-03-31'}).fetchall();r2=cx.execute(sql2,{'会社番号':'001','管理者番号':9}).fetchall()
assert r1==[('2024-04-01','期首境界'),('2024-06-01','創立'),('2025-03-31','期末境界')]
assert r2==[(1,'一部',1,'一郎'),(1,'一部',2,'次郎'),(2,'二部',3,'三郎')]
# SQLite cannot create a persistent cross-attached-database view; use the equivalent same-schema table/view names for projection verification, and verify explicit SQL schema tokens separately.
sql3=snips[3].split('\n```')[0].replace('［e］','C001.国民の祝日').replace('［f］','PUB.国民の祝日');assert 'CREATE VIEW C001.国民の祝日' in sql3 and 'FROM PUB.国民の祝日' in sql3
cx.execute('CREATE VIEW 国民の祝日ビュー (祝日,祝日名) AS SELECT 祝日,祝日名 FROM 国民の祝日');assert cx.execute('SELECT * FROM 国民の祝日ビュー').fetchall()==cx.execute('SELECT * FROM 国民の祝日').fetchall()
(DEST/'calculation-pm6.json').write_text(json.dumps({'method':'SQLite execution of literal transcribed SQL with filled official-example blanks. Date endpoints, company isolation, multi-department manager and sorting verified.','holidayRows':r1,'employeeRows':r2,'viewProjection':'passed with same-schema equivalent','schemaQualifiedViewSQL':sql3,'limitation':'SQLite persistent view cannot reference attached databases; cross-schema syntax checked explicitly and projection executed in same-schema equivalent.'},ensure_ascii=False,indent=2)+'\n')
