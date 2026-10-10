import {validateCardEvents} from '../domain/flashcards.js';
import {cardDocumentId,sameCardPayload,validateCardDocument,visibleCardEvents} from '../domain/card-sync.js';
const request=r=>new Promise((resolve,reject)=>{r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
const done=tx=>new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error||new Error('単語帳を保存できません。'));tx.onerror=()=>{};});
const chunks=items=>Array.from({length:Math.ceil(items.length/200)},(_,i)=>items.slice(i*200,i*200+200));
export function createCardStore({rootPath,owner,qualificationId,deviceId}){
 const scope=[owner,qualificationId];let connection,queue=Promise.resolve(),localDevice=deviceId;
 async function db(){if(!connection)connection=new Promise((resolve,reject)=>{const r=indexedDB.open(`hitomon:${rootPath}:cards`,1);r.onupgradeneeded=()=>{const events=r.result.createObjectStore('events',{keyPath:['owner','qualificationId','id']});events.createIndex('namespace',['owner','qualificationId']);r.result.createObjectStore('checkpoints',{keyPath:['owner','qualificationId']});};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});return connection;}
 function operation(fn){const op=queue.then(async()=>{const database=await db(),tx=database.transaction(['events','checkpoints'],'readwrite'),finished=done(tx),store=tx.objectStore('events'),cps=tx.objectStore('checkpoints');try{
   const [raw,oldCheckpoint]=await Promise.all([request(store.index('namespace').getAll(scope)),request(cps.get(scope))]);
   const checkpoint=oldCheckpoint||{owner,qualificationId,value:null};localDevice||=checkpoint.sync?.deviceId||crypto.randomUUID();checkpoint.sync={...checkpoint.sync,deviceId:localDevice};
   const rows=new Map(raw.filter(row=>row.kind).map(row=>[row.id,row]));
   const make=(kind,payload)=>({owner,qualificationId,id:cardDocumentId(kind,payload.id),kind,payload:structuredClone(payload),deviceId:localDevice,operationId:cardDocumentId(kind,payload.id),dirty:true,remoteRevision:0,localRevision:1});
   // Preserve pre-sync events in the same transaction as their durable outbox.
   for(const old of raw.filter(row=>!row.kind)){const {owner,qualificationId,...payload}=old;validateCardEvents([payload]);const row=make('rating',payload),existing=rows.get(row.id);if(existing&&!sameCardPayload(existing.payload,payload))throw new Error('同じIDの異なる記録があります。');store.delete([...scope,old.id]);if(!existing){rows.set(row.id,row);store.put(row);}}
   for(const row of rows.values())validateCardDocument(row);
   const put=row=>{rows.set(row.id,row);store.put(row);};
   const result=await fn({rows,checkpoint,put,make});cps.put(checkpoint);await finished;return result;
  }catch(error){try{tx.abort();}catch{}await finished.catch(()=>{});throw error;}});queue=op.catch(()=>{});return op;}
 const read=()=>operation(({rows,checkpoint})=>({events:visibleCardEvents([...rows.values()]),checkpoint:checkpoint.value||null}));
 function write(checkpoint,event=null){if(event)validateCardEvents([event]);return operation(({rows,checkpoint:cp,put,make})=>{if(event){const row=make('rating',event),old=rows.get(row.id);if(old&&!sameCardPayload(old.payload,event))throw new Error('同じIDの異なる記録があります。');if(!old)put(row);visibleCardEvents([...rows.values()]);}cp.value=checkpoint;});}
 function importEvents(events,{restoreDeleted=true}={}){validateCardEvents(events);return operation(({rows,put,make})=>{
  for(const event of events){const row=make('rating',event),old=rows.get(row.id);if(old&&!sameCardPayload(old.payload,event))throw new Error('同じIDの異なる記録があります。現在の記録は変更していません。');if(!old)put(row);}
  if(restoreDeleted){const visible=new Set(visibleCardEvents([...rows.values()]).map(e=>e.id)),hidden=events.filter(e=>!visible.has(e.id)).map(e=>e.id);
   for(const eventIds of chunks(hidden)){const wanted=new Set(eventIds),resetIds=[...rows.values()].filter(r=>r.kind==='reset'&&r.payload.eventIds.some(id=>wanted.has(id))).map(r=>r.payload.id);for(const ids of chunks(resetIds))put(make('restore',{id:crypto.randomUUID(),eventIds,resetIds:ids}));}}
  visibleCardEvents([...rows.values()]);
 });}
 const clear=()=>operation(({rows,checkpoint,put,make})=>{for(const eventIds of chunks(visibleCardEvents([...rows.values()]).map(e=>e.id)))put(make('reset',{id:crypto.randomUUID(),eventIds}));checkpoint.value=null;});
 function accept(remote,{rows,put}){
  validateCardDocument(remote);if(remote.version!==1||remote.revision!==1||remote.operationId!==remote.id||typeof remote.deviceId!=='string'||!remote.deviceId.length||remote.deviceId.length>100)throw new Error('単語帳の同期形式が正しくありません。');
  const old=rows.get(remote.id);if(old&&(old.kind!==remote.kind||!sameCardPayload(old.payload,remote.payload)))throw new Error('同じIDの異なる単語帳記録があります。');
  put({owner,qualificationId,id:remote.id,kind:remote.kind,payload:structuredClone(remote.payload),deviceId:remote.deviceId,operationId:remote.id,dirty:false,remoteRevision:1,localRevision:1});
 }
 const sync={identity:async()=>{await read();return {owner,qualificationId,deviceId:localDevice};},read:()=>operation(({rows})=>[...rows.values()]),merge:remote=>operation(ctx=>accept(remote,ctx)),acknowledge:(id,operationId,remote)=>operation(ctx=>{if(id!==operationId||id!==remote?.id)throw new Error('単語帳の同期応答が一致しません。');accept(remote,ctx);}),cursor:()=>operation(({checkpoint})=>checkpoint.sync.cursor||null),setCursor:cursor=>operation(({checkpoint})=>{checkpoint.sync.cursor=cursor;})};
 return {read,write,importEvents,clear,syncStore:()=>sync,close:async()=>{await queue;if(connection)(await connection).close();}};
}
