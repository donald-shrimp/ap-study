import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeSync,qualificationSyncLabels} from '../src/domain/sync-status.js';
import {hasGuestImport} from '../src/domain/guest-import.js';
import {makeState} from '../src/domain/study.js';

test('一部失敗・未送信・不明な系統があれば全体を同期済みと表示しない',()=>{
 const states=Object.fromEntries(['study','planning','learning','cards','personal'].map(k=>[k,{kind:'synced'}]));
 assert.equal(summarizeSync(states,true).kind,'synced');
 for(const scope of Object.keys(states))for(const kind of ['pending','syncing','offline','error','conflict','rules','mock-rules','history-rules','extended-rules','blocked','unknown']){
  const actual=summarizeSync({...states,[scope]:{kind}},true);
  assert.notEqual(actual.kind,'synced',scope+':'+kind);
  if(['error','rules','blocked'].includes(kind))assert.equal(actual.details[0].scope,scope);
 }
 assert.notEqual(summarizeSync({},true).kind,'synced');
 assert.equal(summarizeSync(states,false).kind,'guest');
 assert.equal(summarizeSync({...states,local:{kind:'error'}},true).kind,'error');
 assert.ok(summarizeSync({...states,local:{kind:'error'}},false).text.includes('保存できません'));
});

test('通常記録がなくても、取り込める単語帳・メモ・計画・紙ペン指定を検出する',()=>{
 const input=()=>({guest:makeState(),current:makeState(),prefix:'device:'});
 assert.equal(hasGuestImport(input()),false);
 assert.equal(hasGuestImport({...input(),guestCards:[{id:'rating'}]}),true);
 assert.equal(hasGuestImport({...input(),guestWorkspace:[{id:'planning'}]}),true);
 const note=input();note.guest.readingNotes.db='第1章';assert.equal(hasGuestImport(note),true);
 const desk=input();desk.guest.settings.deskQuestionIds=['q1'];assert.equal(hasGuestImport(desk),true);
 const record=input();record.guest.attempts=[{id:'first'}];assert.equal(hasGuestImport(record),true);
 record.current.attempts=[{importedFrom:'device:first'}];assert.equal(hasGuestImport(record),false);
});

test('取り込み済みの内容や、アカウントで削除したカードを再度の取り込み候補にしない',()=>{
 const guest=makeState(),current=makeState();guest.attempts=[{id:'first'}];current.attempts=[{importedFrom:'device:first'}];guest.readingNotes.db='昔のメモ';guest.settings.deskQuestionIds=['q1'];
 const data={guest,current,prefix:'device:',guestCards:[{id:'rating'}],cardRows:[{kind:'rating',payload:{id:'rating'}},{kind:'reset',payload:{eventIds:['rating']}}],guestWorkspace:[{id:'planning'}],workspaceRows:[{id:'planning'}],personalRows:[{kind:'note',payload:{topicId:'db',text:''}}],learningRows:[{id:'desk--q1'}]};
 assert.equal(hasGuestImport(data),false);
 assert.equal(hasGuestImport({...data,guestWorkspace:[{id:'new-diagnosis'}]}),true);
});

 test('同期対象名は公開されている資格の科目を使い、共通状態表示を保つ',()=>{
 const ap={examParts:[{label:'科目B',unit:'cases',practiceAvailable:true}]},fp={examParts:[{label:'実技（日本FP協会）',unit:'cases',practiceAvailable:true},{label:'未公開実技',unit:'cases',practiceAvailable:false}]};
 assert.deepEqual(qualificationSyncLabels(ap),{written:'科目B'});assert.deepEqual(qualificationSyncLabels(fp),{written:'実技（日本FP協会）'});assert.deepEqual(qualificationSyncLabels({examParts:[]}),{});
 for(const kind of ['error','conflict'])assert.equal(summarizeSync({written:{kind}},true,qualificationSyncLabels(fp)).details[0].label,'実技（日本FP協会）');
 assert.equal(summarizeSync({planning:{kind:'mock-rules'}},true,{planning:'計画'}).details[0].label,'模試');
 assert.equal(summarizeSync({written:{kind:'synced'}},true,qualificationSyncLabels(fp)).text,'同期済み');
 });
