"""Real account controller with synthetic Auth/transport; no production login."""
import os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/')
STUB='''export function createFirebaseClient(){
 const page=(scope,uid)=>{window.calls.push({scope,uid});if(window.hold&&uid==='a'){window.hold=false;return new Promise(resolve=>window.releaseOld=()=>resolve({rows:[],cursor:null,more:false}));}return Promise.resolve({rows:[],cursor:null,more:false});};
 return {observe:cb=>{window.auth=cb;queueMicrotask(()=>cb({uid:'a'}));},
 logout:async()=>{if(window.scenario==='success'){window.auth(null);return;}if(window.scenario==='changed')window.auth({uid:'b'});throw new Error('Synthetic Auth persistence failure');},
 pull:uid=>page('study',uid),pullDocuments:(uid,q,c,collection='resourcesV2')=>page(collection,uid),pullLearning:uid=>page('learning',uid),pullCards:uid=>page('cards',uid),pullPersonal:uid=>page('personal',uid)};
}'''
BOOT='''async scenario=>{
 window.scenario=scenario;window.calls=[];window.messages=[];window.hold=scenario==='late';window.merges=0;
 document.body.innerHTML=['google-login','google-logout','sync-now','import-guest'].map(id=>'<button id="'+id+'">'+id+'</button>').join('')+'<p id="sync-state"></p><span id="account-name"></span>';
 const messages=new MutationObserver(()=>window.messages.push(document.getElementById('sync-state').textContent));messages.observe(document.getElementById('sync-state'),{childList:true});
 let owner='uid:a';const study={cursor:async()=>null,pending:async()=>[],mergeRemote:async()=>{window.merges++;return [];}};
 const workspace={read:async()=>[],merge:async()=>{}};
 const {initAccountControls}=await import(new URL('src/sync/account.js',location.href));
 window.control=await initAccountControls({qualificationId:'ap',getStore:()=>study,getWorkspaceStore:()=>workspace,getLearningStore:()=>workspace,getCardStore:()=>workspace,getPersonalStore:()=>workspace,getWrittenStore:()=>workspace,switchOwner:async next=>{owner=next;},importGuest:async()=>{},validateAttempt:()=>{},onRecords:()=>{}});
 await window.control.ready;
}'''
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts)
  for scenario in ['failure','late','success','changed']:
   ctx=b.new_context(service_workers='block');pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.route('**/src/sync/firebase.js',lambda r:r.fulfill(content_type='text/javascript',body=STUB));pg.route('**/lifecycle-probe',lambda r:r.fulfill(content_type='text/html',body='<html><body></body></html>'));pg.goto(BASE+'lifecycle-probe');pg.evaluate(BOOT,scenario)
   pg.wait_for_function('calls.length===6&&!document.getElementById("google-logout").disabled');pg.locator('#google-logout').click()
   if scenario in ['failure','late']:
    pg.wait_for_function('calls.length>=12&&!document.getElementById("google-logout").disabled');assert pg.evaluate('control.owner()')=='uid:a'
    assert pg.evaluate('messages.some(s=>s.includes("ログアウトできませんでした"))');assert all(c['uid']=='a' for c in pg.evaluate('calls'))
    if scenario=='late':
     before=pg.evaluate('merges');pg.evaluate('releaseOld()');pg.wait_for_timeout(30);assert pg.evaluate('merges')==before
    pg.locator('#sync-now').click();pg.wait_for_function('calls.length>=18')
    for scope in ['study','resourcesV2','learning','cards','personal','writtenV2']:assert pg.evaluate('(s)=>calls.filter(c=>c.scope===s).length',scope)>=3
   elif scenario=='success':
    pg.wait_for_function('!document.getElementById("google-login").hidden&&!document.getElementById("google-login").disabled');assert pg.evaluate('control.owner()') is None;assert pg.evaluate('calls.length')==6
   else:
    pg.wait_for_function('control.owner()==="uid:b"&&!document.getElementById("google-logout").disabled');pg.locator('#sync-now').click();pg.wait_for_function('calls.filter(c=>c.uid==="b").length>=12');assert pg.evaluate('calls.filter(c=>c.uid==="a").length')==6
   assert not errors,errors;ctx.close()
  b.close()
finally:server.shutdown()
print('PASS logout failure resumes all six scopes / manual retry / late old response ignored / success and concurrent UID change isolated')
