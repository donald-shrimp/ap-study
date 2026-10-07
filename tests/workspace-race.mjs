import test from 'node:test';
import assert from 'node:assert/strict';
import {recoverResourceWrite} from '../src/sync/firebase.js';

const permission=Object.assign(new Error('denied'),{code:'permission-denied'});
const item={id:'planning',operationId:'device:planning:7',remoteRevision:4};
test('CASが先に更新された権限エラーは、最新文書との競合として返す',async()=>{
 const fresh={id:'planning',operationId:'other:planning:9',revision:5,payload:{context:{rationale:'別端末の前提'}}};let reads=0;
 const result=await recoverResourceWrite(permission,item,async()=>{reads++;return fresh;},()=>{});
 assert.equal(reads,1);assert.equal(result.conflict,true);assert.deepEqual(result.remote,fresh);assert.equal(result.remote.payload.context.rationale,'別端末の前提');
});
test('同じ操作の保存が済んでいれば再送せずACKし、本当のルール不足は保持する',async()=>{
 const fresh={operationId:item.operationId,revision:5};assert.deepEqual(await recoverResourceWrite(permission,item,async()=>fresh,()=>{}),{remote:fresh});
 for(const record of [null,{operationId:'other',revision:4},{operationId:'other',revision:3}])await assert.rejects(()=>recoverResourceWrite(permission,item,async()=>record,()=>{}),e=>e===permission);
 await assert.rejects(()=>recoverResourceWrite(permission,item,async()=>{throw new Error('read denied');},()=>{}),e=>e===permission);
});
test('通信エラーでは追加読取せず、読み直し中にUIDが変わってもACKしない',async()=>{
 const network=Object.assign(new Error('offline'),{code:'unavailable'});let reads=0;
 await assert.rejects(()=>recoverResourceWrite(network,item,async()=>{reads++;return null;},()=>{}),e=>e===network);assert.equal(reads,0);
 let sameOwner=true;const ownershipError=new Error('owner changed');await assert.rejects(()=>recoverResourceWrite(permission,item,async()=>{sameOwner=false;return {operationId:item.operationId,revision:5};},()=>{if(!sameOwner)throw ownershipError;}),e=>e===ownershipError);
});
