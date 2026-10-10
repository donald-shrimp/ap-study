"""Real IndexedDB durability: legacy ratings, atomic outbox and controls/cursor."""
import shutil
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);pg=b.new_page();pg.goto('http://127.0.0.1:4173/');pg.locator('.quick-start').wait_for()
 result=pg.evaluate('''async()=>{
 const {createCardStore}=await import('./src/storage/cards.js'),rootPath=new URL('.',document.baseURI).pathname,owner='test-store',qualificationId='ap';const identity={rootPath,owner,qualificationId,deviceId:'device'};
 const e={id:'old',cardId:'one',cardVersion:1,outcome:'again',at:'2026-10-10T00:00:00.000Z'};
 let s=createCardStore(identity);await s.read();await s.close();
 // Seed the actual pre-sync v1 database layout.
 const db=await new Promise((resolve,reject)=>{const r=indexedDB.open(`hitomon:${rootPath}:cards`,1);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
 await new Promise((resolve,reject)=>{const tx=db.transaction('events','readwrite');tx.objectStore('events').put({...e,owner,qualificationId});tx.oncomplete=resolve;tx.onabort=reject;});db.close();
 s=createCardStore(identity);const initial=await s.read(),legacy=await s.syncStore().read();if(initial.events.length!==1||!legacy[0].dirty)throw Error('legacy lost');
 const cursor={seconds:1,nanoseconds:2,id:'rating--old'};await s.syncStore().setCursor(cursor);await s.write({cardId:'one',flipped:true});
 // Failure after event/outbox insertion must roll back both as well as checkpoint.
 const original=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(value,...args){if(this.name==='checkpoints')throw Error('injected');return original.call(this,value,...args);};
 let rollback=false;try{await s.write({cardId:'two'},{...e,id:'failed'});}catch{rollback=true;}finally{IDBObjectStore.prototype.put=original;}
 if(!rollback||(await s.read()).events.length!==1||(await s.read()).checkpoint.cardId!=='one')throw Error('partial transaction');
 await s.clear();if((await s.read()).events.length)throw Error('reset failed');await s.close();s=createCardStore(identity);if((await s.read()).events.length||JSON.stringify(await s.syncStore().cursor())!==JSON.stringify(cursor))throw Error('cursor/reset reload');
 await s.importEvents([e],{restoreDeleted:false});if((await s.read()).events.length)throw Error('guest resurrected');
 await s.importEvents([e]);if((await s.read()).events.length!==1)throw Error('backup restore');const count=(await s.syncStore().read()).length;await s.importEvents([e]);if((await s.syncStore().read()).length!==count)throw Error('duplicate restore');
 let conflict=false;try{await s.importEvents([{...e,id:'new'},{...e,outcome:'recalled'}]);}catch{conflict=true;}if(!conflict||(await s.read()).events.length!==1)throw Error('partial import');
 const q=createCardStore({...identity,qualificationId:'other'});if((await q.read()).events.length)throw Error('qualification leak');await q.close();
 await s.clear();await s.importEvents([e]);const rows=await s.syncStore().read();if(rows.filter(r=>r.kind==='reset').length!==2||rows.filter(r=>r.kind==='restore').length!==2)throw Error('later reset/restore');
 const many=createCardStore({...identity,owner:'chunk-test'});await many.importEvents(Array.from({length:205},(_,i)=>({...e,id:`event-${i}`})));await many.clear();const controls=await many.syncStore().read();if(controls.filter(r=>r.kind==='reset').length!==2||controls.some(r=>r.kind==='reset'&&r.payload.eventIds.length>200))throw Error('chunk reset');await many.close();
 await s.close();return {rollback,legacy:true,atomicImport:conflict,namespace:true,controls:rows.length};
 }''')
 assert result['rollback'] and result['atomicImport'];b.close()
print('PASS actual IDB legacy preservation / atomic event-outbox-checkpoint rollback / durable cursor/reset / backup restore / repeated import / guest no-resurrection / qualification isolation')
