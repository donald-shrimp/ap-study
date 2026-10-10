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
const path=(uid,id,qual='ap')=>`users/${uid}/qualifications/${qual}/attempts/${id}`;
function envelope(a,revision=1,deviceId='device-one'){
 const {scrollY,...payload}=a;return {version:1,deviceId,revision,operationId:`${a.id}:${revision}`,payload,updatedAt:serverTimestamp()};
}
before(async()=>{env=await initializeTestEnvironment({projectId:'hito-mon',firestore:{host:'127.0.0.1',port:8080,rules:readFileSync(new URL('../firestore.rules',import.meta.url),'utf8')}});await env.clearFirestore();});
after(async()=>{await env.cleanup();});
test('本人の中断・回答・回答後ヒントだけ更新できる',async()=>{
 const db=env.authenticatedContext('alice').firestore(),a=createAttempt(q),ref=doc(db,path('alice',a.id));
 await assertSucceeds(setDoc(ref,envelope(a)));openHint(a);await assertSucceeds(setDoc(ref,envelope(a,2)));
 selectAnswer(a,q.answer);finalizeAttempt(a,gradeAttempt(a));await assertSucceeds(setDoc(ref,envelope(a,3)));
 openHint(a);await assertSucceeds(setDoc(ref,envelope(a,4)));await assertSucceeds(getDoc(ref));
 await assertSucceeds(getDocs(collection(db,'users/alice/qualifications/ap/attempts')));
});
test('未認証・他人の参照/書込/一覧と削除は拒否する',async()=>{
 const a=createAttempt(q),alice=env.authenticatedContext('alice').firestore(),bob=env.authenticatedContext('bob').firestore(),guest=env.unauthenticatedContext().firestore();
 await assertSucceeds(setDoc(doc(alice,path('alice',a.id)),envelope(a)));
 for(const db of [bob,guest]){await assertFails(getDoc(doc(db,path('alice',a.id))));await assertFails(setDoc(doc(db,path('alice',a.id)),envelope(a,2)));await assertFails(getDocs(collection(db,'users/alice/qualifications/ap/attempts')));}
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
 const db=env.authenticatedContext('pagination').firestore(),ref=collection(db,'users/pagination/qualifications/ap/attempts');
 const first=await assertSucceeds(getDocs(query(ref,orderBy('updatedAt'),orderBy('__name__'),limit(100))));
 assert.equal(first.size,100);const last=first.docs.at(-1);
 const next=await assertSucceeds(getDocs(query(ref,orderBy('updatedAt'),orderBy('__name__'),startAfter(last.data().updatedAt,last.id),limit(100))));
 assert.equal(next.size,5);assert.equal(new Set([...first.docs,...next.docs].map(d=>d.id)).size,105);
});
const qualification=JSON.parse(readFileSync(new URL('../content/ap/qualification.json',import.meta.url)));
const resourcePath=(uid,id)=>`users/${uid}/qualifications/ap/resources/${id}`;
const resourceEnvelope=(kind,payload,revision=1)=>({version:1,kind,revision,operationId:`resource:${revision}`,deviceId:'device',payload,updatedAt:serverTimestamp()});
test('計画は本人のみ保存でき、古い版・他資格・他人・削除を拒否する',async()=>{
 const db=env.authenticatedContext('planner').firestore(),other=env.authenticatedContext('other').firestore(),guest=env.unauthenticatedContext().firestore(),p=blankPlan(qualification),ref=doc(db,resourcePath('planner','planning'));
 await assertSucceeds(setDoc(ref,resourceEnvelope('planning',p)));p.examDates=[{examPartId:'objective',date:'2026-11-04'}];p.phases=JSON.parse(readFileSync(new URL('../schemas/study-plan.example.json',import.meta.url))).phases;await assertSucceeds(setDoc(ref,resourceEnvelope('planning',p,2)));
 await assertFails(setDoc(ref,resourceEnvelope('planning',p,2)));await assertFails(setDoc(ref,resourceEnvelope('planning',{...p,qualificationId:'other'},3)));
 for(const client of [other,guest]){await assertFails(getDoc(doc(client,resourcePath('planner','planning'))));await assertFails(setDoc(doc(client,resourcePath('planner','planning')),resourceEnvelope('planning',p,3)));}
 await assertFails(deleteDoc(ref));await assertSucceeds(getDocs(collection(db,'users/planner/qualifications/ap/resources')));
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

const learningPath=(uid,id)=>`users/${uid}/qualifications/ap/learning/${id}`;
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
 const make=(kind,payload)=>({version:1,kind,revision:1,operationId:`${kind}--${payload.id}`,deviceId:'phone',payload,updatedAt:serverTimestamp()});
 const ref=(db,id)=>doc(db,`users/${uid}/qualifications/ap/cards/${id}`);
 const rating={id:'event',cardId:'card',cardVersion:1,outcome:'again',at:'2026-10-10T00:00:00.000Z'};
 for(const [kind,payload] of [['rating',rating],['reset',{id:'clear',eventIds:['event']}],['restore',{id:'import',eventIds:['event'],resetIds:['clear']}]]){
  const value=make(kind,payload),r=ref(db,value.operationId);await assertSucceeds(setDoc(r,value));await assertSucceeds(getDoc(r));await assertFails(setDoc(r,value));await assertFails(deleteDoc(r));
  for(const other of [env.authenticatedContext('other').firestore(),env.unauthenticatedContext().firestore()]){await assertFails(getDoc(ref(other,value.operationId)));await assertFails(setDoc(ref(other,'rating--other'),make('rating',{...rating,id:'other'})));}
 }
 await assertSucceeds(getDocs(collection(db,`users/${uid}/qualifications/ap/cards`)));
 for(const payload of [{...rating,id:'invalid',outcome:'unknown'},{...rating,id:'invalid',cardVersion:0},{...rating,id:'invalid',at:'not-date'},{...rating,id:'invalid',extra:1}])await assertFails(setDoc(ref(db,'rating--invalid'),make('rating',payload)));
 for(const eventIds of [[],['e','e'],Array.from({length:201},(_,i)=>`e${i}`)])await assertFails(setDoc(ref(db,'reset--invalid'),make('reset',{id:'invalid',eventIds})));
 await assertFails(setDoc(doc(db,resourcePath(uid,'rating--invalid')),make('rating',{...rating,id:'invalid'})));
 await assertFails(setDoc(doc(db,learningPath(uid,'rating--invalid')),make('rating',{...rating,id:'invalid'})));
});
