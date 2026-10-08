import test from 'node:test';
import assert from 'node:assert/strict';
import {learningFields,diagnosticFields,upcomingExam} from '../src/domain/analytics.js';
import {chooseNextAction} from '../src/domain/next-action.js';
import {blankPlan} from '../src/domain/planning.js';
const at=new Date('2026-10-07T03:00:00Z');
const qualification={id:'ap',topics:[{id:'db',name:'DB'},{id:'nw',name:'NW'},{id:'empty',name:'未確認'}],defaultExamPartId:'a',examParts:[{id:'a',label:'選択式',practiceAvailable:true},{id:'b',label:'記述式',practiceAvailable:false}]};
const questions=[{id:'db1',topicId:'db',examPartId:'a',qualificationId:'ap'},{id:'db2',topicId:'db',examPartId:'a',qualificationId:'ap'},{id:'nw1',topicId:'nw',examPartId:'a',qualificationId:'ap'},{id:'b1',topicId:'db',examPartId:'b',qualificationId:'ap'}];
const attempt=(questionId,status,completedAt='2026-10-06T03:00:00Z',id=questionId)=>({id,questionId,qualificationId:'ap',status,startedAt:'2026-10-01T03:00:00Z',updatedAt:completedAt,completedAt,hintCount:0,selected:null,questionSnapshot:{...questions.find(q=>q.id===questionId),topic:'DB'}});
const plan={...blankPlan(qualification),examDates:[{examPartId:'a',date:'2026-11-04'},{examPartId:'b',date:'2026-10-09'}],phases:[{id:'foundation',name:'基礎確認',start:'2026-10-01',end:'2026-10-10',examPartIds:['a'],targets:{completedAttempts:100},focusTopicIds:['db','nw']}]};
function select(attempts=[],options={}){const rows=new Map(attempts.filter(a=>['correct','assisted','incorrect','revealed'].includes(a.status)).map(a=>[a.questionId,a]));return chooseNextAction({qualification,questions,attempts,at,reviewInfo:q=>rows.has(q.id)?{a:rows.get(q.id),isDue:false,needs:true,due:new Date('2026-10-07')}:null,...options});}

test('同じ問題の最新の完了記録だけを数え、支援・閲覧・未確認を区別する',()=>{
 const attempts=[attempt('db1','incorrect',undefined,'old'),attempt('db1','correct','2026-10-07T02:00:00Z','new'),attempt('db2','revealed'),attempt('nw1','assisted'),attempt('db2','in_progress','2026-10-07T02:30:00Z','unfinished')];
 const data=learningFields({qualification,attempts,at}),db=data.rows.find(r=>r.topicId==='db'),nw=data.rows.find(r=>r.topicId==='nw');
 assert.deepEqual([db.total,db.correct,db.incorrect,db.revealed,db.rate],[2,1,0,1,.5]);assert.equal(nw.assisted,1);assert.equal(nw.rate,0);assert.equal(data.rows.find(r=>r.topicId==='empty').rate,null);
});
test('28日・資格・パート・診断・未確認教材を切り分け、未来を数えない',()=>{
 const attempts=[attempt('db1','correct','2026-09-10T03:00:00Z'),attempt('db2','correct','2026-09-09T03:00:00Z'),{...attempt('nw1','correct'),diagnosticRunId:'run'},attempt('b1','correct'),{...attempt('db2','correct'),qualificationId:'other'},attempt('db2','correct','2026-10-07T03:01:00Z'),{...attempt('db2','correct'),questionSnapshot:{topicId:'db',diagnosticOnly:true}}];
 const data=learningFields({qualification,attempts,at,examPartId:'a'});assert.equal(data.rows.reduce((n,r)=>n+r.total,0),1);assert.equal(data.rows.find(r=>r.topicId==='db').correct,1);
});
test('少数の低い率を通常の順位より上にせず、重点は明示した計画に従う',()=>{
 const many=Array.from({length:10},(_,i)=>({...attempt('nw1','correct',undefined,'n'+i),questionId:'n'+i}));const few=[attempt('db1','incorrect')];
 assert.equal(learningFields({qualification,attempts:[...many,...few],at}).rows[0].topicId,'nw');
 assert.equal(learningFields({qualification,attempts:[...many,...few],plan,at}).rows.find(r=>r.topicId==='db').focus,true);
});
test('診断はこの1回の回答数を分母にし、未回答分野を0%にしない',()=>{
 const data=diagnosticFields({topics:[{topicId:'db',answered:2,correct:1}]},qualification);assert.equal(data.rows[0].rate,.5);assert.equal(data.rows[1].rate,null);assert.equal(diagnosticFields(null,qualification).rows.every(r=>r.total===0),true);
});
test('対象パートの受験日を選び、過ぎた日・未登録にも対応する',()=>{
 assert.equal(upcomingExam(plan,qualification,at,'a').days,28);assert.equal(upcomingExam(plan,qualification,at).label,'記述式');assert.equal(upcomingExam({...plan,examDates:[{examPartId:'a',date:'2026-10-06'}]},qualification,at).days,-1);assert.equal(upcomingExam(null,qualification,at),null);
});
test('通常の中断を最優先にし、診断・別資格・継続元は再開候補にしない',()=>{
 const paused=attempt('db1','postponed'),diagnostic={...attempt('nw1','in_progress'),diagnosticRunId:'run'};
 assert.equal(select([paused,diagnostic]).kind,'resume');assert.equal(select([paused,diagnostic]).attemptId,'db1');assert.equal(select([paused],{ignorePaused:true}).kind,'question');
 assert.equal(select([{...paused,qualificationId:'other'}]).kind,'question');assert.equal(select([paused,{...attempt('db2','correct'),continuationOf:'db1'}]).kind,'question');
});
test('期限到来の復習を選ぶが、計画から範囲を自動固定しない',()=>{
 const old=attempt('db2','assisted'),result=select([old],{plan,reviewInfo:q=>q.id==='db2'?{a:old,isDue:true,due:new Date('2026-10-06')}:null});
 assert.equal(result.questionId,'db2');assert.equal(result.reasonCode,'due');assert.equal(result.scope.topicId,null);assert.equal(result.scope.examPartId,null);
});
test('未着手を要復習より先に選び、重点は固定条件にしない',()=>{
 const a=attempt('db1','correct'),b=attempt('db2','correct');assert.equal(select([a,b],{plan}).questionId,'nw1');
 const c=attempt('nw1','correct','2026-10-02T03:00:00Z');assert.equal(select([a,b,c],{plan}).questionId,'nw1');assert.equal(select([a,b,c],{plan}).reasonCode,'needs');
});
test('期限切れ・重点なしは通常出題、教材未対応パートは通常学習に混ぜない',()=>{
 assert.equal(select([],{plan:{...plan,phases:[{...plan.phases[0],end:'2026-10-05'}]}}).reasonCode,'new');assert.notEqual(select([],{plan:{...plan,phases:[{...plan.phases[0],examPartIds:['b']}]}}).questionId,'b1');
});
test('オフラインで利用できる問題を選び、0問なら開始しない',()=>{
 const p={...plan,phases:[{...plan.phases[0],focusTopicIds:['db']}]},r=select([],{plan:p,online:false,available:q=>q.id==='nw1'});
 assert.equal(r.questionId,'nw1');assert.equal(r.reasonCode,'new');assert.equal(r.scope.topicId,null);assert.equal(select([],{available:()=>false,online:false}).kind,'unavailable');
});

test('問題スナップショットのない旧記録も資格の問題一覧から分野に数える',()=>{
 const old=attempt('db1','correct');delete old.questionSnapshot;
 const rows=learningFields({qualification,questions,attempts:[old],at,examPartId:'a'}).rows;
 assert.equal(rows.find(r=>r.topicId==='db').total,1);
});
test('明示した分野と教材対応パートは候補と継続範囲に保持する',()=>{
 const q={...qualification,examParts:qualification.examParts.map(p=>({...p,practiceAvailable:true}))},p={...plan,phases:plan.phases.map(p=>({...p,examPartIds:['b'],focusTopicIds:['db']}))};
 const selected=select([],{qualification:q,plan:p,scope:{topicId:'db',examPartId:'b'}});assert.equal(selected.questionId,'b1');assert.equal(selected.scope.topicId,'db');assert.equal(selected.scope.examPartId,'b');
});

test('パートだけ明示した場合、分野は固定しない',()=>{
 const q={...qualification,examParts:qualification.examParts.map(p=>({...p,practiceAvailable:true}))},p={...plan,phases:plan.phases.map(p=>({...p,examPartIds:['b'],focusTopicIds:[]}))};
 const selected=select([],{qualification:q,plan:p,scope:{examPartId:'b'}});assert.equal(selected.questionId,'b1');assert.equal(selected.reasonCode,'new');assert.equal(selected.scope.topicId,null);assert.equal(selected.scope.examPartId,'b');
});
