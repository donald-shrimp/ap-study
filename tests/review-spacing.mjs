import test from 'node:test';
import assert from 'node:assert/strict';
import {createProgress} from '../src/domain/review.js';
import {selectPractice} from '../src/domain/practice.js';
import {chooseNextAction,chooseFieldAction} from '../src/domain/next-action.js';
import {addDays} from '../src/domain/planning.js';
import {spawnSync} from 'node:child_process';

const qualification={id:'ap',defaultExamPartId:'objective',topics:[{id:'db'},{id:'nw'}],examParts:[{id:'objective',practiceAvailable:true},{id:'written',practiceAvailable:false}]};
const questions=Array.from({length:800},(_,i)=>({id:`ap-q${i}`,qualificationId:'ap',examPartId:'objective',topicId:i%2?'db':'nw',packId:`pack${i%10}`}));
const record=(q,day,status='correct',patch={})=>({id:`${q.id}-${day}-${status}`,qualificationId:q.qualificationId,questionId:q.id,status,confidence:false,startedAt:day+'T01:00:00.000Z',completedAt:day+'T01:00:00.000Z',questionSnapshot:q,...patch});
const info=(rows,q=questions[0],at='2026-10-25')=>createProgress(rows).reviewInfo(q,at+'T03:00:00Z');

test('別日の自力正解を重ねると間隔が伸び、同日連打では伸びない',()=>{
 const q=questions[0],rows=[],intervals=[];
 for(let n=0;n<7;n++){
  const day=addDays('2025-01-01',n*200);rows.push(record(q,day));
  const before=info(rows,q);intervals.push(before.intervalDays);
  rows.push(record(q,day,'correct',{id:'retry'+n,completedAt:day+'T02:00:00.000Z'}));
  assert.equal(info(rows,q).intervalDays,before.intervalDays);
  assert.equal(info(rows,q).streak,n+1);
 }
 for(let n=1;n<6;n++)assert.ok(intervals[n]>intervals[n-1],intervals.join(','));
 assert.ok(intervals[2]>=17&&intervals[5]>=150);
 assert.equal(info(rows,q).successes,7);
});

test('失敗・支援・解答開示・自信なしは翌日に戻り、当日の成功で履歴を消さない',()=>{
 const q=questions[0],mastered=Array.from({length:5},(_,n)=>record(q,addDays('2025-01-01',n*40)));
 for(const patch of [{status:'incorrect'},{status:'assisted'},{status:'revealed'},{confidence:true}]){
  const rows=[...mastered,record(q,'2026-01-01','correct',patch)];
  assert.equal(info(rows,q).intervalDays,1);assert.equal(info(rows,q).streak,0);
  rows.push(record(q,'2026-01-01','correct',{id:'retry',completedAt:'2026-01-01T02:00:00.000Z'}));
  assert.equal(info(rows,q).intervalDays,1);assert.equal(info(rows,q).streak,0);
  rows.push(record(q,'2026-01-02'));assert.equal(info(rows,q).streak,1);
  assert.ok(info(rows,q).intervalDays>=2&&info(rows,q).intervalDays<=4);
 }
});

test('同日に解いた200問を分散し、再読み込み・同期順・端末TZで日程が変わらない',()=>{
 for(const successes of [1,2,3,5]){
  const rows=questions.slice(0,200).flatMap(q=>Array.from({length:successes},(_,n)=>record(q,addDays('2026-01-01',n*100))));
  const a=createProgress(rows),b=createProgress(rows.slice().reverse()),dates=new Map();
  for(const q of questions.slice(0,200)){
   const x=a.reviewInfo(q);assert.equal(x.dueDate,b.reviewInfo(q).dueDate);
   dates.set(x.dueDate,(dates.get(x.dueDate)||0)+1);
  }
  assert.ok(dates.size>=(successes===1?3:5));
  assert.ok(Math.max(...dates.values())<100);
 }
});

test('診断・模試専用試行は通常学習の復習段階を変えず、入力記録を改変しない',()=>{
 const q=questions[0],rows=[record(q,'2026-01-01'),record(q,'2026-01-02','incorrect',{diagnosticRunId:'diagnostic'}),record(q,'2026-01-03','incorrect',{questionSnapshot:{...q,diagnosticOnly:true}})];
 const before=structuredClone(rows);assert.equal(info(rows,q).streak,1);assert.equal(info(rows,q).a.id,rows[0].id);assert.deepEqual(rows,before);
});

test('復習の山があっても新問2:復習1を継続し、ホーム・分野・次問が一致する',()=>{
 const pool=questions.slice(0,200),rows=pool.slice(0,100).map(q=>record(q,'2026-01-01','incorrect',{practiceScope:{intent:'review'}})),kinds=[],seen=[];
 for(let n=0;n<30;n++){
  const progress=createProgress(rows),opts={qualification,questions:pool,attempts:rows,reviewInfo:q=>progress.reviewInfo(q,'2026-10-25T03:00:00Z')};
  const r=selectPractice(opts);assert.equal(chooseNextAction(opts).questionId,r.questionId);
  assert.equal(selectPractice({...opts,questions:pool.slice().reverse()}).questionId,r.questionId);
  const q=pool.find(q=>q.id===r.questionId);kinds.push(r.reasonCode);assert.ok(!seen.includes(q.id));seen.push(q.id);
  rows.push(record(q,'2026-10-25','correct',{id:'learn-'+n,startedAt:new Date(Date.UTC(2026,9,25,1,n)).toISOString(),completedAt:new Date(Date.UTC(2026,9,25,1,n,30)).toISOString()}));
 }
 assert.deepEqual(kinds,Array.from({length:30},(_,n)=>n%3===2?'due':'new'));
 const progress=createProgress(rows),opts={qualification,questions:pool,attempts:rows,reviewInfo:q=>progress.reviewInfo(q,'2026-10-25T03:00:00Z'),scope:{topicId:'db',examPartId:'objective'}};
 assert.equal(chooseFieldAction({...opts,topicId:'db',examPartId:'objective'}).questionId,selectPractice({...opts,intent:'topic'}).questionId);
});

test('資格・科目・分野・明示復習・直接指定を通常学習の混合枠から分離する',()=>{
 const pool=questions.slice(0,20),rows=pool.slice(0,5).map(q=>record(q,'2026-01-01','incorrect',{practiceScope:{intent:'review'}}));
 const choose=extra=>{const attempts=[...rows,...extra],p=createProgress(attempts);return selectPractice({qualification,questions:pool,attempts,scope:{topicId:'db'},reviewInfo:q=>p.reviewInfo(q,'2026-10-25T03:00:00Z')});};
 for(const patch of [{qualificationId:'other'},{diagnosticRunId:'diag'},{practiceScope:{intent:'review'}},{practiceScope:{intent:'direct'}}]){
  const extra=pool.slice(5,7).map(q=>record(q,'2026-10-24','correct',patch));assert.equal(choose(extra).reasonCode,'new');
 }
 const extra=[pool[6],pool[8]].map(q=>record(q,'2026-10-24'));assert.equal(choose(extra).reasonCode,'new');
 const scoped=[pool[5],pool[7]].map(q=>record(q,'2026-10-24'));assert.equal(choose(scoped).reasonCode,'due');
 const p=createProgress(rows),opts={qualification,questions:pool,attempts:rows,reviewInfo:q=>p.reviewInfo(q,'2026-10-25T03:00:00Z')};
 assert.equal(selectPractice({...opts,intent:'review'}).reasonCode,'due');
 assert.equal(selectPractice({...opts,available:q=>q.id===pool[0].id}).reasonCode,'due');
 assert.equal(selectPractice({...opts,scope:{order:'number',packId:pool[0].packId}}).questionId,pool[0].id);
});

test('800問を21日×20問学ぶと、新問の進行と復習の両方が止まらない',()=>{
 const rows=[],counts={new:0,due:0,needs:0,recheck:0};
 for(let d=0;d<21;d++){
  const day=addDays('2026-10-01',d),visited=[];
  for(let n=0;n<20;n++){
   const p=createProgress(rows),r=selectPractice({qualification,questions,attempts:rows,reviewInfo:q=>p.reviewInfo(q,day+'T03:00:00Z'),visitedQuestionIds:visited});
   assert.equal(r.kind,'question');visited.push(r.questionId);counts[r.reasonCode]++;
   const q=questions.find(q=>q.id===r.questionId);
   rows.push(record(q,day,n%5===0?'assisted':'correct',{id:`day${d}-${n}`,startedAt:new Date(Date.parse(day+'T01:00:00Z')+n*60000).toISOString(),completedAt:new Date(Date.parse(day+'T01:00:00Z')+n*60000+30000).toISOString()}));
  }
 }
 assert.ok(counts.new>=280,JSON.stringify(counts));assert.ok(counts.due>=100,JSON.stringify(counts));
 assert.equal(counts.needs+counts.recheck,0);
 console.log('21日×20問の合成履歴:',counts);
});


test('自力正解の分散日と段階は端末タイムゾーンや同時刻の同期順に依存しない',()=>{
 const script=`import {createProgress} from './src/domain/review.js';const rows=['2026-10-01T14:59:00Z','2026-10-01T15:01:00Z'].map((completedAt,i)=>({id:String(i),questionId:'q',status:'correct',completedAt}));const r=createProgress(rows,{timeZone:'Asia/Tokyo'}).reviewInfo({id:'q'},'2026-10-02T01:00:00Z');console.log(JSON.stringify({due:r.dueDate,interval:r.intervalDays,streak:r.streak}));`;
 const outputs=['UTC','Asia/Tokyo','America/New_York'].map(TZ=>{const r=spawnSync(process.execPath,['--input-type=module','-e',script],{cwd:new URL('..',import.meta.url),env:{...process.env,TZ},encoding:'utf8'});assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);});
 assert.deepEqual(outputs,[outputs[0],outputs[0],outputs[0]]);assert.equal(outputs[0].streak,2);
 const q=questions[0],rows=[record(q,'2026-01-01','correct',{id:'a'}),record(q,'2026-01-01','incorrect',{id:'z'})];
 assert.deepEqual(info(rows,q),info(rows.slice().reverse(),q));assert.equal(info(rows,q).intervalDays,1);
});
