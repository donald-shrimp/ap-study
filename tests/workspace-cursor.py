"""Durable workspace/learning cursors after real IndexedDB page commits."""
import os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/')
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);ctx=b.new_context(service_workers='block');pg=ctx.new_page();pg.route('**/cursor-probe',lambda r:r.fulfill(content_type='text/html',body='<html><body></body></html>'));pg.goto(BASE+'cursor-probe')
  result=pg.evaluate('''async()=>{
   const root=new URL('.',location.href),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),{createWorkspaceSync}=await import(new URL('src/sync/workspace.js',root)),{createLocalStore}=await import(new URL('src/storage/local.js',root));
   const assert=(v,m)=>{if(!v)throw Error(m);},make=(path,extra={})=>createWorkspaceStore({owner:'uid:a',qualificationId:'ap',deviceId:'local',rootPath:path,validate:(_,p)=>p,...extra});
   const rows=Array.from({length:51},(_,n)=>({id:'n'+String(n).padStart(3,'0'),kind:'note',version:2,revision:1,deviceId:'remote',operationId:'op'+n,payload:{n}}));
   const transport=()=>{const read=[];return {read,pullDocuments:async(uid,q,cursor)=>{const start=cursor?Number(cursor.id.slice(1))+1:0,page=rows.slice(start,start+25);read.push(page.length);return {rows:page,cursor:page.length?{seconds:10,nanoseconds:1,id:page.at(-1).id}:cursor,more:page.length===25};},pushDocument:async()=>{throw Error('unexpected upload');}};};
   async function sync(store,remote){const engine=createWorkspaceSync({uid:'a',qualificationId:'ap',store,remote});await engine.run();engine.stop();}
   let store=make('/cursor-reload/'),remote=transport();await sync(store,remote);assert((await store.read()).length===51,'first page count');assert((await store.cursor()).id==='n050','first cursor');await store.close();
   store=make('/cursor-reload/');remote=transport();await sync(store,remote);assert(remote.read.length===1&&remote.read[0]===0,'restart downloaded the whole collection');assert((await store.read()).length===51,'restart lost rows');await store.close();
   store=make('/cursor-failure/');const merge=store.merge;store.merge=async row=>{if(row.id==='n030')throw Error('synthetic document write failure');return merge(row);};await sync(store,transport());assert((await store.cursor()).id==='n024','cursor advanced past failed page');assert((await store.read()).length===30,'failure fixture');await store.close();
   store=make('/cursor-failure/');remote=transport();await sync(store,remote);assert(remote.read.reduce((a,b)=>a+b,0)===26,'retry skipped/repeated committed page');assert((await store.read()).length===51,'retry lost rows');await store.close();
   store=make('/cursor-quota/');const put=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...a){if(this.name==='checkpoints')throw new DOMException('synthetic cursor quota','QuotaExceededError');return put.apply(this,a);};try{await sync(store,transport());}finally{IDBObjectStore.prototype.put=put;}assert(await store.cursor()===null,'failed cursor write committed');assert((await store.read()).length===25,'cursor failure lost committed documents');await store.close();
   store=make('/cursor-quota/');await sync(store,transport());assert((await store.read()).length===51,'cursor failure retry lost rows');await store.close();
   store=make('/cursor-conflict/');await store.write('note','n030',{n:'local'},0);await sync(store,transport());let conflict=(await store.read()).find(r=>r.id==='n030');assert(conflict.payload.n==='local'&&conflict.conflict.payload.n===30,'conflict not durable');assert((await store.cursor()).id==='n050','conflict cursor');await store.close();store=make('/cursor-conflict/');await store.resolve('n030',false);assert((await store.read()).find(r=>r.id==='n030').payload.n===30,'conflict could not resolve after restart');await store.close();
   const path='/cursor-isolation/',a=make(path),c=make(path),high={seconds:20,nanoseconds:2,id:'z'};await Promise.all([a.setCursor(high),c.setCursor({seconds:10,nanoseconds:1,id:'a'})]);assert((await a.cursor()).seconds===20,'stale tab moved cursor back');await c.setCursor({seconds:20,nanoseconds:2,id:'a'});assert((await a.cursor()).id==='z','same timestamp id regressed');await c.setCursor({seconds:20,nanoseconds:2,id:'\\u{10000}'});await a.setCursor({seconds:20,nanoseconds:2,id:'\\uE000'});assert((await a.cursor()).id==='\\u{10000}','Firestore UTF-8 ordering');assert((await a.read()).length===0,'cursor leaked into learning records');
   for(const extra of [{owner:'uid:b'},{qualificationId:'fp2'},{namespaceName:'written'}]){const other=make(path,extra);assert(await other.cursor()===null,'cursor scope leak');await other.close();}
   let invalid=false;try{await a.setCursor({seconds:1,nanoseconds:1e9,id:'x'});}catch{invalid=true;}assert(invalid&&(await a.cursor()).seconds===20,'invalid cursor changed metadata');await a.close();await c.close();
   const local=createLocalStore({qualificationId:'ap',owner:'uid:a',rootPath:path});await local.learningStore().setCursor(high);assert(await local.cursor()===null,'learning cursor mixed with attempts');await local.close();const reopened=createLocalStore({qualificationId:'ap',owner:'uid:a',rootPath:path});assert((await reopened.learningStore().cursor()).id==='z','learning cursor not durable');await reopened.close();
   return {firstDownload:51,restartDownload:0,retryAfterPageFailure:26,documentFailure:true,cursorFailure:true,conflictRecovery:true,staleTabs:true,scopeIsolation:true,learningCursor:true};
  }''');b.close()
finally:server.shutdown()
print('PASS durable cursors / page and cursor failures / conflict recovery / stale tabs / UID, qualification, namespace isolation / learning store:',result)
