// Ancillary checkpoints live outside record databases: no upgrade of an open
// learning DB is needed. Call setCursor only after all page documents commit.
const valid=c=>!!c&&Object.keys(c).every(k=>['seconds','nanoseconds','id'].includes(k))&&Number.isSafeInteger(c.seconds)&&Number.isInteger(c.nanoseconds)&&c.nanoseconds>=0&&c.nanoseconds<1e9&&typeof c.id==='string'&&c.id.length>0&&c.id.length<=1500;
const idLater=(a,b)=>{const enc=new TextEncoder(),left=enc.encode(a),right=enc.encode(b);for(let i=0;i<Math.min(left.length,right.length);i++)if(left[i]!==right[i])return left[i]>right[i];return left.length>right.length;};
const later=(a,b)=>a.seconds!==b.seconds?a.seconds>b.seconds:a.nanoseconds!==b.nanoseconds?a.nanoseconds>b.nanoseconds:idLater(a.id,b.id);
export function createSyncCursorStore({rootPath,owner,qualificationId,namespaceName}){
 const key=[owner,qualificationId,namespaceName];let connection,queue=Promise.resolve();
 async function db(){
  if(!connection)connection=new Promise((resolve,reject)=>{
   const r=indexedDB.open(`hitomon-v2:${rootPath}:sync-cursors`,1);
   r.onupgradeneeded=()=>r.result.createObjectStore('checkpoints',{keyPath:['owner','qualificationId','namespaceName']});
   r.onerror=()=>reject(r.error);r.onblocked=()=>reject(Error('同期位置を保存できません。別タブを閉じて開き直してください。'));
   r.onsuccess=()=>{r.result.onversionchange=()=>r.result.close();resolve(r.result);};
  });return connection;
 }
 function operation(mode,fn){
  const op=queue.catch(()=>{}).then(async()=>{
   const database=await db(),tx=database.transaction('checkpoints',mode),store=tx.objectStore('checkpoints');
   const done=new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error||Error('同期位置を保存できません。'));tx.onerror=()=>{};});
   try{
    const row=await new Promise((resolve,reject)=>{const r=store.get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
    const result=fn(store,valid(row?.cursor)?row.cursor:null);await done;return result;
   }catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}
  });queue=op;return op;
 }
 return {
  cursor:()=>operation('readonly',(_,cursor)=>structuredClone(cursor)),
  setCursor:cursor=>{if(cursor===null)return Promise.resolve();if(!valid(cursor))throw Error('同期位置の形式を確認できません。');const next=structuredClone(cursor);return operation('readwrite',(store,old)=>{if(!old||later(next,old))store.put({owner,qualificationId,namespaceName,cursor:next});});},
  close:async()=>{await queue.catch(()=>{});if(connection)(await connection).close();}
 };
}
