import json,shutil,tempfile,threading,time
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];ART=Path(tempfile.mkdtemp(prefix='hitomon-system-review-'))
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/blank':
   self.send_response(200);self.end_headers();self.wfile.write(b'<html><body></body></html>');return
  if self.path=='/assets/review-slow.png':
   time.sleep(1.5);self.send_response(200);self.end_headers();self.wfile.write(b'network');return
  return super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_port}/'
result={}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context();pg=ctx.new_page();pg.goto(BASE+'blank')
  result['workspaceCursor']=pg.evaluate("""async()=>{const {createWorkspaceStore}=await import('/src/storage/workspace.js');const s=createWorkspaceStore({owner:'uid:audit',qualificationId:'ap',deviceId:'audit',rootPath:'/probe/',validate:(k,p)=>p});const out={cursor:typeof s.cursor,setCursor:typeof s.setCursor};await s.close();return out;}""")
  ap=json.loads((ROOT/'content/ap/written-cases.json').read_text());fp=json.loads((ROOT/'content/fp2/practical-cases.json').read_text())
  result['bodyReferences']=pg.evaluate("""async cases=>{const {caseBodyHTML}=await import('/src/ui/case-body.js');const missing=[];for(const c of cases){const root=document.createElement('div');root.innerHTML=caseBodyHTML(c,document.baseURI);for(const [key,ref] of Object.entries(c.bodyRefs||{})){if(![...root.querySelectorAll('[id]')].some(e=>e.id==='written-ref-'+key))missing.push({caseId:c.id,key,text:ref.text||ref.anchor,firstLinks:c.items.filter(i=>i.bodyRefs?.[0]===key).map(i=>i.id)});}}return missing;}""",ap+fp)
  result['sharedLabel']=pg.evaluate("""async()=>{const {syncLabels}=await import('/src/domain/sync-status.js');return {written:syncLabels.written};}""")
  awaitworker="""async()=>{const r=await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener('controllerchange',ok,{once:true}));await(await caches.open('hitomon-/images')).put(new URL('assets/review-slow.png',location.origin).href,new Response('saved'));const start=performance.now(),body=await(await fetch('/assets/review-slow.png')).text();return {elapsedMs:Math.round(performance.now()-start),body};}"""
  result['cachedImageNetworkWait']=pg.evaluate(awaitworker)
  ctx.close()
  # Real account controller with a failed local Auth sign-out; no production login.
  ctx=b.new_context(service_workers='block');pg=ctx.new_page();pg.route('**/src/sync/firebase.js',lambda route:route.fulfill(content_type='text/javascript',body="""export function createFirebaseClient(){return {observe:cb=>{window.auditObserve=cb;queueMicrotask(()=>cb({uid:'audit',email:'test@example.invalid'}));},logout:async()=>{throw new Error('Synthetic Auth persistence failure');},pull:async()=>{window.auditPulls=(window.auditPulls||0)+1;return {rows:[],cursor:null,more:false};},push:async()=> 'ack'};}"""));pg.goto(BASE+'blank')
  result['logoutFailure']=pg.evaluate("""async()=>{document.body.innerHTML=['google-login','google-logout','sync-now','import-guest'].map(id=>'<button id="'+id+'"></button>').join('')+'<p id="sync-state"></p><span id="account-name"></span>';const {initAccountControls}=await import('/src/sync/account.js');const store={cursor:async()=>null,pending:async()=>[],mergeRemote:async()=>[],identity:async()=>({owner:'uid:audit',deviceId:'audit'})};const control=await initAccountControls({qualificationId:'ap',getStore:()=>store,switchOwner:async()=>{},importGuest:async()=>{},validateAttempt:()=>{},onRecords:()=>{}});await control.ready;await new Promise(r=>setTimeout(r,30));const before=window.auditPulls;document.getElementById('google-logout').click();await new Promise(r=>setTimeout(r,30));document.getElementById('sync-now').click();await new Promise(r=>setTimeout(r,30));return {pullsBefore:before,pullsAfterManualRefresh:window.auditPulls,owner:control.owner(),message:document.getElementById('sync-state').textContent,logoutVisible:!document.getElementById('google-logout').hidden};}""")
  b.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2));print('Artifacts:',ART)
