import {encodeResourceRow,decodeResourceRow} from '../v2/resources.js';
// Mutable plans and diagnostic runs use compare-and-swap, independently of
// immutable learning attempts. The outbox and local document commit together.
const request=r=>new Promise((resolve,reject)=>{r.onsuccess=()=>resolve(decodeResourceRow(r.result));r.onerror=()=>reject(r.error);});
const finished=tx=>new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error||new Error('保存を中止しました。'));tx.onerror=()=>{};});
const serial=JSON.stringify;
export const MAX_WORKSPACE_BYTES=850000;
export function createWorkspaceStore({owner,qualificationId,deviceId,rootPath,validate,namespaceName='workspace',planHistory=null}){
 let dbPromise,queue=Promise.resolve(),validationError=null;
 const namespace=[owner,qualificationId],key=id=>[...namespace,id],samePayload=(a,b)=>planHistory?planHistory.canonical(a)===planHistory.canonical(b):serial(a)===serial(b);
 async function db(){if(!dbPromise)dbPromise=new Promise((resolve,reject)=>{const r=indexedDB.open(`hitomon-v2:${rootPath}:${namespaceName}`,1);r.onupgradeneeded=()=>{const store=r.result.createObjectStore('documents',{keyPath:['owner','qualificationId','id']});store.createIndex('namespace',['owner','qualificationId']);};r.onsuccess=()=>resolve(decodeResourceRow(r.result));r.onerror=()=>reject(r.error);});return dbPromise;}
 const objectStore=tx=>{const raw=tx.objectStore('documents');return {get:(...a)=>raw.get(...a),index:(...a)=>raw.index(...a),delete:(...a)=>raw.delete(...a),put:row=>raw.put(encodeResourceRow(row)),add:row=>raw.add(encodeResourceRow(row))};};
 async function read(){const database=await db(),tx=database.transaction('documents'),done=finished(tx),rows=await request(tx.objectStore('documents').index('namespace').getAll(namespace));await done;validationError=null;return rows.filter(row=>{try{validate(row.kind,row.payload);return true;}catch(error){validationError=error;return false;}});}
 function transaction(callback){const op=queue.catch(()=>{}).then(async()=>{const database=await db(),tx=database.transaction('documents','readwrite'),done=finished(tx);try{const result=await callback(objectStore(tx));await done;return result;}catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}});queue=op;return op;}
 async function archivePlanning(store,before,after,origin='edited',force=false){
  if(!planHistory||!force&&before&&planHistory.canonical(before)===planHistory.canonical(after))return;
  const rows=await request(store.index('namespace').getAll(namespace));
  const matching=plan=>rows.filter(r=>r.kind==='planRevision'&&planHistory.canonical(r.payload.plan)===planHistory.canonical(plan)).sort((a,b)=>b.payload.savedAt.localeCompare(a.payload.savedAt)||b.id.localeCompare(a.id))[0];
  const add=(plan,previousId,source)=>{const payload=validate('planRevision',planHistory.create(plan,{previousId,origin:source}));if(new TextEncoder().encode(serial(payload)).length>MAX_WORKSPACE_BYTES)throw new Error('計画履歴が大きすぎます。850KB以内にしてください。');const id=payload.id,row={owner,qualificationId,id,kind:'planRevision',payload,localRevision:1,remoteRevision:0,deviceId,operationId:`${deviceId}:${id}:1`,dirty:true,ancestors:[]};store.add(row);rows.push(row);return row;};
  let previous=before?matching(before):null;
  if(before&&!previous)previous=add(before,null,'baseline');
  // Backup snapshots already contain the restored version; avoid a duplicate.
  if((origin==='restored'||!before)&&matching(after))return;
  add(after,previous?.id||null,before?origin:origin==='edited'?'registered':origin);
 }
 function write(kind,id,payload,expectedLocalRevision,{historyOrigin='edited'}={}){
  payload=JSON.parse(serial(validate(kind,payload)));if(new TextEncoder().encode(serial(payload)).length>MAX_WORKSPACE_BYTES)throw new Error('記録が大きすぎます。850KB以内にしてください。');
  return transaction(async store=>{const old=await request(store.get(key(id)));if(expectedLocalRevision!==undefined&&(old?.localRevision||0)!==expectedLocalRevision)throw new Error('別タブで更新されました。画面を開き直してから編集してください。');
   if(old?.conflict)throw new Error('別端末の変更と競合しています。先にどちらの内容を使うか選んでください。');
   if(kind==='planRevision'&&(id!==payload.id||old&&!samePayload(old.payload,payload)))throw new Error('同じIDの異なる計画履歴は保存できません。');
   if(['diagnostic','mock'].includes(kind)&&old){
    if(old.payload.status!=='in_progress'&&serial(old.payload)!==serial(payload))throw new Error('終了した診断は変更できません。');
    if(['blueprintVersion','selectionPolicy','catalogRevision','size','startedAt','mode','mockSet'].some(k=>serial(old.payload[k])!==serial(payload[k]))||serial(old.payload.slots)!==serial(payload.slots)||Object.entries(old.payload.responses).some(([id,value])=>!Object.hasOwn(payload.responses,id)||serial(payload.responses[id])!==serial(value)))throw new Error('診断の出題方針・問題と確定した回答は変更できません。');
   }
   if(kind==='case'&&old){
    if(['format','version','kind','id','qualificationId','examPartId','caseId','caseVersion','material','mode','startedAt'].some(k=>serial(old.payload[k])!==serial(payload[k])))throw Error('大問の教材・開始条件は変更できません。');
    for(const [key,response] of Object.entries(old.payload.responses))if(response.submittedAt){const next=payload.responses[key];if(!next||next.value!==response.value||next.submittedAt!==response.submittedAt||response.evaluation&&serial(next.evaluation)!==serial(response.evaluation))throw Error('確定した回答・評価は変更できません。新しく解き直してください。');}
   }
   const localRevision=(old?.localRevision||0)+1,operationId=`${deviceId}:${id}:${localRevision}`;
   const row={owner,qualificationId,id,kind,payload,localRevision,remoteRevision:old?.remoteRevision||0,deviceId,operationId,dirty:true,ancestors:[...(old?.ancestors||[]),...(old?.operationId?[old.operationId]:[])].slice(-100)};
   if(kind==='planning')await archivePlanning(store,old?.payload||null,payload,historyOrigin);
   store.put(row);return row;
  });
 }
 // A backup's planning/diagnostic additions either all commit, or none do.
 // Existing plans are deliberately retained; diagnostic IDs are immutable.
 function restoreBackup(value){
  const items=[...(value.plan?[{id:'planning',kind:'planning',payload:value.plan}]:[]),...(value.planRevisions||[]).map(payload=>({id:payload.id,kind:'planRevision',payload})),...value.runs.map(payload=>({id:payload.id,kind:payload.mode==='mock'?'mock':'diagnostic',payload}))].map(item=>{
   const payload=JSON.parse(serial(validate(item.kind,item.payload)));
   if(new TextEncoder().encode(serial(payload)).length>MAX_WORKSPACE_BYTES)throw new Error('記録が大きすぎます。850KB以内にしてください。');
   return {...item,payload};
  });
  if(new Set(items.map(item=>item.id)).size!==items.length)throw new Error('取り込む記録のIDが重複しています。');
  return transaction(async store=>{
   const result={plan:'absent',diagnosticsAdded:0,diagnosticsRetained:0,historyAdded:0,historyRetained:0};
   for(const item of items){
    const old=await request(store.get(key(item.id)));
    if(old){
     validate(old.kind,old.payload);
     if(old.kind!==item.kind||['diagnostic','mock','planRevision'].includes(item.kind)&&!samePayload(old.payload,item.payload))throw new Error('同じIDの異なる記録があります。計画・診断の取り込みを中止しました。');
     if(item.kind==='planning')result.plan='retained';else if(item.kind==='planRevision')result.historyRetained++;else result.diagnosticsRetained++;
     continue;
    }
    const localRevision=1,operationId=`${deviceId}:${item.id}:${localRevision}`;
    store.add({owner,qualificationId,...item,localRevision,remoteRevision:0,deviceId,operationId,dirty:true,ancestors:[]});
    if(item.kind==='planning')result.plan='restored';else if(item.kind==='planRevision')result.historyAdded++;else result.diagnosticsAdded++;
   }
   if(result.plan==='restored')await archivePlanning(store,null,value.plan,'restored');
   return result;
  });
 }
 function merge(remote){remote=decodeResourceRow(remote);
  if(remote.version!==2||!Number.isInteger(remote.revision)||remote.revision<1||typeof remote.deviceId!=='string'||typeof remote.operationId!=='string'||remote.kind==='planning'&&remote.id!=='planning'||['diagnostic','mock','planRevision'].includes(remote.kind)&&remote.id!==remote.payload?.id)throw new Error('同期データの形式を確認できません。');
  const payload=validate(remote.kind,remote.payload);
  return transaction(async store=>{const old=await request(store.get(key(remote.id)));
   if(remote.kind==='planRevision'&&old&&!samePayload(old.payload,payload))throw new Error('同期された計画履歴のIDが重複しています。既存の履歴は保持しました。');
   if(old?.dirty){
    if(old.operationId===remote.operationId||serial(old.payload)===serial(payload)||remote.kind==='planRevision'&&samePayload(old.payload,payload)){const row={...old,payload,remoteRevision:remote.revision,dirty:false,conflict:null};store.put(row);return row;}
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
  if(useLocal&&['diagnostic','mock','case'].includes(old.kind))throw new Error('診断の確定回答は上書きできません。この端末の診断は別の回として保存してください。');
  if(old.kind==='planning')await archivePlanning(store,useLocal?validate('planning',old.conflict.payload):old.payload,useLocal?old.payload:validate('planning',old.conflict.payload),'resolved',true);
  const localRevision=old.localRevision+1,row=useLocal?{...old,localRevision,remoteRevision:old.conflict.revision,conflict:null,operationId:`${deviceId}:${id}:${localRevision}`,deviceId,dirty:true}:{...old,payload:validate(old.kind,old.conflict.payload),localRevision,remoteRevision:old.conflict.revision,deviceId:old.conflict.deviceId,operationId:old.conflict.operationId,dirty:false,conflict:null,ancestors:[]};store.put(row);return row;
 });}
 function clearDiagnostics(){if(owner.startsWith('uid:'))throw new Error('ログイン中の診断は削除できません。');return transaction(async store=>{const rows=await request(store.index('namespace').getAll(namespace));for(const r of rows)if(['diagnostic','mock'].includes(r.kind))store.delete(key(r.id));});}
 function writeNotes(items,{keepExisting=false}={}){
  const checked=items.map(p=>JSON.parse(serial(validate('note',p))));
  return transaction(async store=>{
   for(const payload of checked){const id='note--'+payload.topicId,old=await request(store.get(key(id)));if(old&&keepExisting)continue;
    if(old?.conflict)throw new Error('分野メモが競合しています。先に使う内容を選んでください。');
    const localRevision=(old?.localRevision||0)+1,operationId=`${deviceId}:${id}:${localRevision}`;
    store.put({owner,qualificationId,id,kind:'note',payload,localRevision,remoteRevision:old?.remoteRevision||0,deviceId,operationId,dirty:true,ancestors:[...(old?.ancestors||[]),...(old?.operationId?[old.operationId]:[])].slice(-100)});
    store.delete(key('draft--'+payload.topicId));
   }
  });
 }
 function removeDraft(id){if(!id.startsWith('draft--'))throw new Error('下書き以外は削除できません。');return transaction(async store=>{const row=await request(store.get(key(id)));if(row?.kind==='draft')store.delete(key(id));});}
 return {writeNotes,removeDraft,read,error:()=>validationError,write,restoreBackup,merge,acknowledge,resolve,clearDiagnostics,flush:()=>queue,close:async()=>{await queue.catch(()=>{});if(dbPromise)(await dbPromise).close();},identity:()=>({owner,qualificationId,deviceId})};
}
