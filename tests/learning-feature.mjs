import test from 'node:test';
import assert from 'node:assert/strict';
import {createLearningFeature} from '../src/features/learning.js';
import {makeState} from '../src/domain/study.js';
test('late metadata receive cannot cross an account binding boundary',async()=>{
 const previousDocument=globalThis.document;globalThis.document={getElementById:()=>null};
 try{
  let state=makeState(),hold=false,release,updates=0;
  const first={read:async()=>[],identity:async()=>{if(hold)await new Promise(resolve=>release=resolve);return {owner:'uid:first'};}};
  const second={read:async()=>[],identity:async()=>({owner:'uid:second'})};let storage=first;
  const feature=createLearningFeature({qualification:{id:'ap',topics:[],examParts:[]},getStore:()=>({learningStore:()=>storage}),getState:()=>state,onUpdate:()=>updates++,onNotice:()=>{}});
  await feature.bind();hold=true;
  const pending=feature.onRows([{id:'desk--q',kind:'desk',owner:'uid:first',payload:{questionId:'q',value:true}}]);
  storage=second;state=makeState();await feature.bind();release();await pending;
  assert.deepEqual(state.settings.deskQuestionIds,[]);assert.equal(updates,0);assert.deepEqual(feature.backup().documents,[]);
 }finally{globalThis.document=previousDocument;}
});
