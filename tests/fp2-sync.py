"""Synthetic multiple-practical subjects through real Auth/Firestore emulators."""
import json,shutil,tempfile,threading,uuid
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from fp2_fixtures import prepare
from browser_storage import nav,select_target,wait_for_async
READ='''async()=>{const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js'),s=createLocalStore({qualificationId:'fp2',rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{const i=await s.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),w=createWorkspaceStore({...i,rootPath:'/',namespaceName:'written',validate:(k,p)=>p});try{return await w.read();}finally{await w.close();}}finally{await s.close();}}'''
def settings(page):
 if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
 if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる',exact=True).click()
def sync(page):
 settings(page);page.locator('#sync-now').click();wait_for_async(page,'async()=>!(await ('+READ+')()).some(r=>r.dirty||r.conflict)',timeout=30000);close(page)
def login(page,email):
 settings(page);page.wait_for_function('!document.getElementById("google-login").disabled')
 with page.expect_popup() as event:page.locator('#google-login').click()
 popup=event.value;popup.get_by_text('Sign-in with Google.com',exact=True).wait_for();existing=popup.get_by_text(email,exact=True)
 if existing.count():existing.click()
 else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('synthetic FP test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');sync(page)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
with tempfile.TemporaryDirectory(prefix='fp2-sync-root-') as d:
 root=Path(d);prepare(root);server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/fp2/?firebase-emulator=1'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[b.new_context(viewport={'width':390,'height':844}) for _ in range(2)];first,second=[c.new_page() for c in contexts];errors=[]
   for pg in [first,second]:pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(url);pg.locator('.quick-start').wait_for()
   email='synthetic-fp2-'+uuid.uuid4().hex+'@example.test';login(first,email);select_target(first,'jafp-practical','fp2');first.locator('[data-action=written-start]').first.click();first.locator('input[data-written-key="q1--amount"]').fill('１４９００００');sync(first)
   select_target(first,'kinzai-personal','fp2');first.locator('[data-action=written-start]').first.click();first.locator('input[data-written-key="q1--amount"]').fill('7');sync(first);nav(first,'history')
   login(second,email);select_target(second,'jafp-practical','fp2');sync(second);second.locator('.study-entry [data-action=written-resume]').click();second.locator('input[data-written-key="q1--amount"]').wait_for();assert second.locator('input[data-written-key="q1--amount"]').input_value()=='１４９００００';second.locator('[data-action=written-submit][data-written-key="q1--amount"]').click();second.locator('input[data-written-key="q1--amount"][readonly]').wait_for();sync(second)
   rows=second.evaluate(READ);assert len(rows)==2;assert all(r['payload']['material']['sourceRecord']['legalAsOf']=='2026-04-01' for r in rows);assert next(r for r in rows if r['payload']['examPartId']=='jafp-practical')['payload']['evaluations']['q1--amount']['outcome']=='correct'
   assert 'synthetic-a' not in first.locator('#main').inner_text();select_target(second,'kinzai-personal','fp2');second.locator('.study-entry [data-action=written-resume]').click();second.locator('input[data-written-key="q1--amount"]').fill('8');sync(second)
   sync(first);first.locator('[data-action=written-resume]').first.click();first.locator('input[data-written-key="q1--amount"]').wait_for();assert first.locator('input[data-written-key="q1--amount"]').input_value()=='8';first.locator('[data-action=written-submit]').click();first.locator('input[readonly]').wait_for();sync(first);select_target(first,'jafp-practical','fp2');first.locator('.study-entry [data-action=written-resume]').click();assert first.locator('input[data-written-key="q1--amount"][readonly]').input_value()=='１４９００００'
   sync(second);rows=second.evaluate(READ);assert next(r for r in rows if r['payload']['examPartId']=='kinzai-personal')['payload']['evaluations']['q1--amount']['outcome']=='incorrect';assert not errors,errors;b.close()
 finally:server.shutdown()
print('PASS synthetic FP two-device sync / partial numeric values and exact assessment / legal basis retained / practical subjects and histories isolated / no production account')
