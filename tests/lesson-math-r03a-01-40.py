import itertools,ipaddress,sqlite3
assert 60000/6000/2+10+1000/10000000*1000==15.1
assert 60000/max(40,30,50)==1200
assert .4/(2*40000)==5e-6
for a,b in itertools.product((0,1),repeat=2):assert 2*(a&b)+(a^b)==a+b
for v in range(256):
 w=v|8;assert w&8 and (w&64)==(v&64)
assert 16384+16384>32767 and 20000+20000>32767
for a in range(-32768,0):
 assert -32768<=a+32767<=32767
for errors in [((0,0),(1,1)),((0,1),(1,0))]:
 syndrome=([sum(r==i for r,c in errors)%2 for i in range(4)],[sum(c==i for r,c in errors)%2 for i in range(4)])
 if errors[0]==(0,0): first=syndrome
 else:assert first==syndrome
R={('0001','a',100),('0002','b',200),('0003','d',300)};S={('0001','a',100),('0002','a',200)};assert len(R|S)==4 and len(R)*len(S)==6
c=sqlite3.connect(':memory:');c.execute('create table t(d text,a int,b int)');c.executemany('insert into t values(?,?,?)',[('D01',1000,4000),('D02',2000,5000),('D03',3000,8000)])
base="select d,'第1期' as period,a from t";other="select d,'第2期',b from t"
assert len(c.execute(base+' union '+other).fetchall())==6
assert len(c.execute(base+' intersect '+other).fetchall())==0
for ip,prefix in [('192.168.1.31',24),('10.1.2.3',17),('172.16.4.22',28)]:
 net=ipaddress.ip_network(f'{ip}/{prefix}',strict=False);assert int(ipaddress.ip_address(ip))|(~int(net.netmask)&0xffffffff)==int(net.broadcast_address)
print('PASS: Q4 parity ambiguity; Q8 bounds; Q11 disk; Q15 pipeline; Q17 fault probability; Q22 half adder; Q23 all 256 port values; Q26 sets; Q29 SQL; Q35 broadcast')
