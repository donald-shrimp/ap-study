"""Real Auth restore: no guest/home flash, including slow local Auth and offline reload.
Run Auth on9099 and Firestore with this repo's Rules on8082 (override via env).
Only the test server changes the emulator port and delays the SDK's real callback.
"""
import functools,json,os,shutil,tempfile,threading,uuid
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
from browser_storage import nav,select_target,wait_for_async
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-startup-'))
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if urlparse(self.path).path=='/src/sync/firebase.js':
   source=(ROOT/'src/sync/firebase.js').read_text().replace("'127.0.0.1',8080", "'127.0.0.1',"+os.getenv('HITOMON_TEST_FIRESTORE_PORT','8082'))
   source=source.replace('sdk.onAuthStateChanged(auth,callback)',"sdk.onAuthStateChanged(auth,next=>setTimeout(()=>callback(next),Number(sessionStorage.getItem('test-auth-delay')||0)))")
   raw=source.encode();self.send_response(200);self.send_header('Content-Type','text/javascript');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{server.server_port}/ap/?firebase-emulator=1'
TRACE='''(()=>{window.startupFrames=[];new MutationObserver(()=>{const m=document.getElementById('main');if(!m)return;const view=m.querySelector('.loading')?'loading':m.querySelector('.quick-start,.study-entry')?'home':m.querySelector('.written-layout')?'written':m.querySelector('.question-panel')?'study':m.querySelector('.flashcard')?'cards':m.querySelector('.diagnostic-question')?'diagnostic':m.querySelector('h1')?.textContent||'other';if(startupFrames.at(-1)!==view)startupFrames.push(view);}).observe(document,{childList:true,subtree:true});})()'''
READ='''async()=>{const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js'),s=createLocalStore({qualificationId:document.documentElement.dataset.qualification,rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{return JSON.parse(await s.snapshot());}finally{await s.close();}}'''
def settings(p):
 if not p.locator('#settings-dialog').evaluate('(d)=>d.open'):p.locator('#settings-button').click()
def close(p):
 if p.locator('#settings-dialog').evaluate('(d)=>d.open'):p.get_by_role('button',name='設定を閉じる',exact=True).click()
def login(p,email):
 settings(p);p.wait_for_function('!document.getElementById("google-login").disabled')
 with p.expect_popup() as event:p.locator('#google-login').click()
 popup=event.value;popup.get_by_text('Sign-in with Google.com',exact=True).wait_for()
 if popup.get_by_text(email,exact=True).count():popup.get_by_text(email,exact=True).click()
 else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('Startup test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 p.wait_for_function('!document.getElementById("google-logout").disabled && !document.getElementById("google-logout").hidden');close(p)
def ready(p):p.wait_for_function('document.getElementById("main").getAttribute("aria-busy")==="false" && !document.getElementById("main").inert')
def reload(p,selector,expected):
 p.evaluate("sessionStorage.setItem('test-auth-delay','1200')");p.reload(wait_until='domcontentloaded');expect(p.locator('#main .loading')).to_have_text('ひと問を読み込んでいます。');assert p.locator('#main').evaluate('(m)=>m.inert');assert p.locator('#settings-button').is_disabled();p.locator(selector).wait_for();ready(p);frames=p.evaluate('startupFrames');assert frames[0]=='loading' and frames[1:]==[expected],frames
 print('PASS delayed Auth reload:',expected,frames,flush=True)
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':390,'height':844});ctx.add_init_script(TRACE);p=ctx.new_page();p.set_default_timeout(45000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.accept());p.goto(URL);p.locator('.quick-start').wait_for();ready(p)
  # Guest resume is also direct, and ordinary foreground return does not navigate.
  p.locator('.study-entrance[data-paper-mode=all]').click();p.locator('.question-panel').wait_for();p.get_by_role('radio').first.check();p.locator('[data-action=hint]').click();reload(p,'.question-panel','study');assert p.get_by_role('radio').first.is_checked();guest=p.evaluate(READ);assert guest['currentId'];p.evaluate("document.dispatchEvent(new Event('visibilitychange'))");assert p.locator('.question-panel').count()==1
  nav(p,'home');login(p,'startup-'+uuid.uuid4().hex+'@example.test');assert not p.evaluate(READ)['attempts']
  p.locator('.study-entrance[data-paper-mode=all]').click();p.locator('.question-panel').wait_for();p.get_by_role('radio').first.check();p.locator('[data-action=submit]').click();p.locator('#result-heading').wait_for();before=p.evaluate(READ);reload(p,'#result-heading','study');after=p.evaluate(READ);assert before['currentId']==after['currentId'] and before['attempts']==after['attempts']
  # Cached Auth and records must work offline; no waiting for Firestore.
  p.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener("controllerchange",ok,{once:true}));}');ctx.set_offline(True);reload(p,'#result-heading','study');assert p.evaluate(READ)['currentId']==before['currentId'];ctx.set_offline(False)
  nav(p,'history');reload(p,'.answer-history','学習記録')
  nav(p,'home');reload(p,'.quick-start','home')
  p.get_by_role('button',name='単語帳',exact=True).click();p.locator('.flashcard').wait_for();reload(p,'.flashcard','cards')
  select_target(p,'written');p.locator('.study-entry [data-action=written-start]').click();p.locator('.written-layout').wait_for();p.locator('textarea[data-written-key]').fill('復元する記述回答');p.locator('[data-action=written-submit]').click();reload(p,'.written-layout','written');assert p.locator('textarea[data-written-key]').input_value()=='復元する記述回答';p.screenshot(path=str(ART/'written-restored.png'))
  # A deliberate chooser entry stays home, rather than reopening a checkpoint.
  p.goto(URL+'&part=written&entry=home');p.locator('.study-entry').wait_for();ready(p);assert p.evaluate('startupFrames')==['loading','home'];assert p.locator('[data-action=written-resume]').count()==1
  # If the account checkpoint cannot be read, show an error instead of guest home.
  ctx.add_init_script('''(()=>{const get=IDBObjectStore.prototype.get;IDBObjectStore.prototype.get=function(key){if(this.name==='meta'&&String(key).startsWith('uid:')&&sessionStorage.getItem('test-fail-owner'))throw new Error('Synthetic account read failure');return get.call(this,key);};})()''')
  p.evaluate("sessionStorage.setItem('test-fail-owner','1')");p.reload();p.get_by_role('heading',name='ひと問を読み込めませんでした。',exact=True).wait_for();ready(p);assert p.evaluate('startupFrames')==['loading','ひと問を読み込めませんでした。'];p.evaluate("sessionStorage.removeItem('test-fail-owner')");p.reload();p.locator('.study-entry [data-action=written-resume]').wait_for();ready(p)
  settings(p);p.locator('#google-logout').click();p.wait_for_function('!document.getElementById("google-login").hidden && !document.getElementById("google-login").disabled');close(p);assert not p.locator('.written-layout').count();select_target(p,'objective');assert p.evaluate(READ)['attempts'][0]['id']==guest['attempts'][0]['id']
  # A missing optional login module still permits guest learning, with no hang.
  fallback=b.new_context(service_workers='block');fallback.add_init_script(TRACE);q=fallback.new_page();q.route('**/src/sync/firebase.js',lambda route:route.abort());q.goto(URL);q.locator('.quick-start').wait_for();ready(q);assert q.locator('#google-login').is_disabled();assert q.evaluate('startupFrames')==['loading','home'];fallback.close()
  assert not errors,errors;ctx.close();b.close()
 print('PASS real Auth guest/account isolation / A selection+hints+result / history+home+cards / B input / explicit home entry / offline / no intermediate screen or page errors; artifacts:',ART)
finally:server.shutdown();server.server_close()
