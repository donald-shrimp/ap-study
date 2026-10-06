// Transport-independent synchronization; remote pages and their cursor commit
// together. The bound UID/store cannot change while an operation is in flight.
export function createSyncEngine({uid,qualificationId,store,remote,validateAttempt,onRecords=()=>{},onFork=()=>{},onStatus=()=>{},isOnline=()=>navigator.onLine}){
 let stopped=false,running=null,timer,latestScheduled='',lastRun=0,retries=0;
 const active=()=>!stopped;
 const bounded=operation=>new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('同期通信がタイムアウトしました。')),20000);operation.then(resolve,reject).finally(()=>clearTimeout(timeout));});
 async function download(){
  let cursor=await store.cursor(),more=true,held=false;
  while(active()&&more){
   const page=await bounded(remote.pull(uid,qualificationId,cursor));if(!active())return;
   for(const row of page.rows){
    if(row.version!==1||row.id!==row.payload?.id||!Number.isInteger(row.revision)||row.revision<1||typeof row.deviceId!=='string')throw new Error('同期データの形式を確認できません。');
    validateAttempt({...row.payload,scrollY:0});
   }
   const pending=new Map((await store.pending()).map(item=>[item.id,item]));
   for(const row of page.rows){const item=pending.get(row.id);if(item&&item.deviceId!==row.deviceId){
    const fork=await store.forkPending(item.id,item.revision);if(!active())return;if(fork)onFork(fork);
   }else if(item)held=true;}
   // A pending local revision prevents applying that remote row. Keep the
   // durable cursor behind it until the upload is acknowledged, then reread it.
   const changed=await store.mergeRemote(page.rows,held?null:page.cursor);if(!active())return;onRecords(changed);cursor=page.cursor;more=page.more;
  }
 }
 async function perform(){
  if(!active()||!isOnline()){onStatus('offline');return;}
  lastRun=Date.now();onStatus('syncing');
  try{
   await download();if(!active())return;
   let items=await store.pending(),blocked=0;
   // A foreign-device import is forked once and retried under its own UUID.
   for(let index=0;index<items.length&&active();index++){
    const item=items[index];if(item.blocked){blocked++;continue;}
    if(item.owner!==`uid:${uid}`||item.qualificationId!==qualificationId)throw new Error('送信先のアカウントが一致しません。');
    validateAttempt({...item.payload,scrollY:0});
    const result=await bounded(remote.push(uid,qualificationId,item));if(!active())return;
    if(result==='fork'){
     const fork=await store.forkPending(item.id,item.revision);if(fork){onFork(fork);items.push(...(await store.pending()).filter(x=>x.id===fork.after));}
    }else await store.acknowledge(item.id,item.revision);
   }
   if(!active())return;if(items.some(item=>!item.blocked))await download();if(!active())return;
   const remaining=await store.pending();retries=0;onStatus(blocked?'blocked':remaining.length?'pending':'synced');
   if(remaining.some(item=>!item.blocked))timer=setTimeout(()=>run(),15000);
  }catch(error){if(active()){
   onStatus('error',error);
   if(isOnline()&&(/unavailable|network-request-failed|deadline-exceeded/.test(error.code||'')||error.message==='同期通信がタイムアウトしました。'))timer=setTimeout(()=>run(),Math.min(60000,15000*2**retries++));
  }}
 }
 function run(){clearTimeout(timer);timer=null;if(stopped)return Promise.resolve();if(running)return running;
  running=perform().finally(()=>{running=null;});return running;
 }
 async function schedule(){
  if(stopped)return;const items=await store.pending();if(stopped)return;
  const signature=items.map(x=>x.operationId).sort().join('|');if(!signature||signature===latestScheduled)return;
  latestScheduled=signature;onStatus('pending');clearTimeout(timer);
  timer=setTimeout(()=>run(),Math.max(1200,15000-(Date.now()-lastRun)));
 }
 return {run,schedule,stop:async()=>{stopped=true;clearTimeout(timer);},refresh:()=>{if(Date.now()-lastRun>=60000)return run();return Promise.resolve();}};
}
