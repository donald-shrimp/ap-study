import {toRecord} from '../src/v2/records.js';
import {encodeResource} from '../src/v2/resources.js';
import {createMock} from '../src/domain/mock.js';
import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {initializeTestEnvironment,assertSucceeds,assertFails} from '@firebase/rules-unit-testing';
import {doc,setDoc,getDoc,getDocs,collection,deleteDoc,serverTimestamp,writeBatch,query,orderBy,limit,startAfter} from 'firebase/firestore';
import {createAttempt,selectAnswer,gradeAttempt,finalizeAttempt,openHint} from '../src/domain/study.js';
import {createDiagnostic,submitDiagnostic} from '../src/domain/diagnostic.js';
import {blankPlan} from '../src/domain/planning.js';

let env;
const manifest=JSON.parse(readFileSync(new URL('../data/qualifications/ap/manifest.json',import.meta.url)));
const questions=JSON.parse(readFileSync(new URL('../data/qualifications/ap/'+manifest.packs.find(p=>p.id==='r07h').url,import.meta.url)));
const q=questions[0];
const path=(uid,id,qual='ap')=>`users/${uid}/qualifications/${qual}/attemptsV2/${id}`;
function envelope(a,revision=1,deviceId='device-one'){
 const payload=toRecord(a);return {version:2,deviceId,revision,operationId:`${a.id}:${revision}`,payload,updatedAt:serverTimestamp()};
}
before(async()=>{env=await initializeTestEnvironment({projectId:'hito-mon',firestore:{host:'127.0.0.1',port:8080,rules:readFileSync(new URL('../firestore.rules',import.meta.url),'utf8')}});await env.clearFirestore();});
after(async()=>{await env.cleanup();});
test('本人の中断・回答・回答後ヒントだけ更新できる',async()=>{
 const db=env.authenticatedContext('alice').firestore(),a=createAttempt(q),ref=doc(db,path('alice',a.id));
 await assertSucceeds(setDoc(ref,envelope(a)));openHint(a);await assertSucceeds(setDoc(ref,envelope(a,2)));
 selectAnswer(a,q.answer);finalizeAttempt(a,gradeAttempt(a));await assertSucceeds(setDoc(ref,envelope(a,3)));
 openHint(a);await assertSucceeds(setDoc(ref,envelope(a,4)));await assertSucceeds(getDoc(ref));
 await assertSucceeds(getDocs(collection(db,'users/alice/qualifications/ap/attemptsV2')));
});
test('未認証・他人の参照/書込/一覧と削除は拒否する',async()=>{
 const a=createAttempt(q),alice=env.authenticatedContext('alice').firestore(),bob=env.authenticatedContext('bob').firestore(),guest=env.unauthenticatedContext().firestore();
 await assertSucceeds(setDoc(doc(alice,path('alice',a.id)),envelope(a)));
 for(const db of [bob,guest]){await assertFails(getDoc(doc(db,path('alice',a.id))));await assertFails(setDoc(doc(db,path('alice',a.id)),envelope(a,2)));await assertFails(getDocs(collection(db,'users/alice/qualifications/ap/attemptsV2')));}
 await assertFails(deleteDoc(doc(alice,path('alice',a.id))));
 await assertFails(setDoc(doc(alice,'public/any'),{text:'no'}));
});
test('確定回答・原本・端末・旧リビジョン・正答開示判定の改ざんを拒否する',async()=>{
 const db=env.authenticatedContext('alice').firestore(),a=createAttempt(q);selectAnswer(a,q.answer);finalizeAttempt(a,gradeAttempt(a));const ref=doc(db,path('alice',a.id));await assertSucceeds(setDoc(ref,envelope(a,5)));
 const altered=structuredClone(a);altered.status='incorrect';altered.selected=(q.answer+1)%4;altered.selectedChoiceId=q.choices[altered.selected].id;
 await assertFails(setDoc(ref,envelope(altered,6)));
 const snapshot=structuredClone(a);snapshot.questionSnapshot.title='changed';await assertFails(setDoc(ref,envelope(snapshot,6)));
 await assertFails(setDoc(ref,envelope(a,4)));await assertFails(setDoc(ref,envelope(a,6,'other-device')));
 const reveal=createAttempt(q);reveal.answerViewedBefore=true;selectAnswer(reveal,(q.answer+1)%4);finalizeAttempt(reveal,'incorrect');await assertFails(setDoc(doc(db,path('alice',reveal.id)),envelope(reveal)));
 const wrongQualification=envelope(a,6);wrongQualification.payload.qualificationId='other';await assertFails(setDoc(ref,wrongQualification));
 const fakeTime=envelope(a,6);fakeTime.updatedAt=new Date();await assertFails(setDoc(ref,fakeTime));
});
test('同じサーバー時刻の105件を100件ずつ欠落なく取得できる',async()=>{
 await env.withSecurityRulesDisabled(async context=>{const db=context.firestore(),batch=writeBatch(db);for(let i=0;i<105;i++){const a=createAttempt(q,{id:`page-${String(i).padStart(3,'0')}`});batch.set(doc(db,path('pagination',a.id)),envelope(a));}await batch.commit();});
 const db=env.authenticatedContext('pagination').firestore(),ref=collection(db,'users/pagination/qualifications/ap/attemptsV2');
 const first=await assertSucceeds(getDocs(query(ref,orderBy('updatedAt'),orderBy('__name__'),limit(100))));
 assert.equal(first.size,100);const last=first.docs.at(-1);
 const next=await assertSucceeds(getDocs(query(ref,orderBy('updatedAt'),orderBy('__name__'),startAfter(last.data().updatedAt,last.id),limit(100))));
 assert.equal(next.size,5);assert.equal(new Set([...first.docs,...next.docs].map(d=>d.id)).size,105);
});
const qualification=JSON.parse(readFileSync(new URL('../content/ap/qualification.json',import.meta.url)));
const resourcePath=(uid,id)=>`users/${uid}/qualifications/ap/resourcesV2/${id}`;
const resourceEnvelope=(kind,payload,revision=1)=>({version:2,kind,revision,operationId:`resource:${revision}`,deviceId:'device',payload:encodeResource(kind,payload),updatedAt:serverTimestamp()});
test('計画は本人のみ保存でき、古い版・他資格・他人・削除を拒否する',async()=>{
 const db=env.authenticatedContext('planner').firestore(),other=env.authenticatedContext('other').firestore(),guest=env.unauthenticatedContext().firestore(),p=blankPlan(qualification),ref=doc(db,resourcePath('planner','planning'));
 await assertSucceeds(setDoc(ref,resourceEnvelope('planning',p)));p.examDates=[{examPartId:'objective',date:'2026-11-04'}];p.phases=JSON.parse(readFileSync(new URL('../schemas/study-plan.example.json',import.meta.url))).phases;await assertSucceeds(setDoc(ref,resourceEnvelope('planning',p,2)));
 await assertFails(setDoc(ref,resourceEnvelope('planning',p,2)));await assertFails(setDoc(ref,resourceEnvelope('planning',{...p,qualificationId:'other'},3)));
 for(const client of [other,guest]){await assertFails(getDoc(doc(client,resourcePath('planner','planning'))));await assertFails(setDoc(doc(client,resourcePath('planner','planning')),resourceEnvelope('planning',p,3)));}
 await assertFails(deleteDoc(ref));await assertSucceeds(getDocs(collection(db,'users/planner/qualifications/ap/resourcesV2')));
});
test('30問診断を保存・回答・終了でき、支援と終了後の変更を拒否する',async()=>{
 const db=env.authenticatedContext('diagnostic').firestore(),run=createDiagnostic(questions.slice(0,30),qualification),ref=doc(db,resourcePath('diagnostic',run.id));
 await assertSucceeds(setDoc(ref,resourceEnvelope('diagnostic',run)));
 run.currentChoiceId=run.slots[0].attempt.questionSnapshot.correctChoiceId;await assertSucceeds(setDoc(ref,resourceEnvelope('diagnostic',run,2)));
 const hinted=structuredClone(run);hinted.slots[0].attempt.hintCount=1;await assertFails(setDoc(ref,resourceEnvelope('diagnostic',hinted,3)));
 submitDiagnostic(run,run.currentChoiceId);await assertSucceeds(setDoc(ref,resourceEnvelope('diagnostic',run,3)));
 const changed=structuredClone(run);changed.responses[run.slots[0].id]='different';await assertFails(setDoc(ref,resourceEnvelope('diagnostic',changed,4)));
 for(let i=1;i<30;i++)submitDiagnostic(run,run.slots[run.currentIndex].attempt.questionSnapshot.correctChoiceId);
 await assertSucceeds(setDoc(ref,resourceEnvelope('diagnostic',run,4)));
 const reopened=structuredClone(run);reopened.status='in_progress';reopened.completedAt=null;await assertFails(setDoc(ref,resourceEnvelope('diagnostic',reopened,5)));
});

test('計画の前提は本人だけ保存でき、未知項目・型・長さ・学習時間を検証する',async()=>{
 const db=env.authenticatedContext('context-planner').firestore(),ref=doc(db,resourcePath('context-planner','planning')),p={...blankPlan(qualification),context:{studiedScope:'教科書を一周',materials:'手元の教材',weeklyMinutes:180,constraints:'週末のみ',rationale:'広く確認',updatedOn:'2026-10-07'}};
 await assertSucceeds(setDoc(ref,resourceEnvelope('planning',p)));
 for(const context of [null,[],{unknown:'value'},{weeklyMinutes:-1},{weeklyMinutes:1.5},{weeklyMinutes:10081},{materials:'x'.repeat(2001)},{updatedOn:'not-date'}])await assertFails(setDoc(ref,resourceEnvelope('planning',{...p,context},2)));
 await assertFails(getDoc(doc(env.authenticatedContext('other').firestore(),resourcePath('context-planner','planning'))));
 await assertSucceeds(setDoc(ref,resourceEnvelope('planning',{...p,context:{}},2)));
});

test('診断専用問題は通常の試行コレクションへ書き込めない',async()=>{
 const db=env.authenticatedContext('no-derived-attempt').firestore(),a=createAttempt(q);
 a.questionSnapshot.diagnosticOnly=true;a.questionSnapshot.parentQuestionId='parent';
 await assertFails(setDoc(doc(db,path('no-derived-attempt',a.id)),envelope(a)));
});

const learningPath=(uid,id)=>`users/${uid}/qualifications/ap/learningV2/${id}`;
test('紙ペンと先送りは本人だけ保存・解除でき、旧版と削除を拒否する',async()=>{
 const db=env.authenticatedContext('preferences').firestore(),ref=doc(db,learningPath('preferences','desk--q'));
 await assertSucceeds(setDoc(ref,resourceEnvelope('desk',{questionId:'q',value:true})));
 await assertSucceeds(setDoc(ref,resourceEnvelope('desk',{questionId:'q',value:false},2)));
 await assertFails(setDoc(ref,resourceEnvelope('desk',{questionId:'q',value:true},2)));
 await assertFails(setDoc(ref,resourceEnvelope('desk',{questionId:'q',value:'true'},3)));
 await assertFails(setDoc(ref,resourceEnvelope('desk',{questionId:'other',value:true},3)));
 await assertFails(deleteDoc(ref));
 for(const client of [env.authenticatedContext('other').firestore(),env.unauthenticatedContext().firestore()])await assertFails(getDoc(doc(client,learningPath('preferences','desk--q'))));
 await assertSucceeds(setDoc(doc(db,learningPath('preferences','deferred--q')),resourceEnvelope('deferred',{questionId:'q',value:true})));
});
test('再開範囲は回答とは別に保存し、不正な入口・戻り先・余分な回答を拒否する',async()=>{
 const db=env.authenticatedContext('scope').firestore(),ref=doc(db,learningPath('scope','context--a'));
 const p={attemptId:'a',questionId:'q',entryMode:'desk',scope:{intent:'review',topicId:'database',topicIds:[],examPartId:'objective',examPartIds:[],paperMode:'desk',returnView:'review',returnRunId:null}};
 await assertSucceeds(setDoc(ref,resourceEnvelope('context',p)));
 for(const bad of [{...p,entryMode:'paperless'},{...p,answer:3},{...p,scope:{...p.scope,returnView:'unsafe'}},{...p,scope:{...p.scope,extra:true}}])await assertFails(setDoc(ref,resourceEnvelope('context',bad,2)));
 // New kinds cannot enter the old resources stream consumed by older PWAs.
 await assertFails(setDoc(doc(db,resourcePath('scope','context--a')),resourceEnvelope('context',p)));
});

test('単語帳評価と観測済み削除・復元は本人だけ追記し、既存文書の変更は拒否する',async()=>{
 const uid='cards-rules',db=env.authenticatedContext(uid).firestore();
 const make=(kind,payload)=>({version:2,kind,revision:1,operationId:`${kind}--${payload.id}`,deviceId:'phone',payload,updatedAt:serverTimestamp()});
 const ref=(db,id)=>doc(db,`users/${uid}/qualifications/ap/cardsV2/${id}`);
 const rating={id:'event',cardId:'card',cardVersion:1,outcome:'again',at:'2026-10-10T00:00:00.000Z'};
 for(const [kind,payload] of [['rating',rating],['reset',{id:'clear',eventIds:['event']}],['restore',{id:'import',eventIds:['event'],resetIds:['clear']}]]){
  const value=make(kind,payload),r=ref(db,value.operationId);await assertSucceeds(setDoc(r,value));await assertSucceeds(getDoc(r));await assertFails(setDoc(r,value));await assertFails(deleteDoc(r));
  for(const other of [env.authenticatedContext('other').firestore(),env.unauthenticatedContext().firestore()]){await assertFails(getDoc(ref(other,value.operationId)));await assertFails(setDoc(ref(other,'rating--other'),make('rating',{...rating,id:'other'})));}
 }
 await assertSucceeds(getDocs(collection(db,`users/${uid}/qualifications/ap/cardsV2`)));
 for(const payload of [{...rating,id:'invalid',outcome:'unknown'},{...rating,id:'invalid',cardVersion:0},{...rating,id:'invalid',at:'not-date'},{...rating,id:'invalid',extra:1}])await assertFails(setDoc(ref(db,'rating--invalid'),make('rating',payload)));
 for(const eventIds of [[],['e','e'],Array.from({length:201},(_,i)=>`e${i}`)])await assertFails(setDoc(ref(db,'reset--invalid'),make('reset',{id:'invalid',eventIds})));
 await assertFails(setDoc(doc(db,resourcePath(uid,'rating--invalid')),make('rating',{...rating,id:'invalid'})));
 await assertFails(setDoc(doc(db,learningPath(uid,'rating--invalid')),make('rating',{...rating,id:'invalid'})));
});

const personalPath=(uid,id,qual='ap')=>`users/${uid}/qualifications/${qual}/personalV2/${id}`;
const personalEnvelope=(kind,payload,revision=1,deviceId='phone')=>({version:2,kind,payload,revision,deviceId,operationId:`${deviceId}:${kind}:${revision}`,updatedAt:serverTimestamp()});
test('分野メモは本人だけ更新・空欄化でき、文字数・未知種類・旧版・削除を拒否する',async()=>{
 const db=env.authenticatedContext('notes').firestore(),ref=doc(db,personalPath('notes','note--network')),payload={topicId:'network',text:'教科書 p.20'};
 await assertSucceeds(setDoc(ref,personalEnvelope('note',payload)));
 for(const other of [env.unauthenticatedContext().firestore(),env.authenticatedContext('someone').firestore()]){await assertFails(getDoc(doc(other,personalPath('notes','note--network'))));await assertFails(setDoc(doc(other,personalPath('notes','note--network')),personalEnvelope('note',payload,2)));}
 await assertFails(setDoc(ref,personalEnvelope('note',payload,1)));
 await assertFails(setDoc(ref,personalEnvelope('note',{...payload,text:'x'.repeat(201)},2)));
 await assertFails(setDoc(ref,personalEnvelope('note',{...payload,extra:true},2)));
 await assertFails(setDoc(doc(db,personalPath('notes','draft--network')),personalEnvelope('draft',{...payload,baseRevision:1})));
 await assertSucceeds(setDoc(ref,personalEnvelope('note',{...payload,text:''},2,'pc')));
 await assertFails(deleteDoc(ref));await assertSucceeds(getDocs(collection(db,'users/notes/qualifications/ap/personalV2')));
 assert.equal((await getDoc(doc(db,personalPath('notes','note--network','other')))).exists(),false);
});
test('単語帳の再開位置は端末別文書で更新し、別端末IDへの変更を拒否する',async()=>{
 const db=env.authenticatedContext('resume-cards').firestore(),ref=doc(db,personalPath('resume-cards','checkpoint--phone'));
 const payload={deviceId:'phone',at:'2026-10-11T01:00:00.000Z',checkpoint:{cardId:'card',cardVersion:1,flipped:false,seen:[],recent:[],topicId:null}};
 await assertSucceeds(setDoc(ref,personalEnvelope('checkpoint',payload)));
 await assertFails(setDoc(ref,personalEnvelope('checkpoint',payload,2,'pc')));
 await assertFails(setDoc(ref,personalEnvelope('checkpoint',{...payload,checkpoint:{...payload.checkpoint,flipped:'yes'}},2)));
 await assertFails(setDoc(ref,personalEnvelope('checkpoint',{...payload,checkpoint:{...payload.checkpoint,recent:Array(11).fill('card')}},2)));
 await assertSucceeds(setDoc(ref,personalEnvelope('checkpoint',{...payload,checkpoint:null},2)));
 await assertSucceeds(setDoc(doc(db,personalPath('resume-cards','checkpoint--pc')),personalEnvelope('checkpoint',{...payload,deviceId:'pc'},1,'pc')));
 await assertFails(deleteDoc(ref));
});

test('固定80問の模試は本人だけ保存・再開でき、問題順・確定回答・終了後を変更できない',async()=>{
 const sets=JSON.parse(readFileSync(new URL('../data/qualifications/ap/'+manifest.mockSets.url,import.meta.url))).sets;
 const variants=JSON.parse(readFileSync(new URL('../data/qualifications/ap/'+manifest.assessment.url,import.meta.url)));
 const run=createMock(sets[0],variants,qualification),db=env.authenticatedContext('mock-user').firestore(),ref=doc(db,resourcePath('mock-user',run.id));
 await assertSucceeds(setDoc(ref,resourceEnvelope('mock',run)));
 for(const client of [env.authenticatedContext('mock-other').firestore(),env.unauthenticatedContext().firestore()]){await assertFails(getDoc(doc(client,resourcePath('mock-user',run.id))));await assertFails(setDoc(doc(client,resourcePath('mock-user',run.id)),resourceEnvelope('mock',run,2)));}
 const reorder=structuredClone(run);reorder.slots.reverse();await assertFails(setDoc(ref,resourceEnvelope('mock',reorder,2)));
 const identity=structuredClone(run);identity.mockSet.label='changed';await assertFails(setDoc(ref,resourceEnvelope('mock',identity,2)));
 const policy=structuredClone(run);policy.assistance='hints';await assertFails(setDoc(ref,resourceEnvelope('mock',policy,2)));
 submitDiagnostic(run,run.slots[0].attempt.questionSnapshot.correctChoiceId);await assertSucceeds(setDoc(ref,resourceEnvelope('mock',run,2)));
 const answer=structuredClone(run);answer.responses[run.slots[0].id]='choice-unknown';await assertFails(setDoc(ref,resourceEnvelope('mock',answer,3)));
 for(let i=1;i<80;i++)submitDiagnostic(run,run.slots[i].attempt.questionSnapshot.correctChoiceId);
 await assertSucceeds(setDoc(ref,resourceEnvelope('mock',run,3)));
 const reopened=structuredClone(run);reopened.status='in_progress';reopened.completedAt=null;await assertFails(setDoc(ref,resourceEnvelope('mock',reopened,4)));await assertFails(deleteDoc(ref));
 const wrongSize=createMock(sets[1],variants,qualification);wrongSize.size=30;await assertFails(setDoc(doc(db,resourcePath('mock-user',wrongSize.id)),resourceEnvelope('mock',wrongSize)));
});

import {createPlanRevision} from '../src/domain/plan-history.js';
test('計画履歴は本人のみ保存・取得し、同じIDの内容変更・他資格・削除を拒否する',async()=>{
 const db=env.authenticatedContext('history').firestore(),r=createPlanRevision(blankPlan(qualification),qualification),ref=doc(db,resourcePath('history',r.id));
 await assertSucceeds(setDoc(ref,resourceEnvelope('planRevision',r)));await assertSucceeds(getDoc(ref));
 await assertSucceeds(setDoc(ref,resourceEnvelope('planRevision',r,2)));
 for(const patch of [{origin:'baseline'},{savedAt:'2026-10-01T00:00:00.000Z'},{plan:{...r.plan,examDates:[{examPartId:'objective',date:'2026-11-01'}]}}])await assertFails(setDoc(ref,resourceEnvelope('planRevision',{...r,...patch},3)));
 await assertFails(deleteDoc(ref));
 for(const client of [env.authenticatedContext('other').firestore(),env.unauthenticatedContext().firestore()]){await assertFails(getDoc(doc(client,resourcePath('history',r.id))));await assertFails(setDoc(doc(client,resourcePath('history',r.id)),resourceEnvelope('planRevision',r,3)));}
 for(const patch of [{id:'other'},{qualificationId:'other'},{origin:'invalid'},{extra:true},{previousId:'plan--invalid'},{savedAt:'invalid'}])await assertFails(setDoc(doc(db,resourcePath('history','plan--invalid')),resourceEnvelope('planRevision',{...r,id:'plan--invalid',...patch})));
});


test('親なし独自40問の診断・模試を別資格で保存でき、用途とサイズ改変を拒否する',async()=>{
 const qual={...qualification,id:'synthetic',diagnosticBlueprint:{size:40}};
 const independent=questions.slice(0,40).map((source,i)=>{const q={...structuredClone(source),id:'independent-'+i,qualificationId:qual.id,sourceKind:'authored',uses:['diagnostic','mock']};delete q.parentQuestionId;delete q.diagnosticOnly;return q;});
 const db=env.authenticatedContext('generic').firestore();
 const ref=(id)=>doc(db,`users/generic/qualifications/synthetic/resourcesV2/${id}`);
 const run=createDiagnostic(independent,qual);await assertSucceeds(setDoc(ref(run.id),resourceEnvelope('diagnostic',run)));
 submitDiagnostic(run,run.slots[0].attempt.questionSnapshot.correctChoiceId);await assertSucceeds(setDoc(ref(run.id),resourceEnvelope('diagnostic',run,2)));
 const resized=structuredClone(run);resized.size=41;await assertFails(setDoc(ref(run.id),resourceEnvelope('diagnostic',resized,3)));
 const set={id:'fixed40',label:'非公開テスト',version:1,status:'ready',size:40,slots:independent.map((q,i)=>({number:i+1,questionId:q.id,topicId:q.topicId}))};
 const mock=createMock(set,independent,qual);await assertSucceeds(setDoc(ref(mock.id),resourceEnvelope('mock',mock)));
 submitDiagnostic(mock,mock.slots[0].attempt.questionSnapshot.correctChoiceId);await assertSucceeds(setDoc(ref(mock.id),resourceEnvelope('mock',mock,2)));
 const foreign=env.authenticatedContext('other').firestore();await assertFails(getDoc(doc(foreign,ref(mock.id).path)));
 const a=createAttempt({...independent[0],uses:['practice'],hints:[]});await assertSucceeds(setDoc(doc(db,path('generic',a.id,'synthetic')),envelope(a)));a.questionSnapshot.uses=['diagnostic','mock'];await assertFails(setDoc(doc(db,path('generic',a.id,'synthetic')),envelope(a,2)));
});

test('複数選択の途中・採点・回答後ヒントを同期し、不明ID・重複・部分正解・型の混在を拒否',async()=>{
 const multi={...structuredClone(q),type:'multipleChoice',answer:null,correctChoiceIds:['choice-0','choice-2'],selection:{mode:'exact',count:2},grading:{method:'exactChoiceSet'}};delete multi.correctChoiceId;
 const uid='multi-rules',db=env.authenticatedContext(uid).firestore(),a=createAttempt(multi),ref=doc(db,path(uid,a.id));
 await assertSucceeds(setDoc(ref,envelope(a)));a.selectedChoiceIds=['choice-2'];await assertSucceeds(setDoc(ref,envelope(a,2)));
 for(const ids of [['unknown'],['choice-0','choice-0'],['choice-0',null]])await assertFails(setDoc(ref,envelope({...a,selectedChoiceIds:ids},3)));
 for(const patch of [{selected:0},{selectedChoiceId:'choice-0'}]){const value=envelope(a,3);Object.assign(value.payload.response,patch);await assertFails(setDoc(ref,value));}
 const partial=structuredClone(a);finalizeAttempt(partial,'correct');await assertFails(setDoc(ref,envelope(partial,3)));
 const short=structuredClone(a);finalizeAttempt(short,'incorrect');await assertFails(setDoc(ref,envelope(short,3)));
 a.selectedChoiceIds=['choice-0','choice-2'];finalizeAttempt(a,gradeAttempt(a));await assertSucceeds(setDoc(ref,envelope(a,3)));openHint(a);await assertSucceeds(setDoc(ref,envelope(a,4)));
 await assertFails(setDoc(ref,envelope({...a,selectedChoiceIds:['choice-1','choice-2'],status:'incorrect'},5)));
 const wrong=createAttempt(multi);wrong.selectedChoiceIds=['choice-1','choice-2'];finalizeAttempt(wrong,gradeAttempt(wrong));await assertSucceeds(setDoc(doc(db,path(uid,wrong.id)),envelope(wrong)));
 const twenty={...structuredClone(multi),choices:Array.from({length:20},(_,i)=>({id:'choice-'+i,label:String(i+1),text:'検証用'})),correctChoiceIds:['choice-0','choice-19']};const wide=createAttempt(twenty);wide.selectedChoiceIds=['choice-0','choice-19'];finalizeAttempt(wide,gradeAttempt(wide));await assertSucceeds(setDoc(doc(db,path(uid,wide.id)),envelope(wide)));
 const defer=createAttempt(multi);defer.questionSnapshot.type='freeText';defer.questionSnapshot.correctChoiceId='choice-0';defer.questionSnapshot.grading={method:'deferred'};await assertFails(setDoc(doc(db,path(uid,defer.id)),envelope(defer)));
});
test('複数選択の診断・固定模試は配列の途中回答を保存し、確定組合せを変更できない',async()=>{
 const questions=Array.from({length:30},(_,i)=>{const m={...structuredClone(q),id:'multi-'+i,type:'multipleChoice',sourceKind:'authored',uses:['diagnostic','mock'],answer:null,correctChoiceIds:['choice-0','choice-2'],selection:{mode:'exact',count:2},grading:{method:'exactChoiceSet'}};delete m.correctChoiceId;return m;});
 const db=env.authenticatedContext('multi-assessment').firestore();
 const set={id:'multi-fixed',label:'合成テスト',version:1,status:'ready',size:30,slots:questions.map((q,i)=>({number:i+1,questionId:q.id,topicId:q.topicId}))};
 for(const [kind,run] of [['diagnostic',createDiagnostic(questions,qualification)],['mock',createMock(set,questions,qualification)]]){
  const ref=doc(db,resourcePath('multi-assessment',run.id));await assertSucceeds(setDoc(ref,resourceEnvelope(kind,run)));run.currentChoiceId=['choice-2'];await assertSucceeds(setDoc(ref,resourceEnvelope(kind,run,2)));
  run.currentChoiceId=['choice-0','choice-2'];submitDiagnostic(run,run.currentChoiceId);await assertSucceeds(setDoc(ref,resourceEnvelope(kind,run,3)));
  const changed=structuredClone(run);changed.responses[run.slots[0].id]=['choice-1','choice-2'];await assertFails(setDoc(ref,resourceEnvelope(kind,changed,4)));
 }
});

import {createCaseRun,caseFields,setCaseResponse,submitCaseField,viewCaseAnswer,rateCaseField} from '../src/domain/case-study.js';
const pilot=JSON.parse(readFileSync(new URL('../content/ap/written-cases.json',import.meta.url)))[0];
const casePath=(uid,id)=>`users/${uid}/qualifications/ap/writtenV2/${id}`;
test('Bの部分回答・自己評価・完了は本人のみ保存し、確定回答・教材・他人・不正評価を拒否',async()=>{
 const uid='written-rules',db=env.authenticatedContext(uid).firestore(),r=createCaseRun(pilot),ref=doc(db,casePath(uid,r.id));let rev=1;
 const save=()=>setDoc(ref,resourceEnvelope('case',r,rev++));await assertSucceeds(save());const slots=caseFields(pilot),first=slots[0];setCaseResponse(r,first.key,'未知表現');await assertSucceeds(save());submitCaseField(r,first.key);await assertSucceeds(save());viewCaseAnswer(r,first.key);await assertSucceeds(save());rateCaseField(r,first.key,'partial');await assertSucceeds(save());
 const altered=structuredClone(r);altered.responses[first.key].value='改ざん';await assertFails(setDoc(ref,resourceEnvelope('case',altered,rev)));const source=structuredClone(r);source.material.title='changed';await assertFails(setDoc(ref,resourceEnvelope('case',source,rev)));
 const fake=structuredClone(r);fake.evaluations[first.key].outcome='correct';await assertFails(setDoc(ref,resourceEnvelope('case',fake,rev)));
 for(const slot of slots.slice(1)){submitCaseField(r,slot.key,undefined,{skip:true});await assertSucceeds(save());viewCaseAnswer(r,slot.key);await assertSucceeds(save());if(!r.evaluations[slot.key]){rateCaseField(r,slot.key,'notYet');await assertSucceeds(save());}}
 assert.equal(r.progress.status,'completed');const rewritten=structuredClone(r);rewritten.evaluations[first.key].outcome='meets';await assertFails(setDoc(ref,resourceEnvelope('case',rewritten,rev)));for(const client of [env.authenticatedContext('other').firestore(),env.unauthenticatedContext().firestore()])await assertFails(getDoc(doc(client,casePath(uid,r.id))));await assertFails(deleteDoc(ref));
 const clone=structuredClone(r);clone.id='case--imported';await assertSucceeds(setDoc(doc(db,casePath(uid,clone.id)),resourceEnvelope('case',clone)));
});
test('上限20欄の合成大問バックアップもRulesの処理量内で取り込める',async()=>{
 // Nonpublic contract fixture; this is not authored or reviewed exam material.
 const synthetic={...structuredClone(pilot),id:'synthetic20',title:'非公開の20欄形式テスト',items:Array.from({length:20},(_,i)=>({id:'field'+i,label:'合成',prompt:'形式テスト',fields:[structuredClone(pilot.items[0].fields[0])]}))};
 const r=createCaseRun(synthetic),db=env.authenticatedContext('limit20').firestore();for(const slot of caseFields(synthetic)){submitCaseField(r,slot.key,undefined,{skip:true});viewCaseAnswer(r,slot.key);rateCaseField(r,slot.key,'notYet');}await assertSucceeds(setDoc(doc(db,casePath('limit20',r.id)),resourceEnvelope('case',r)));
});
