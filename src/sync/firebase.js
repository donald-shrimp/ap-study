import * as sdk from '../../assets/vendor/firebase.js';
import {firebaseConfig} from './config.js';
import {complete} from '../domain/study.js';

const stable=value=>JSON.stringify(value,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const resultKey=payload=>{const {hintCount,hintEvents,updatedAt,...result}=payload;return stable(result);};

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
