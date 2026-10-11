import {createWorkspaceSync} from '../src/sync/workspace.js';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createMock,validateMock,mockResult,mockQuestions} from '../src/domain/mock.js';
import {submitDiagnostic,finishDiagnostic,validateDiagnostic} from '../src/domain/diagnostic.js';
import {createStateValidator} from '../src/storage/validate.js';
import {makeState} from '../src/domain/study.js';
const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const qualification=read('data/qualifications/ap/manifest.json'),questions=read('data/qualifications/ap/'+qualification.diagnostic.url),sets=read('data/qualifications/ap/'+qualification.mockSets.url).sets;
const validateState=createStateValidator({getQuestions:()=>questions,getTopics:()=>qualification.topics.map(t=>t.name),getQualification:()=>qualification,allowDiagnosticOnly:true});
const validateAttempt=a=>validateState({...makeState(),attempts:[a]});
test('模試A/Bの80問は固定順・固定4択、受け直しは別ID',()=>{
 for(const set of sets){const first=createMock(set,questions,qualification),again=createMock(set,[...questions].reverse(),qualification);
  assert.notEqual(first.id,again.id);assert.equal(first.slots.length,80);
  assert.deepEqual(first.slots.map(s=>s.attempt.questionSnapshot.id),set.slots.map(s=>s.questionId));
  assert.deepEqual(first.slots.map(s=>s.attempt.questionSnapshot),again.slots.map(s=>s.attempt.questionSnapshot));
  assert.deepEqual(validateMock(first,qualification,validateAttempt),first);assert.ok(Buffer.byteLength(JSON.stringify(first))<850000);
 }
});
test('未回答は80問の分母に含める。途中終了も完了と区別',()=>{
 const run=createMock(sets[0],questions,qualification);
 for(let i=0;i<80;i++){const q=run.slots[i].attempt.questionSnapshot;submitDiagnostic(run,i<60?q.correctChoiceId:i===70?null:q.choices.find(c=>c.id!==q.correctChoiceId).id);}
 const result=mockResult(run,qualification);assert.equal(result.scoreRate,.75);assert.equal(result.correct,60);assert.equal(result.answered,79);assert.equal(result.unanswered,1);assert.equal(run.status,'completed');
 const partial=createMock(sets[0],questions,qualification);submitDiagnostic(partial,partial.slots[0].attempt.questionSnapshot.correctChoiceId);finishDiagnostic(partial);assert.equal(partial.status,'ended_early');assert.equal(mockResult(partial,qualification).scoreRate,1/80);
});
test('元教材の更新で保存済み80問・採点は変わらない',()=>{
 const run=createMock(sets[0],questions,qualification),before=structuredClone(run);const changed=structuredClone(questions);changed[0].version++;changed[0].choices.reverse();
 assert.deepEqual(validateMock(run,qualification,validateAttempt),before);
});
test('診断と模試を区別し、不足・重複・未確認教材・順序改変・支援を拒否',()=>{
 const run=createMock(sets[0],questions,qualification);
 assert.throws(()=>validateDiagnostic(run,qualification,validateAttempt));
 assert.throws(()=>mockQuestions({...sets[0],slots:sets[0].slots.slice(0,79)},questions));
 const changed=structuredClone(run);[changed.slots[0],changed.slots[1]]=[changed.slots[1],changed.slots[0]];assert.throws(()=>validateMock(changed,qualification,validateAttempt));
 for(const edit of [r=>r.size=30,r=>r.slots[0].attempt.hintCount=1,r=>r.slots[0].attempt.answerViewedBefore=true,r=>r.mockSet.questionIds[0]=r.mockSet.questionIds[1],r=>r.mode='diagnostic']){const broken=structuredClone(run);edit(broken);assert.throws(()=>validateMock(broken,qualification,validateAttempt));}
});

test('旧ルールで模試だけ拒否されても既存計画・診断の送信を継続',async()=>{
 Object.defineProperty(globalThis,'navigator',{value:{onLine:true},configurable:true});
 const rows=[{id:'a',kind:'mock',dirty:true,owner:'uid:user',qualificationId:'ap',operationId:'one'},{id:'planning',kind:'planning',dirty:true,owner:'uid:user',qualificationId:'ap',operationId:'two'}],sent=[],statuses=[];
 const engine=createWorkspaceSync({uid:'user',qualificationId:'ap',store:{read:async()=>rows,merge:async()=>{},acknowledge:async id=>{rows.find(r=>r.id===id).dirty=false;}},remote:{pullDocuments:async()=>({rows:[],cursor:null,more:false}),pushDocument:async(uid,qualificationId,row)=>{if(row.kind==='mock')throw {code:'permission-denied'};sent.push(row.id);return {remote:{revision:1}};}},onStatus:kind=>statuses.push(kind)});
 try{await engine.run();assert.deepEqual(sent,['planning']);assert.equal(rows[0].dirty,true);assert.equal(rows[1].dirty,false);assert.equal(statuses.at(-1),'mock-rules');}finally{engine.stop();}
});
