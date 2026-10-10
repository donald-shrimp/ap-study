import {validateLearning,learningId,contextPayload} from '../domain/learning-state.js';
import {makeState, complete} from '../domain/study.js';

const request = operation => new Promise((resolve,reject)=>{
 operation.onsuccess=()=>resolve(operation.result);operation.onerror=()=>reject(operation.error);
});
const finished = tx => new Promise((resolve,reject)=>{
 tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error||new Error('保存を中止しました。'));tx.onerror=()=>{};
});
const serial = value => JSON.stringify(value);
const sharedFields = ['settings','readingNotes','overrides'];
const checkpoint = state => ({version:state.version,currentId:state.currentId,currentRunId:state.currentRunId||null,view:state.view,session:state.session});
const shared = state => Object.fromEntries(sharedFields.map(k=>[k,state[k]]));
const transport = a => {const {scrollY,readingNote,entryMode,practiceScope,deferred,...payload}=a;return JSON.parse(JSON.stringify(payload));};
const changedResult = (before,after) => ['status','selected','selectedChoiceId','confidence','completedAt','hintsBeforeAnswer','answerViewedBefore','questionSnapshot','materialSnapshot'].some(k=>serial(before[k])!==serial(after[k]));

// Records and their durable outgoing item commit together. Navigation, scroll,
// display settings and personal material stay local. Mutable learning metadata
// uses its own outbox in meta. A guest queue never targets a UID.
export function createLocalStore({qualificationId,rootPath='/',key,validate,owner:requestedOwner}={}) {
 if(!qualificationId)throw new Error('保存する資格が指定されていません。');
 const databaseName=`hitomon:${rootPath}:records`;
 let dbPromise,queue=Promise.resolve(),owner,deviceId,baseline=new Map(),baselineShared=shared(makeState()),remaps=new Map(),closed=false,seenGeneration=0;
 let tabId;
 try {const name=`hitomon:${rootPath}:tab`;tabId=sessionStorage.getItem(name)||crypto.randomUUID();sessionStorage.setItem(name,tabId);}catch{tabId=crypto.randomUUID();}
 async function database(){
  if(closed)throw new Error('保存先は閉じています。');
  if(!dbPromise)dbPromise=new Promise((resolve,reject)=>{
   const opening=indexedDB.open(databaseName,1);
   opening.onupgradeneeded=()=>{const db=opening.result;db.createObjectStore('meta',{keyPath:'key'});for(const name of ['attempts','outbox']){const store=db.createObjectStore(name,{keyPath:['owner','qualificationId','id']});store.createIndex('namespace',['owner','qualificationId']);}};
   opening.onerror=()=>reject(opening.error);opening.onblocked=()=>reject(new Error('保存先を開けません。別タブを閉じて再読み込みしてください。'));
   opening.onsuccess=()=>{opening.result.onversionchange=()=>opening.result.close();resolve(opening.result);};
  });
  const db=await dbPromise;
  if(!deviceId){
   const tx=db.transaction('meta','readwrite'),done=finished(tx),meta=tx.objectStore('meta');let value=await request(meta.get('device'));
   if(!value){value={key:'device',id:crypto.randomUUID()};meta.put(value);}deviceId=value.id;owner=requestedOwner||`guest:${deviceId}`;await done;
  }
  return db;
 }
 const scope=()=>[owner,qualificationId];
 const sharedKey=()=>`${owner}|${qualificationId}|shared`;
 const tabKey=()=>`${owner}|${qualificationId}|tab:${tabId}`;
 async function snapshot({remember=false}={}) {
  const db=await database(),tx=db.transaction(['meta','attempts'],'readonly'),done=finished(tx),meta=tx.objectStore('meta');
  const [common,local,rows]=await Promise.all([request(meta.get(sharedKey())),request(meta.get(tabKey())),request(tx.objectStore('attempts').index('namespace').getAll(scope()))]);await done;
  if(!common)return null;
  const state={...makeState(),...common.data,...(local?.data||common.checkpoint),attempts:rows.map(r=>r.data).sort((a,b)=>a.startedAt.localeCompare(b.startedAt)||a.id.localeCompare(b.id))};
  const ids=new Set(state.attempts.map(a=>a.id));if(!ids.has(state.currentId)){state.currentId=null;if(state.view==='study')state.view='home';}state.session.attemptIds=state.session.attemptIds.filter(id=>ids.has(id));
  if(remember){baseline=new Map(rows.map(r=>[r.id,{data:serial(r.data),revision:r.revision}]));baselineShared=structuredClone(shared(state));seenGeneration=common.generation;}
  return serial(state);
 }
 async function commit(input,{replace=false,ifAbsent=false,learningOperations=[]}={}){
  const db=await database(),state=structuredClone(input);
  if(!replace){
   const present=new Set(state.attempts.map(a=>a.id)),queuedRemaps=new Map([...remaps].filter(([,after])=>!present.has(after)));
   for(const a of state.attempts)if(queuedRemaps.has(a.id)){const original=a.id;a.id=queuedRemaps.get(a.id);a.continuationOf=original;a.continuedAt=JSON.parse(baseline.get(a.id).data).continuedAt;}
   if(queuedRemaps.has(state.currentId))state.currentId=queuedRemaps.get(state.currentId);state.session.attemptIds=state.session.attemptIds.map(id=>queuedRemaps.get(id)||id);
  }
  const tx=db.transaction(['meta','attempts','outbox'],'readwrite'),done=finished(tx),meta=tx.objectStore('meta'),attempts=tx.objectStore('attempts'),outbox=tx.objectStore('outbox');
  try {
   const [common,rows]=await Promise.all([request(meta.get(sharedKey())),request(attempts.index('namespace').getAll(scope()))]);
   if(ifAbsent&&common){await done;return {attempts:[],remap:{}};}
   if(common&&seenGeneration&&common.generation!==seenGeneration&&!replace)throw new Error('別タブで記録が初期化・読み込みされています。書き出して保管後、再読み込みしてください。');
   const existing=new Map(rows.map(r=>[r.id,r])),mapping={},nextBaseline=replace?new Map():new Map(baseline);
   if(replace){for(const r of rows){attempts.delete([owner,qualificationId,r.id]);outbox.delete([owner,qualificationId,r.id]);}existing.clear();}
   for(const a of state.attempts){
    if(a.qualificationId!==undefined&&a.qualificationId!==qualificationId)throw new Error('資格が異なる学習記録を保存できません。');
    const previous=baseline.get(a.id),dbRow=existing.get(a.id),value=serial(a);
    if(!replace&&previous?.data===value)continue;
    if(!replace&&dbRow&&serial(dbRow.data)===value){nextBaseline.set(a.id,{data:value,revision:dbRow.revision});continue;}
    // A stale metadata projection must preserve a newer downloaded answer.
    if(!replace&&dbRow&&previous&&serial(transport(a))===serial(transport(JSON.parse(previous.data)))&&serial(transport(a))!==serial(transport(dbRow.data))){
     const local=Object.fromEntries(['scrollY','readingNote','entryMode','practiceScope','deferred'].filter(k=>Object.hasOwn(a,k)).map(k=>[k,a[k]]));Object.assign(a,dbRow.data,local);
    }
    const conflict=!replace&&dbRow&&previous&&dbRow.revision!==previous.revision&&serial(transport(dbRow.data))!==serial(transport(JSON.parse(previous.data)))&&serial(transport(dbRow.data))!==serial(transport(a));
    const finalizedTogether=conflict&&complete(dbRow.data)&&complete(a)&&!changedResult(dbRow.data,a);
    if(finalizedTogether&&dbRow.data.hintCount>a.hintCount)Object.assign(a,dbRow.data);
    if(!replace&&dbRow&&complete(dbRow.data)&&complete(a)&&changedResult(dbRow.data,a)&&(!conflict||complete(JSON.parse(previous.data))))throw new Error('確定した回答を上書きできません。記録を書き出して保管してください。');
    // A checkpoint edited concurrently becomes a separate continuation.
    if(conflict&&!finalizedTogether){
     const original=a.id;a.id=crypto.randomUUID();a.continuationOf=original;a.continuedAt=new Date().toISOString();mapping[original]=a.id;
     if(state.currentId===original)state.currentId=a.id;state.session.attemptIds=state.session.attemptIds.map(id=>id===original?a.id:id);
    }
    const old=existing.get(a.id),metadataOnly=old&&serial(transport(old.data))===serial(transport(a)),revision=metadataOnly?old.revision:(old?.revision||0)+1;
    const originDevice=metadataOnly||old&&complete(old.data)&&complete(a)&&!changedResult(old.data,a)?old.deviceId:deviceId;
    const row={owner,qualificationId,id:a.id,deviceId:originDevice,revision,data:a};attempts.put(row);existing.set(a.id,row);
    const payload=transport(a),semantic=serial(payload);
    if(replace||!old||serial(transport(old.data))!==semantic){
     const blocked=new TextEncoder().encode(semantic).length>900000;
     outbox.put({owner,qualificationId,id:a.id,deviceId:originDevice,revision,operationId:`${a.id}:${revision}`,payload,blocked});
    }
    nextBaseline.set(a.id,{data:serial(a),revision});
   }
   let nextShared=common?.data||shared(makeState());
   if(replace||!common)nextShared=shared(state);
   else for(const field of sharedFields){
    const next={...nextShared[field]};for(const item of new Set([...Object.keys(baselineShared[field]),...Object.keys(state[field])]))if(serial(baselineShared[field][item])!==serial(state[field][item])){if(Object.hasOwn(state[field],item))next[item]=state[field][item];else delete next[item];}nextShared={...nextShared,[field]:next};
   }
   const learningChanges=[];
   if(replace){const keys=await request(meta.getAllKeys(learningRange()));for(const key of keys)meta.delete(key);}
   for(const [before,after] of Object.entries(mapping))if(!learningOperations.some(op=>op.kind==='context'&&op.payload.attemptId===before)){
    const payload=contextPayload(existing.get(after).data);if(payload)learningChanges.push(await putLearning(meta,{id:learningId('context',payload),kind:'context',payload,expectedLocalRevision:0}));
   }
   for(const original of learningOperations){
    const op=structuredClone(original);if(replace)op.expectedLocalRevision=0;
    if(op.kind==='context'&&mapping[op.payload.attemptId]){op.payload.attemptId=mapping[op.payload.attemptId];op.id=learningId(op.kind,op.payload);op.expectedLocalRevision=0;}
    learningChanges.push(await putLearning(meta,op));
   }
   const generation=(common?.generation||1)+(replace?1:0);
   meta.put({key:sharedKey(),data:nextShared,checkpoint:checkpoint(state),generation});meta.put({key:tabKey(),data:checkpoint(state)});
   await done;seenGeneration=generation;baseline=nextBaseline;if(replace)remaps.clear();for(const [before,after] of Object.entries(mapping))remaps.set(before,after);baselineShared=structuredClone(shared(state));
   return {attempts:[...existing.values()].map(r=>r.data),remap:mapping,learningChanges};
  }catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}
 }
 function write(state,options){
  const copy=structuredClone(state);const operation=queue.catch(()=>{}).then(()=>commit(copy,options));queue=operation;return operation;
 }
 async function read(){
  const raw=await snapshot({remember:true});if(raw!==null)return raw;
  let legacy;try{legacy=key&&localStorage.getItem(key);}catch{}
  if(!legacy||requestedOwner)return null;
  try{const state=validate(JSON.parse(legacy));await write(state,{ifAbsent:true});return await snapshot({remember:true});}catch{return legacy;}
 }
 async function pending(){await queue.catch(()=>{});const db=await database(),tx=db.transaction('outbox'),done=finished(tx);const rows=await request(tx.objectStore('outbox').index('namespace').getAll(scope()));await done;return rows;}
 async function acknowledge(id,revision){const db=await database(),tx=db.transaction('outbox','readwrite'),done=finished(tx),store=tx.objectStore('outbox'),row=await request(store.get([owner,qualificationId,id]));if(row?.revision===revision)store.delete([owner,qualificationId,id]);await done;}
 const cursorKey=()=>`${owner}|${qualificationId}|sync-cursor`;
 async function cursor(){const db=await database(),tx=db.transaction('meta'),done=finished(tx);const value=await request(tx.objectStore('meta').get(cursorKey()));await done;return value?.data||null;}
 async function remoteDevice(id){const db=await database(),tx=db.transaction('attempts'),done=finished(tx);const value=await request(tx.objectStore('attempts').get([owner,qualificationId,id]));await done;return value?.deviceId;}
 function mergeRemote(rows,nextCursor){
  const operation=queue.catch(()=>{}).then(async()=>{
   const db=await database(),tx=db.transaction(['meta','attempts','outbox'],'readwrite'),done=finished(tx),attempts=tx.objectStore('attempts'),outbox=tx.objectStore('outbox'),changed=[];
   try{
    for(const row of rows){
     const key=[owner,qualificationId,row.id];const [existing,pending]=await Promise.all([request(attempts.get(key)),request(outbox.get(key))]);
     // Never overwrite an unsent local answer/checkpoint. The uploader handles
     // foreign-device collisions by giving that local work a new UUID.
     if(pending||existing&&existing.deviceId===row.deviceId&&existing.revision>=row.revision)continue;
     const data={...row.payload,scrollY:existing?.data.scrollY||0,readingNote:existing?.data.readingNote||'',...(existing?.data.entryMode?{entryMode:existing.data.entryMode}:{}),...(existing?.data.practiceScope?{practiceScope:existing.data.practiceScope}:{}),...(existing?.data.deferred!==undefined?{deferred:existing.data.deferred}:{})};
     attempts.put({owner,qualificationId,id:row.id,deviceId:row.deviceId,revision:row.revision,data});changed.push(data);
    }
    if(nextCursor)tx.objectStore('meta').put({key:cursorKey(),data:nextCursor});
    await done;return changed;
   }catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}
  });queue=operation;return operation;
 }
 function forkPending(id,revision){
  const operation=queue.catch(()=>{}).then(async()=>{
   const db=await database(),tx=db.transaction(['meta','attempts','outbox'],'readwrite'),done=finished(tx),attempts=tx.objectStore('attempts'),outbox=tx.objectStore('outbox'),key=[owner,qualificationId,id];
   try{
    const [row,item]=await Promise.all([request(attempts.get(key)),request(outbox.get(key))]);if(!row||item?.revision!==revision){await done;return null;}
    const newId=crypto.randomUUID(),data={...row.data,id:newId,continuationOf:id,continuedAt:new Date().toISOString()};
    // Keep the original until the next remote page supplies its authoritative
    // version, but stop trying to publish this device's copy under its ID.
    outbox.delete(key);attempts.put({...row,id:newId,deviceId,revision:1,data});
    const context=contextPayload(data);if(context)await putLearning(tx.objectStore('meta'),{id:learningId('context',context),kind:'context',payload:context,expectedLocalRevision:0});
    outbox.put({...item,id:newId,deviceId,revision:1,operationId:`${newId}:1`,payload:transport(data)});
    const local=await request(tx.objectStore('meta').get(tabKey()));if(local){if(local.data.currentId===id)local.data.currentId=newId;local.data.session.attemptIds=local.data.session.attemptIds.map(x=>x===id?newId:x);tx.objectStore('meta').put(local);}
    await done;baseline.set(newId,{data:serial(data),revision:1});remaps.set(id,newId);return {before:id,after:newId,data};
   }catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}
  });queue=operation;return operation;
 }

 const learningPrefix=()=>`${owner}|${qualificationId}|learning:`;
 const learningKey=id=>learningPrefix()+id;
 const learningRange=()=>IDBKeyRange.bound(learningPrefix(),learningPrefix()+'\uffff');
 async function putLearning(meta,op){
  const payload=validateLearning(op.kind,op.payload);if(op.id!==learningId(op.kind,payload))throw new Error('学習設定のIDが一致しません。');
  const old=(await request(meta.get(learningKey(op.id))))?.row;
  if(old?.kind===op.kind&&serial(old.payload)===serial(payload))return old;
  if((old?.localRevision||0)!==op.expectedLocalRevision)throw new Error('別タブで学習設定が変更されました。開き直してもう一度指定してください。');
  const localRevision=(old?.localRevision||0)+1;
  const row={owner,qualificationId,id:op.id,kind:op.kind,payload,localRevision,remoteRevision:old?.remoteRevision||0,deviceId,operationId:`${deviceId}:${op.id}:${localRevision}`,dirty:true,ancestors:[...(old?.ancestors||[]),...(old?.operationId?[old.operationId]:[])].slice(-100)};
  meta.put({key:learningKey(row.id),row});return row;
 }
 function learningTransaction(callback){
  const operation=queue.catch(()=>{}).then(async()=>{const db=await database(),tx=db.transaction('meta','readwrite'),done=finished(tx);
   try{const result=await callback(tx.objectStore('meta'));await done;return result;}catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}
  });queue=operation;return operation;
 }
 function learningStore(){return {
  identity:async()=>{await database();return {owner,deviceId,qualificationId};},
  read:async()=>{await queue.catch(()=>{});const db=await database(),tx=db.transaction('meta'),done=finished(tx),values=await request(tx.objectStore('meta').getAll(learningRange()));await done;return values.map(v=>v.row);},
  merge:remote=>learningTransaction(async meta=>{
   if(remote.version!==1||!Number.isInteger(remote.revision)||remote.revision<1||typeof remote.deviceId!=='string'||typeof remote.operationId!=='string'||remote.id!==learningId(remote.kind,remote.payload))throw new Error('学習設定の同期形式を確認できません。');
   const payload=validateLearning(remote.kind,remote.payload),old=(await request(meta.get(learningKey(remote.id))))?.row;
   if(old&&remote.revision<=old.remoteRevision)return old;
   if(old?.dirty&&remote.deviceId===deviceId&&old.ancestors.includes(remote.operationId)){const row={...old,remoteRevision:remote.revision};meta.put({key:learningKey(remote.id),row});return row;}
   const discarded=Boolean(old?.dirty&&old.operationId!==remote.operationId&&serial(old.payload)!==serial(payload));
   const row={owner,qualificationId,id:remote.id,kind:remote.kind,payload,localRevision:(old?.localRevision||0)+1,remoteRevision:remote.revision,deviceId:remote.deviceId,operationId:remote.operationId,dirty:false,ancestors:[],discarded};meta.put({key:learningKey(remote.id),row});return row;
  }),
  acknowledge:(id,operationId,remote)=>learningTransaction(async meta=>{const old=(await request(meta.get(learningKey(id))))?.row;if(!old)return;const row={...old,remoteRevision:remote.revision};if(old.operationId===operationId)row.dirty=false;meta.put({key:learningKey(id),row});return row;}),
 };}
 return {learningStore,read,snapshot,write,flush:()=>queue,pending,acknowledge,cursor,mergeRemote,forkPending,remoteDevice,identity:async()=>{await database();return {owner,deviceId,qualificationId};},close:async()=>{await queue.catch(()=>{});if(dbPromise)(await dbPromise).close();closed=true;},databaseName};
}
