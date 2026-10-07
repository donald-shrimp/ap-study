import * as sdk from '../../assets/vendor/firebase.js';
import {firebaseConfig} from './config.js';
import {complete} from '../domain/study.js';

const stable=value=>JSON.stringify(value,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const resultKey=payload=>{const {hintCount,hintEvents,updatedAt,...result}=payload;return stable(result);};

export async function recoverResourceWrite(error,item,readCurrent,authorize){
 if(!String(error.code).includes('permission-denied'))throw error;
 authorize();let fresh;
 try{fresh=await readCurrent();}catch{throw error;}
 authorize();
 if(fresh?.operationId===item.operationId)return {remote:fresh};
 if(fresh&&fresh.revision>item.remoteRevision)return {conflict:true,remote:fresh};
 throw error;
}

export function createFirebaseClient(){
 const app=sdk.initializeApp(firebaseConfig),auth=sdk.getAuth(app);
 // Long polling also works behind proxies and avoids an idle streaming read.
 const db=sdk.initializeFirestore(app,{experimentalForceLongPolling:true});
 if(['localhost','127.0.0.1'].includes(location.hostname)&&new URL(location.href).searchParams.get('firebase-emulator')==='1'){
  sdk.connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});
  sdk.connectFirestoreEmulator(db,'127.0.0.1',8080);
 }
 const path=(uid,qualificationId)=>sdk.collection(db,'users',uid,'qualifications',qualificationId,'attempts');
 function authorize(uid){if(auth.currentUser?.uid!==uid)throw new Error('同期するアカウントが変わりました。');}
 return {
  observe:callback=>sdk.onAuthStateChanged(auth,callback),
  login:()=>sdk.signInWithPopup(auth,new sdk.GoogleAuthProvider()),
  logout:()=>sdk.signOut(auth),
  async pullDocuments(uid,qualificationId,cursor){
   authorize(uid);const ref=sdk.collection(db,'users',uid,'qualifications',qualificationId,'resources'),constraints=[sdk.orderBy('updatedAt'),sdk.orderBy('__name__'),sdk.limit(25)];
   if(cursor)constraints.splice(2,0,sdk.startAfter(new sdk.Timestamp(cursor.seconds,cursor.nanoseconds),cursor.id));
   const page=await sdk.getDocsFromServer(sdk.query(ref,...constraints));authorize(uid);
   const rows=page.docs.map(d=>({id:d.id,...d.data()})),last=page.docs.at(-1);
   return {rows,cursor:last?{seconds:last.data().updatedAt.seconds,nanoseconds:last.data().updatedAt.nanoseconds,id:last.id}:cursor,more:rows.length===25};
  },
  async pushDocument(uid,qualificationId,item){
   authorize(uid);const ref=sdk.doc(db,'users',uid,'qualifications',qualificationId,'resources',item.id);
   try{return await sdk.runTransaction(db,async tx=>{
    authorize(uid);const existing=await tx.get(ref),old=existing.exists()?{id:existing.id,...existing.data()}:null;
    if(old?.operationId===item.operationId)return {remote:old};
    if((old?.revision||0)!==item.remoteRevision)return {conflict:true,remote:old};
    const value={version:1,kind:item.kind,revision:item.remoteRevision+1,operationId:item.operationId,deviceId:item.deviceId,payload:item.payload,updatedAt:sdk.serverTimestamp()};
    tx.set(ref,value);return {remote:{id:item.id,...value}};
   });}catch(error){
    // Revision Rules may reject a transaction that raced another commit before
    // its precondition is evaluated. Distinguish this from missing permissions
    // without retrying or overwriting the newly committed document.
    return recoverResourceWrite(error,item,async()=>{const current=await sdk.getDocFromServer(ref);return current.exists()?{id:current.id,...current.data()}:null;},()=>authorize(uid));
   }
  },
  async pull(uid,qualificationId,cursor){
   authorize(uid);const constraints=[sdk.orderBy('updatedAt'),sdk.orderBy('__name__'),sdk.limit(100)];
   if(cursor)constraints.splice(2,0,sdk.startAfter(new sdk.Timestamp(cursor.seconds,cursor.nanoseconds),cursor.id));
   const page=await sdk.getDocsFromServer(sdk.query(path(uid,qualificationId),...constraints));authorize(uid);
   const rows=page.docs.map(d=>({id:d.id,...d.data()})),last=page.docs.at(-1);
   return {rows,cursor:last?{seconds:last.data().updatedAt.seconds,nanoseconds:last.data().updatedAt.nanoseconds,id:last.id}:cursor,more:rows.length===100};
  },
  async push(uid,qualificationId,item){
   authorize(uid);const ref=sdk.doc(path(uid,qualificationId),item.id);
   return sdk.runTransaction(db,async tx=>{
    authorize(uid);const current=await tx.get(ref),remote=current.exists()?current.data():null;
    const sameResult=remote&&complete(remote.payload)&&complete(item.payload)&&resultKey(remote.payload)===resultKey(item.payload);
    if(sameResult&&item.payload.hintCount>remote.payload.hintCount){
     const revision=Math.max(remote.revision,item.revision)+1;
     tx.set(ref,{...remote,revision,operationId:`${item.id}:${revision}`,payload:{...remote.payload,hintCount:item.payload.hintCount,hintEvents:item.payload.hintEvents,updatedAt:item.payload.updatedAt},updatedAt:sdk.serverTimestamp()});return 'ack';
    }
    if(remote?.deviceId!==undefined&&remote.deviceId!==item.deviceId)return 'fork';
    if(remote&&remote.revision>=item.revision)return 'ack';
    tx.set(ref,{version:1,deviceId:item.deviceId,revision:item.revision,operationId:item.operationId,payload:item.payload,updatedAt:sdk.serverTimestamp()});return 'ack';
   });
  }
 };
}
