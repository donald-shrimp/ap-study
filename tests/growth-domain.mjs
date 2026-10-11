import test from 'node:test';
import assert from 'node:assert/strict';
import {learningTrend,learningFields,summarizeFields} from '../src/domain/analytics.js';
import {blankPlan} from '../src/domain/planning.js';
import {canonical,createPlanRevision,validatePlanRevision,completedPlanPeriods,planChanges} from '../src/domain/plan-history.js';
const q={id:'test',defaultExamPartId:'a',examParts:[{id:'a',label:'A',practiceAvailable:true},{id:'b',label:'B',practiceAvailable:true}],topics:[{id:'db',name:'DB'},{id:'nw',name:'NW'}]};
const at='2026-10-11T03:00:00.000Z';
const attempt=(id,questionId,status,completedAt,extra={})=>({id,questionId,status,completedAt,qualificationId:'test',questionSnapshot:{topicId:'db',examPartId:'a'},...extra});
const plan=()=>({...blankPlan(q),phases:[{id:'first',name:'基礎',start:'2026-09-01',end:'2026-09-30',examPartIds:['a'],focusTopicIds:['db'],targets:{completedAttempts:100}}]});
const revision=(p,id,date,previousId=null,origin='edited')=>createPlanRevision(p,q,{id:'plan--'+id,at:date,previousId:previousId?'plan--'+previousId:null,origin});
test('各時点の最後の結果だけを復元し、未来の解き直しを過去に漏らさない',()=>{
 const attempts=[attempt('old','same','incorrect','2026-09-06T00:00:00Z'),attempt('new','same','correct','2026-10-10T00:00:00Z'),attempt('assist','a','assisted','2026-10-10T00:00:00Z'),attempt('revealed','r','revealed','2026-10-10T00:00:00Z'),attempt('future','f','correct','2026-10-11T04:00:00Z'),attempt('diag','d','correct','2026-10-10T00:00:00Z',{diagnosticRunId:'run'}),attempt('derived','v','correct','2026-10-10T00:00:00Z',{questionSnapshot:{topicId:'db',diagnosticOnly:true}}),attempt('foreign','o','correct','2026-10-10T00:00:00Z',{qualificationId:'other'}),attempt('pending','p','in_progress','2026-10-10T00:00:00Z')];
 const data=learningTrend({qualification:q,attempts,at});assert.equal(data.points[0].correct,0);assert.equal(data.points[0].total,1);assert.equal(data.points.at(-1).rate,1/3);
 const {total,correct,rate}=data.points.at(-1);assert.deepEqual({total,correct,rate},summarizeFields(learningFields({qualification:q,attempts,at})));
});
test('JST日付境界・28日窓・同時刻のID・分野とパート・記録なし',()=>{
 const attempts=[attempt('before','x','incorrect','2026-09-13T14:59:59Z'),attempt('at','y','correct','2026-09-13T15:00:00Z'),attempt('a','tie','correct','2026-10-10T02:00:00Z'),attempt('z','tie','incorrect','2026-10-10T02:00:00Z'),attempt('nw','n','correct','2026-10-10T02:00:00Z',{questionSnapshot:{topicId:'nw',examPartId:'b'}})];
 const data=learningTrend({qualification:q,attempts,at});assert.equal(data.points.at(-1).total,3);assert.equal(data.points.at(-1).correct,2);
 assert.equal(learningTrend({qualification:q,attempts,at,examPartId:'a'}).points.at(-1).total,2);assert.equal(learningTrend({qualification:q,attempts,at,topicId:'nw'}).points.at(-1).rate,1);
 assert.ok(learningTrend({qualification:q,attempts:[],at}).points.every(p=>p.rate===null&&p.total===0));
});
test('履歴は資格・日時・未知項目を厳密に検証し、変更の内容を比較する',()=>{
 const p=plan(),r=revision(p,'one','2026-09-01T00:00:00Z');validatePlanRevision(r,q);
 for(const patch of [{qualificationId:'other'},{savedAt:'2026-02-30T00:00:00.000Z'},{previousId:r.id},{extra:true},{id:'unsafe'},{origin:'unknown'}])assert.throws(()=>validatePlanRevision({...r,...patch},q));
 assert.equal(canonical({b:2,a:[3,1]}),canonical({a:[3,1],b:2}));
 const changed=structuredClone(p);changed.phases[0].targets.completedAttempts=80;changed.phases[0].focusTopicIds=['nw'];assert.deepEqual(planChanges(p,changed,q).map(c=>c.label),['基礎の目標','重点分野']);
});
test('終了後の目標引き下げ・期間延長・削除で当時の目標を塗り替えない',()=>{
 const p=plan(),r1=revision(p,'one','2026-09-01T00:00:00Z'),later=structuredClone(p);later.phases[0].targets.completedAttempts=20;later.phases[0].end='2026-10-20';const r2=revision(later,'two','2026-10-02T00:00:00Z','one');
 const out=completedPlanPeriods({plan:later,revisions:[r1,r2],attempts:[attempt('count','x','correct','2026-09-10T00:00:00Z')],qualification:q,at});assert.equal(out.length,1);assert.equal(out[0].targets.completedAttempts,100);assert.equal(out[0].actual,1);assert.equal(out[0].baseline,false);
 const deleted={...p,phases:[]},r3=revision(deleted,'three','2026-10-03T00:00:00Z','two');assert.equal(completedPlanPeriods({plan:deleted,revisions:[r1,r2,r3],attempts:[],qualification:q,at})[0].targets.completedAttempts,100);
});
test('終了前の取消し・延長は未完了を偽って履歴にしない',()=>{
 const p=plan(),r1=revision(p,'one','2026-09-01T00:00:00Z'),later=structuredClone(p);later.phases[0].end='2026-10-20';const r2=revision(later,'two','2026-09-20T00:00:00Z','one');
 assert.equal(completedPlanPeriods({plan:later,revisions:[r1,r2],attempts:[],qualification:q,at}).length,0);
 const deleted={...p,phases:[]},r3=revision(deleted,'three','2026-09-22T00:00:00Z','two');assert.equal(completedPlanPeriods({plan:deleted,revisions:[r1,r2,r3],attempts:[],qualification:q,at}).length,0);
});
test('別端末の不採用案は過去目標に混ぜず、既存計画の保存開始を区別する',()=>{
 const p=plan(),base=revision(p,'base','2026-09-01T00:00:00Z'),branch=structuredClone(p);branch.phases[0].targets.completedAttempts=1;const offline=revision(branch,'offline','2026-09-25T00:00:00Z','base');
 assert.equal(completedPlanPeriods({plan:p,revisions:[base,offline],attempts:[],qualification:q,at})[0].targets.completedAttempts,100);
 const baseline=revision(p,'baseline','2026-10-10T00:00:00Z',null,'baseline');assert.equal(completedPlanPeriods({plan:p,revisions:[baseline],attempts:[],qualification:q,at})[0].baseline,true);
});

import {createWorkspaceSync} from '../src/sync/workspace.js';
test('履歴のルール未公開でも計画本体は同期し、履歴は同期待ちに残す',async()=>{
 Object.defineProperty(globalThis,'navigator',{value:{onLine:true},configurable:true});
 const rows=[{id:'plan--one',kind:'planRevision',dirty:true,owner:'uid:user',qualificationId:'test',operationId:'one'},{id:'planning',kind:'planning',dirty:true,owner:'uid:user',qualificationId:'test',operationId:'two'}],sent=[],statuses=[];
 const engine=createWorkspaceSync({uid:'user',qualificationId:'test',store:{read:async()=>rows,merge:async()=>{},acknowledge:async id=>{rows.find(r=>r.id===id).dirty=false;}},remote:{pullDocuments:async()=>({rows:[],cursor:null,more:false}),pushDocument:async(uid,qualificationId,row)=>{if(row.kind==='planRevision')throw {code:'permission-denied'};sent.push(row.id);return {remote:{revision:1}};}},onStatus:kind=>statuses.push(kind)});
 try{await engine.run();assert.deepEqual(sent,['planning']);assert.equal(rows[0].dirty,true);assert.equal(statuses.at(-1),'history-rules');}finally{engine.stop();}
});

test('回答と計画を保存した直後も、Dateのミリ秒を落とさず集計する',()=>{
 const now=new Date('2026-10-11T03:00:00.900Z'),attempts=[attempt('now','same','correct','2026-10-11T03:00:00.800Z'),attempt('future','later','correct','2026-10-11T03:00:00.901Z')];
 const {total,correct,rate}=learningTrend({qualification:q,attempts,at:now}).points.at(-1);assert.deepEqual({total,correct,rate},{total:1,correct:1,rate:1});assert.deepEqual({total,correct,rate},summarizeFields(learningFields({qualification:q,attempts,at:now})));
 const p=plan(),old=revision(p,'before','2026-09-01T00:00:00Z'),changed=structuredClone(p);changed.phases[0].targets.completedAttempts=10;const saved=revision(changed,'now','2026-10-11T03:00:00.800Z','before');
 assert.equal(completedPlanPeriods({plan:changed,revisions:[old,saved],attempts:[],qualification:q,at:now})[0].targets.completedAttempts,100);
});
