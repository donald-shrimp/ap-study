import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createSyncEngine} from '../src/sync/engine.js';

function local(items=[]){
 let cursor=null;const pending=new Map(items.map(i=>[i.id,i])),records=new Map();
 return {records,pending:async()=>[...pending.values()],cursor:async()=>cursor,
  mergeRemote:async(rows,next)=>{for(const row of rows)records.set(row.id,row.payload);cursor=next;return rows.map(r=>r.payload);},
  acknowledge:async(id,revision)=>{if(pending.get(id)?.revision===revision)pending.delete(id);},
  forkPending:async()=>{throw new Error('unexpected fork');}};
}
const item={id:'attempt-one',owner:'uid:alice',qualificationId:'ap',revision:2,operationId:'attempt-one:2',deviceId:'device-one',payload:{id:'attempt-one'}};
const create=(store,remote,options={})=>createSyncEngine({uid:'alice',qualificationId:'ap',store,remote,isOnline:()=>true,validateAttempt:()=>{},...options});
test('送信済み直後の通信失敗でも同じ操作IDで再送する',async()=>{
 const store=local([item]),sent=new Map();let fail=true;
 const engine=create(store,{pull:async()=>({rows:[],cursor:null,more:false}),push:async(uid,q,i)=>{sent.set(i.operationId,i);if(fail){fail=false;throw new Error('lost response');}return 'ack';}});
 await engine.run();assert.equal((await store.pending()).length,1);await engine.run();assert.equal((await store.pending()).length,0);assert.equal(sent.size,1);await engine.stop();
});
test('ページ分割と同時刻の文書ID境界を引き継ぎ、取込失敗時はカーソルを進めない',async()=>{
 const rows=Array.from({length:205},(_,i)=>({id:String(i).padStart(3,'0'),version:1,revision:1,deviceId:'device-two',payload:{id:String(i).padStart(3,'0')}})),store=local();
 let requests=0;
 const remote={pull:async(uid,q,cursor)=>{requests++;const start=cursor?Number(cursor.id)+1:0,page=rows.slice(start,start+100);return {rows:page,cursor:page.length?{seconds:7,nanoseconds:0,id:page.at(-1).id}:cursor,more:page.length===100};},push:async()=>{throw new Error('download echoed to cloud');}};
 const engine=create(store,remote);await engine.run();assert.equal(store.records.size,205);assert.equal((await store.cursor()).id,'204');assert.equal(requests,3);await engine.stop();
 const failed=local();let refuse=true;const merge=failed.mergeRemote;failed.mergeRemote=async(...args)=>{if(refuse){refuse=false;throw new Error('IDB full');}return merge(...args);};
 const retry=create(failed,remote);await retry.run();assert.equal(await failed.cursor(),null);await retry.run();assert.equal(failed.records.size,205);await retry.stop();
});
test('取得データが不正なら保存もカーソル更新もしない',async()=>{
 const store=local(),engine=create(store,{pull:async()=>({rows:[{id:'a',version:1,revision:1,deviceId:'device',payload:{id:'wrong'}}],cursor:{id:'a'},more:false})});
 await engine.run();assert.equal(await store.cursor(),null);assert.equal(store.records.size,0);await engine.stop();
});
test('未送信のため保留した取得行を、ACK後に再取得してからカーソルを進める',async()=>{
 const store=local([item]),merge=store.mergeRemote;let pulled=0;
 const row={id:item.id,version:1,revision:3,deviceId:item.deviceId,payload:{id:item.id,hintCount:2}};
 store.mergeRemote=async(rows,cursor)=>{const ids=new Set((await store.pending()).map(i=>i.id));return merge(rows.filter(r=>!ids.has(r.id)),cursor);};
 const engine=create(store,{pull:async()=>{pulled++;return {rows:[row],cursor:{seconds:3,id:item.id},more:false};},push:async()=>{assert.equal(await store.cursor(),null);return 'ack';}});
 await engine.run();assert.equal(pulled,2);assert.equal(store.records.get(item.id).hintCount,2);assert.equal((await store.cursor()).id,item.id);await engine.stop();
});
test('ログアウト中の遅い応答をACKせず、別UIDの送信待ちを送らない',async()=>{
 const store=local([item]);let finish,started;const ready=new Promise(resolve=>started=resolve);
 const engine=create(store,{pull:async()=>({rows:[],cursor:null,more:false}),push:async()=>{started();return new Promise(resolve=>finish=resolve);}});
 const run=engine.run();await ready;await engine.stop();finish('ack');await run;assert.equal((await store.pending()).length,1);
 let sent=false;const wrong=create(local([{...item,owner:'uid:bob'}]),{pull:async()=>({rows:[],cursor:null,more:false}),push:async()=>{sent=true;}});await wrong.run();assert.equal(sent,false);await wrong.stop();
});
test('大きすぎる記録は端末に残し、通信しない',async()=>{
 const store=local([{...item,blocked:true}]);let sent=false,status;
 const engine=create(store,{pull:async()=>({rows:[],cursor:null,more:false}),push:async()=>{sent=true;}},{onStatus:value=>status=value});await engine.run();assert.equal(status,'blocked');assert.equal(sent,false);assert.equal((await store.pending()).length,1);await engine.stop();
});
