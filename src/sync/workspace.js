// New synchronization is optional: an old production rule must not interrupt
// the existing attempt sync or local learning.
export function createWorkspaceSync({uid,qualificationId,store,remote,onChange=()=>{},onStatus=()=>{}}){
 let stopped=false,running=null,cursor=null,cursorLoaded=false,timer,lastRun=0,rerun=false;
 const bounded=promise=>new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('同期通信がタイムアウトしました。')),20000);promise.then(resolve,reject).finally(()=>clearTimeout(timeout));});
 async function perform(){
  if(stopped||!navigator.onLine)return;lastRun=Date.now();onStatus('syncing');
  try{
   if(!cursorLoaded){cursor=await store.cursor?.()||null;cursorLoaded=true;if(stopped)return;}
   let more=true;while(!stopped&&more){const page=await bounded(remote.pullDocuments(uid,qualificationId,cursor));if(stopped)return;for(const row of page.rows){await store.merge(row);if(stopped)return;}await store.setCursor?.(page.cursor);if(stopped)return;cursor=page.cursor;more=page.more;}
   for(const row of await store.read()){
    if(stopped)return;if(!row.dirty||row.conflict)continue;
    if(row.owner!==`uid:${uid}`||row.qualificationId!==qualificationId)throw new Error('同期先のアカウントが一致しません。');
    const result=await bounded(remote.pushDocument(uid,qualificationId,row));if(stopped)return;
    if(result.conflict)await store.merge(result.remote);else await store.acknowledge(row.id,row.operationId,result.remote);
   }
   if(stopped)return;const rows=await store.read();onStatus(rows.some(r=>r.conflict)?'conflict':rows.some(r=>r.dirty)?'pending':'synced');onChange(rows);if(rows.some(r=>r.dirty&&!r.conflict))timer=setTimeout(run,15000);
  }catch(error){if(!stopped){console.warn('Planning sync failed',error.code||'',error.message);onStatus(String(error.code).includes('permission-denied')?'rules':'error',error);onChange(await store.read());}}
 }
 function run(){clearTimeout(timer);if(stopped)return Promise.resolve();if(running){rerun=true;return running;}running=perform().finally(()=>{running=null;if(rerun&&!stopped){rerun=false;timer=setTimeout(run,0);}});return running;}
 return {run,schedule:()=>{clearTimeout(timer);timer=setTimeout(run,Math.max(1200,15000-(Date.now()-lastRun)));},refresh:()=>Date.now()-lastRun>=60000?run():Promise.resolve(),stop:()=>{stopped=true;clearTimeout(timer);}};
}
