import {createSyncEngine} from './engine.js';
import {createWorkspaceSync} from './workspace.js';
import {setSyncAccount,setSyncStatus} from '../ui/sync-status.js';

// Deterministic UUID for guest adoption: two tabs importing the same guest
// attempt into the same account address one record instead of duplicating it.
export async function guestAttemptId(uid,source){
 const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(`${uid}|${source}`))).slice(0,16);
 bytes[6]=(bytes[6]&15)|128;bytes[8]=(bytes[8]&63)|128;
 const hex=[...bytes].map(b=>b.toString(16).padStart(2,'0')).join('');return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}

export async function initAccountControls({qualificationId,syncScopeLabels={},getStore,getWorkspaceStore,getLearningStore,onLearningRows,onLearningStatus,getCardStore,onCardRows,onCardStatus,getWrittenStore,onWrittenRows,getPersonalStore,onPersonalRows,onPersonalStatus,switchOwner,importGuest,getGuestImportAvailable=async()=>false,validateAttempt,onRecords,onFork,onDocuments,onWorkspaceStatus}){
 const find=id=>document.getElementById(id),login=find('google-login'),logout=find('google-logout'),refresh=find('sync-now'),adopt=find('import-guest'),status=find('sync-state');
 let client,engine,workspaceEngine,learningEngine,cardsEngine,personalEngine,writtenEngine,user,observedUser,transition=Promise.resolve(),generation=0,busy=false,firstObservation=true,guestAvailable=false;
 // Startup waits for the local owner/checkpoint, never a cloud sync round trip.
 let resolveReady,rejectReady;
 const ready=new Promise((resolve,reject)=>{resolveReady=resolve;rejectReady=reject;});
 ready.catch(()=>{});
 const showStatus=(kind,error)=>{
  if(kind==='error')console.warn('Study sync failed',error?.code||error?.name,error?.message);
  setSyncStatus('study',kind,error);
 };
 const scheduleDocuments=(worker,notify)=>{if(!worker)return;notify?.(navigator.onLine?'pending':'offline');worker.schedule();};
 const buttons=()=>{login.hidden=!!observedUser;logout.hidden=!observedUser;refresh.hidden=!user;adopt.hidden=!user||!guestAvailable;for(const b of [login,logout,refresh,adopt])b.disabled=busy;};
 async function refreshGuestAvailability(){const token=generation,uid=user?.uid;if(!uid){guestAvailable=false;buttons();return;}try{const available=await getGuestImportAvailable(uid);if(token===generation){guestAvailable=available;buttons();}}catch(error){if(token===generation){guestAvailable=true;buttons();console.warn('Guest availability unavailable',error.message);}}}
 const failure=(error,operation='ログイン')=>{
  const code=String(error?.code||'');
  status.textContent=operation==='ログアウト'?'ログアウトできませんでした。もう一度お試しください。':code.includes('popup-closed')?'ログインをキャンセルしました。':code.includes('popup-blocked')?'ブラウザのポップアップを許可して、もう一度お試しください。':'ログインできませんでした。接続を確認してもう一度お試しください。';console.warn('Account operation failed',code,error.message);
 };
 login.addEventListener('click',()=>{
  if(!client||busy)return;busy=true;buttons();
  // Open directly from the click; an awaited local save here loses the gesture.
  client.login().catch(error=>failure(error)).finally(()=>{busy=false;buttons();});
 });
 async function stopSync(){
  const workers=[engine,workspaceEngine,learningEngine,cardsEngine,personalEngine,writtenEngine];
  engine=workspaceEngine=learningEngine=cardsEngine=personalEngine=writtenEngine=null;
  await Promise.all(workers.map(worker=>worker?.stop()));
 }
 function startSync(){
  if(user?.uid!==observedUser?.uid)return;
  if(user){engine=createSyncEngine({uid:user.uid,qualificationId,store:getStore(),remote:client,validateAttempt,onRecords,onFork,onStatus:showStatus});engine.run();if(getWorkspaceStore?.()){workspaceEngine=createWorkspaceSync({uid:user.uid,qualificationId,store:getWorkspaceStore(),remote:client,onChange:onDocuments,onStatus:onWorkspaceStatus});workspaceEngine.run();}if(getLearningStore?.()){learningEngine=createWorkspaceSync({uid:user.uid,qualificationId,store:getLearningStore(),remote:{pullDocuments:(...args)=>client.pullLearning(...args),pushDocument:(...args)=>client.pushLearning(...args)},onChange:onLearningRows,onStatus:onLearningStatus});learningEngine.run();}if(getCardStore?.()){onCardStatus?.(navigator.onLine?'pending':'offline');cardsEngine=createWorkspaceSync({uid:user.uid,qualificationId,store:getCardStore(),remote:{pullDocuments:(...args)=>client.pullCards(...args),pushDocument:(...args)=>client.pushCard(...args)},onChange:onCardRows,onStatus:onCardStatus});cardsEngine.run();}if(getPersonalStore?.()){personalEngine=createWorkspaceSync({uid:user.uid,qualificationId,store:getPersonalStore(),remote:{pullDocuments:(...args)=>client.pullPersonal(...args),pushDocument:(...args)=>client.pushPersonal(...args)},onChange:onPersonalRows,onStatus:onPersonalStatus});personalEngine.run();}if(getWrittenStore?.()){writtenEngine=createWorkspaceSync({uid:user.uid,qualificationId,store:getWrittenStore(),remote:{pullDocuments:(...args)=>client.pullDocuments(...args,'writtenV2'),pushDocument:(...args)=>client.pushDocument(...args,'writtenV2')},onChange:onWrittenRows,onStatus:(status,error)=>setSyncStatus('written',status,error)});writtenEngine.run();}}else {showStatus('guest');onCardStatus?.('guest');onWorkspaceStatus?.('guest');onLearningStatus?.('guest');onPersonalStatus?.('guest');}
 }
 logout.addEventListener('click',async()=>{
  if(busy)return;busy=true;buttons();const token=generation,uid=user?.uid;
  try{await stopSync();await client.logout();}
  catch(error){if(token===generation&&uid&&user?.uid===uid&&observedUser?.uid===uid)startSync();failure(error,'ログアウト');}
  finally{if(token===generation)busy=false;buttons();}
 });
 refresh.addEventListener('click',()=>{engine?.run();workspaceEngine?.run();learningEngine?.run();cardsEngine?.run();personalEngine?.run();writtenEngine?.run();});
 adopt.addEventListener('click',async()=>{
  if(busy||!user)return;busy=true;buttons();const uid=user.uid;
  try{await importGuest(uid);if(user?.uid===uid){await engine?.run();await workspaceEngine?.run();await learningEngine?.run();await cardsEngine?.run();await personalEngine?.run();writtenEngine?.run();await refreshGuestAvailability();}}catch(error){status.textContent=error.message;}finally{busy=false;buttons();}
 });
 try{
  const {createFirebaseClient}=await import('./firebase.js');client=createFirebaseClient();
  client.observe(next=>{
   observedUser=next;
   const restore=firstObservation;firstObservation=false;
   const token=++generation;
   transition=transition.catch(()=>{}).then(async()=>{
    busy=true;guestAvailable=false;buttons();await stopSync();setSyncAccount(false);
    if(token!==generation)return;
    await switchOwner(next?`uid:${next.uid}`:null,{restore});if(token!==generation)return;
    user=next;find('account-name').hidden=!user;find('account-name').textContent=user?(user.email||user.displayName||'Googleアカウント'):'';setSyncAccount(!!user,user?['study',...(getWorkspaceStore?.()?['planning']:[]),...(getLearningStore?.()?['learning']:[]),...(getCardStore?.()?['cards']:[]),...(getPersonalStore?.()?['personal']:[]),...(getWrittenStore?.()?['written']:[])]:[],syncScopeLabels);buttons();
    startSync();
    resolveReady();
    await refreshGuestAvailability();
   }).catch(error=>{if(token===generation)rejectReady(error);status.textContent='保存先を切り替えられませんでした。先に学習記録を書き出してください。';console.error('Account storage transition failed',error.name);}).finally(()=>{busy=false;buttons();});
  });
 }catch(error){status.textContent='ログイン機能を読み込めませんでした。端末内で学習を続けられます。';login.disabled=true;resolveReady();}
 window.addEventListener('online',()=>{engine?.run();workspaceEngine?.run();learningEngine?.run();cardsEngine?.run();personalEngine?.run();writtenEngine?.run();});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'){engine?.refresh();workspaceEngine?.refresh();learningEngine?.refresh();cardsEngine?.refresh();personalEngine?.refresh();writtenEngine?.refresh();}});
 const interval=setInterval(()=>{if(document.visibilityState==='visible'&&navigator.onLine){engine?.refresh();workspaceEngine?.refresh();learningEngine?.refresh();cardsEngine?.refresh();personalEngine?.refresh();writtenEngine?.refresh();}},60000);
 window.addEventListener('pagehide',()=>clearInterval(interval),{once:true});
 return {ready,writtenChanged:()=>scheduleDocuments(writtenEngine,status=>setSyncStatus('written',status)),refreshGuestAvailability,personalChanged:()=>scheduleDocuments(personalEngine,onPersonalStatus),cardsChanged:()=>scheduleDocuments(cardsEngine,onCardStatus),learningChanged:()=>scheduleDocuments(learningEngine,onLearningStatus),prepareLearning:async()=>{await learningEngine?.run();if(learningEngine)await onLearningRows(await getLearningStore().read());},changed:()=>engine?.schedule(),workspaceChanged:()=>scheduleDocuments(workspaceEngine,onWorkspaceStatus),owner:()=>user?`uid:${user.uid}`:null};
}
