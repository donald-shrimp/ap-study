// Mutable plans and diagnostic runs use compare-and-swap, independently of
// immutable learning attempts. The outbox and local document commit together.
const request=r=>new Promise((resolve,reject)=>{r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
const finished=tx=>new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error||new Error('保存を中止しました。'));tx.onerror=()=>{};});
const serial=JSON.stringify;
export function createWorkspaceStore({owner,qualificationId,deviceId,rootPath,validate}){
 let dbPromise,queue=Promise.resolve(),validationError=null;
 const namespace=[owner,qualificationId],key=id=>[...namespace,id];
 async function db(){if(!dbPromise)dbPromise=new Promise((resolve,reject)=>{const r=indexedDB.open(`hitomon:${rootPath}:workspace`,1);r.onupgradeneeded=()=>{const store=r.result.createObjectStore('documents',{keyPath:['owner','qualificationId','id']});store.createIndex('namespace',['owner','qualificationId']);};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});return dbPromise;}
 async function read(){const database=await db(),tx=database.transaction('documents'),done=finished(tx),rows=await request(tx.objectStore('documents').index('namespace').getAll(namespace));await done;validationError=null;return rows.filter(row=>{try{validate(row.kind,row.payload);return true;}catch(error){validationError=error;return false;}});}
 function transaction(callback){const op=queue.catch(()=>{}).then(async()=>{const database=await db(),tx=database.transaction('documents','readwrite'),done=finished(tx);try{const result=await callback(tx.objectStore('documents'));await done;return result;}catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}});queue=op;return op;}
 function write(kind,id,payload,expectedLocalRevision){
  payload=JSON.parse(serial(validate(kind,payload)));if(new TextEncoder().encode(serial(payload)).length>850000)throw new Error('記録が大きすぎます。850KB以内にしてください。');
  return transaction(async store=>{const old=await request(store.get(key(id)));if(expectedLocalRevision!==undefined&&(old?.localRevision||0)!==expectedLocalRevision)throw new Error('別タブで更新されました。画面を開き直してから編集してください。');
   if(old?.conflict)throw new Error('別端末の変更と競合しています。先にどちらの内容を使うか選んでください。');
   if(kind==='diagnostic'&&old){
    if(old.payload.status!=='in_progress'&&serial(old.payload)!==serial(payload))throw new Error('終了した診断は変更できません。');
    if(serial(old.payload.slots)!==serial(payload.slots)||Object.entries(old.payload.responses).some(([id,value])=>!Object.hasOwn(payload.responses,id)||payload.responses[id]!==value))throw new Error('診断の問題と確定した回答は変更できません。');
   }
   const localRevision=(old?.localRevision||0)+1,operationId=`${deviceId}:${id}:${localRevision}`;
   const row={owner,qualificationId,id,kind,payload,localRevision,remoteRevision:old?.remoteRevision||0,deviceId,operationId,dirty:true,ancestors:[...(old?.ancestors||[]),...(old?.operationId?[old.operationId]:[])].slice(-100)};
   store.put(row);return row;
  });
 }
 function merge(remote){
  if(remote.version!==1||!Number.isInteger(remote.revision)||remote.revision<1||typeof remote.deviceId!=='string'||typeof remote.operationId!=='string'||remote.kind==='planning'&&remote.id!=='planning'||remote.kind==='diagnostic'&&remote.id!==remote.payload?.id)throw new Error('同期データの形式を確認できません。');
  const payload=validate(remote.kind,remote.payload);
  return transaction(async store=>{const old=await request(store.get(key(remote.id)));
   if(old?.dirty){
    if(old.operationId===remote.operationId||serial(old.payload)===serial(payload)){const row={...old,payload,remoteRevision:remote.revision,dirty:false,conflict:null};store.put(row);return row;}
    if(remote.deviceId===deviceId&&old.ancestors.includes(remote.operationId)){const row={...old,remoteRevision:remote.revision};store.put(row);return row;}
    if(remote.revision>old.remoteRevision){const row={...old,conflict:remote};store.put(row);return row;}
    return old;
   }
   if(old&&remote.revision<=old.remoteRevision)return old;
   const row={owner,qualificationId,id:remote.id,kind:remote.kind,payload,localRevision:(old?.localRevision||0)+1,remoteRevision:remote.revision,deviceId:remote.deviceId,operationId:remote.operationId,dirty:false,ancestors:[],conflict:null};store.put(row);return row;
  });
 }
 function acknowledge(id,operationId,remote){return transaction(async store=>{const old=await request(store.get(key(id)));if(!old)return;
  const row={...old,remoteRevision:remote.revision};if(old.operationId===operationId){row.dirty=false;row.conflict=null;}store.put(row);return row;
 });}
 function resolve(id,useLocal){return transaction(async store=>{const old=await request(store.get(key(id)));if(!old?.conflict)return old;
  if(useLocal&&old.kind==='diagnostic')throw new Error('診断の確定回答は上書きできません。この端末の診断は別の回として保存してください。');
  const localRevision=old.localRevision+1,row=useLocal?{...old,localRevision,remoteRevision:old.conflict.revision,conflict:null,operationId:`${deviceId}:${id}:${localRevision}`,deviceId,dirty:true}:{...old,payload:validate(old.kind,old.conflict.payload),localRevision,remoteRevision:old.conflict.revision,deviceId:old.conflict.deviceId,operationId:old.conflict.operationId,dirty:false,conflict:null,ancestors:[]};store.put(row);return row;
 });}
 function clearDiagnostics(){if(owner.startsWith('uid:'))throw new Error('ログイン中の診断は削除できません。');return transaction(async store=>{const rows=await request(store.index('namespace').getAll(namespace));for(const r of rows)if(r.kind==='diagnostic')store.delete(key(r.id));});}
 return {read,error:()=>validationError,write,merge,acknowledge,resolve,clearDiagnostics,flush:()=>queue,close:async()=>{await queue.catch(()=>{});if(dbPromise)(await dbPromise).close();},identity:()=>({owner,qualificationId,deviceId})};
}
