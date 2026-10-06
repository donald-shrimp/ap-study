import {createSyncEngine} from './engine.js';

// Deterministic UUID for guest adoption: two tabs importing the same guest
// attempt into the same account address one record instead of duplicating it.
export async function guestAttemptId(uid,source){
 const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(`${uid}|${source}`))).slice(0,16);
 bytes[6]=(bytes[6]&15)|128;bytes[8]=(bytes[8]&63)|128;
 const hex=[...bytes].map(b=>b.toString(16).padStart(2,'0')).join('');return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}

const messages={pending:'同期待ち',syncing:'同期中…',synced:'同期済み',offline:'オフライン · 接続後に同期します',blocked:'大きすぎる記録はこの端末に保存しています'};
export async function initAccountControls({qualificationId,getStore,switchOwner,importGuest,validateAttempt,onRecords,onFork}){
 const find=id=>document.getElementById(id),login=find('google-login'),logout=find('google-logout'),refresh=find('sync-now'),adopt=find('import-guest'),status=find('sync-state');
 let client,engine,user,observedUser,transition=Promise.resolve(),generation=0,busy=false,firstObservation=true;
 const showStatus=(kind,error)=>{
  if(kind==='error')console.warn('Study sync failed',error?.code||error?.name,error?.message);
  status.textContent=messages[kind]|| (kind==='error'?(String(error?.code).includes('permission-denied')?'同期の許可がありません。Firebaseのアクセスルールを確認してください。':'同期できませんでした。記録はこの端末に残っています。'):'ログインすると、学習記録を同期できます。');
  const foot=find('cloud-state');foot.hidden=!user;foot.textContent=status.textContent;
 };
 const buttons=()=>{login.hidden=!!observedUser;logout.hidden=!observedUser;refresh.hidden=!user;adopt.hidden=!user;for(const b of [login,logout,refresh,adopt])b.disabled=busy;};
 const failure=error=>{
  const code=String(error?.code||'');
  status.textContent=code.includes('popup-closed')?'ログインをキャンセルしました。':code.includes('popup-blocked')?'ポップアップがブロックされました。Chromeで許可してからもう一度お試しください。':code.includes('unauthorized-domain')?'Firebaseの承認済みドメインに、このサイトを追加してください。':code.includes('operation-not-allowed')?'FirebaseでGoogleログインを有効にしてください。':'ログイン処理を完了できませんでした。接続を確認してもう一度お試しください。';
 };
 login.addEventListener('click',()=>{
  if(!client||busy)return;busy=true;buttons();
  // Open directly from the click; an awaited local save here loses the gesture.
  client.login().catch(failure).finally(()=>{busy=false;buttons();});
 });
 logout.addEventListener('click',async()=>{
  if(busy)return;busy=true;buttons();try{await engine?.stop();await client.logout();}catch(error){failure(error);}finally{busy=false;buttons();}
 });
 refresh.addEventListener('click',()=>engine?.run());
 adopt.addEventListener('click',async()=>{
  if(busy||!user)return;busy=true;buttons();const uid=user.uid;
  try{await importGuest(uid);if(user?.uid===uid)await engine?.run();}catch(error){status.textContent=error.message;}finally{busy=false;buttons();}
 });
 try{
  const {createFirebaseClient}=await import('./firebase.js');client=createFirebaseClient();
  client.observe(next=>{
   observedUser=next;
   const restore=firstObservation;firstObservation=false;
   const token=++generation;
   transition=transition.catch(()=>{}).then(async()=>{
    busy=true;buttons();await engine?.stop();engine=null;
    if(token!==generation)return;
    await switchOwner(next?`uid:${next.uid}`:null,{restore});if(token!==generation)return;
    user=next;find('account-name').textContent=user?(user.email||user.displayName||'Googleアカウント'):'ログインなしで学習できます。';buttons();
    if(user){engine=createSyncEngine({uid:user.uid,qualificationId,store:getStore(),remote:client,validateAttempt,onRecords,onFork,onStatus:showStatus});engine.run();}else showStatus('guest');
   }).catch(error=>{status.textContent='保存先を切り替えられませんでした。先に学習記録を書き出してください。';console.error('Account storage transition failed',error.name);}).finally(()=>{busy=false;buttons();});
  });
 }catch(error){status.textContent='ログイン機能を読み込めませんでした。端末内で学習を続けられます。';login.disabled=true;}
 window.addEventListener('online',()=>engine?.run());
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')engine?.refresh();});
 const interval=setInterval(()=>{if(document.visibilityState==='visible'&&navigator.onLine)engine?.refresh();},60000);
 window.addEventListener('pagehide',()=>clearInterval(interval),{once:true});
 return {changed:()=>engine?.schedule(),owner:()=>user?`uid:${user.uid}`:null};
}
