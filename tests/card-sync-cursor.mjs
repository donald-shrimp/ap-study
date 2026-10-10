import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createWorkspaceSync} from '../src/sync/workspace.js';
Object.defineProperty(globalThis,'navigator',{configurable:true,value:{onLine:true}});
test('保存済みカーソルから取得し、全行の保存が済んでからカーソルを進める',async()=>{
 let cursor={id:'saved'},count=0,saved=0;const store={cursor:async()=>cursor,setCursor:async next=>{assert.equal(count,2);saved++;cursor=next;},merge:async()=>{count++;},read:async()=>[]};
 const remote={pullDocuments:async(uid,q,c)=>{assert.deepEqual(c,{id:'saved'});return {rows:[{id:'a'},{id:'b'}],cursor:{id:'b'},more:false};}};
 const engine=createWorkspaceSync({uid:'u',qualificationId:'ap',store,remote});await engine.run();engine.stop();assert.equal(saved,1);assert.deepEqual(cursor,{id:'b'});
});
test('途中の保存が失敗しても取得位置を進めず、再実行でページをやり直す',async()=>{
 let cursor=null,fail=true,calls=0,merges=0;const store={cursor:async()=>cursor,setCursor:async next=>{cursor=next;},merge:async row=>{merges++;if(row.id==='b'&&fail){fail=false;throw Error('storage');}},read:async()=>[]};
 const remote={pullDocuments:async(uid,q,c)=>{calls++;assert.equal(c,null);return {rows:[{id:'a'},{id:'b'}],cursor:{id:'b'},more:false};}};
 const engine=createWorkspaceSync({uid:'u',qualificationId:'ap',store,remote});await engine.run();assert.equal(cursor,null);await engine.run();engine.stop();assert.equal(calls,2);assert.equal(merges,4);assert.deepEqual(cursor,{id:'b'});
});
