import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {initializeTestEnvironment,assertSucceeds,assertFails} from '@firebase/rules-unit-testing';
import {doc,setDoc,getDoc,getDocs,collection,deleteDoc,serverTimestamp,writeBatch,query,orderBy,limit,startAfter} from 'firebase/firestore';
import {createAttempt,selectAnswer,gradeAttempt,finalizeAttempt,openHint} from '../src/domain/study.js';

let env;
const q=JSON.parse(readFileSync(new URL('../data/qualifications/ap/packs/r07h.b3e22c032f801e9e.json',import.meta.url)))[0];
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
