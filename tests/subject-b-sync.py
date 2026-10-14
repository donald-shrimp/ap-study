"""Two independent browsers, real Firebase SDK/emulators and case CAS; no production account."""
import json,shutil,uuid
from playwright.sync_api import sync_playwright
from browser_storage import nav,wait_for_async
URL='http://127.0.0.1:4173/ap/?firebase-emulator=1'
READ='''async()=>{const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js'),s=createLocalStore({qualificationId:'ap',rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{const i=await s.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),w=createWorkspaceStore({...i,rootPath:'/',namespaceName:'written',validate:(k,p)=>p});try{return await w.read();}finally{await w.close();}}finally{await s.close();}}'''
def rows(page):return page.evaluate(READ)
def settings(page):
 if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
 if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる',exact=True).click()
def sync(page,conflict=False):
 settings(page);page.locator('#sync-now').click()
 if conflict:page.wait_for_function('document.getElementById("sync-state").dataset.written==="conflict"')
 else:wait_for_async(page,'async()=>{const rows=await ('+READ+')();return !rows.some(r=>r.dirty||r.conflict);}',timeout=30000)
 close(page)
def login(page,email):
 settings(page);page.wait_for_function('!document.getElementById("google-login").disabled')
 with page.expect_popup() as event:page.locator('#google-login').click()
 popup=event.value;popup.get_by_text('Sign-in with Google.com',exact=True).wait_for();existing=popup.get_by_text(email,exact=True)
 if existing.count():existing.click()
 else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('v2 test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');sync(page)
def target(page):page.locator('[data-action=switch-target][data-part-id=written]').click();page.locator('[data-part-id=written][aria-pressed=true]').wait_for()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[b.new_context(viewport={'width':390,'height':844}) for _ in range(2)];first,second=[c.new_page() for c in contexts];errors=[]
 for page in [first,second]:page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.goto(URL);page.locator('.quick-start').wait_for()
 # A case-only guest must expose the explicit adoption action after login.
 target(first);first.locator('[data-action=written-start]').first.click();first.locator('textarea[data-written-key]').fill('ゲストの回答');wait_for_async(first,'async()=>(await ('+READ+')())[0]?.payload.responses["q1--answer"]?.value==="ゲストの回答"');nav(first,'home');email='case-v2-'+uuid.uuid4().hex+'@example.test';login(first,email);settings(first);first.locator('#import-guest').wait_for(state='visible');first.locator('#import-guest').click();wait_for_async(first,'async()=>(await ('+READ+')()).length===1');sync(first);case_id=rows(first)[0]['id'];assert rows(first)[0]['payload']['responses']['q1--answer']['value']=='ゲストの回答'
 login(second,email);target(second);sync(second);wait_for_async(second,'async()=>(await ('+READ+')()).length===1');second.locator('[data-action=written-resume]').click();second.locator('textarea[data-written-key]').wait_for();assert second.locator('textarea[data-written-key]').input_value()=='ゲストの回答';assert rows(second)[0]['payload']['material']['version']==1
 # A foreground partial answer and pane persist to another device.
 second.locator('.written-item-nav [data-id=q3]').click();second.locator('.written-item-nav [data-id=q3][aria-current=step]').wait_for();second.locator('textarea[data-written-key]').first.fill('ロックアウト');sync(second);sync(first);first.locator('[data-action=written-resume]').click();first.locator('.written-item-nav [data-id=q3][aria-current=step]').wait_for();assert first.locator('textarea[data-written-key]').first.input_value()=='ロックアウト'
 # Both devices change the same draft; no silent last-write-wins replacement.
 first.locator('textarea[data-written-key]').first.fill('端末一の回答');wait_for_async(first,'async()=>(await ('+READ+')()).some(r=>r.dirty&&r.payload.responses["q3--setting"]?.value==="端末一の回答")');second.locator('textarea[data-written-key]').first.fill('端末二の回答');wait_for_async(second,'async()=>(await ('+READ+')()).some(r=>r.dirty&&r.payload.responses["q3--setting"]?.value==="端末二の回答")');first.locator('textarea[data-written-key]').last.fill('同時保存する理由');sync(first);sync(second,True);assert second.locator('textarea[data-written-key]').first.input_value()=='端末二の回答';nav(second,'history');second.locator('[data-action=written-fork]').click();sync(second);sync(first);wait_for_async(first,'async()=>(await ('+READ+')()).length===2');values={r['payload']['responses']['q3--setting']['value'] for r in rows(first)};assert values=={'端末一の回答','端末二の回答'},values
 # Logging out never projects account cases into the guest namespace.
 settings(second);second.locator('#google-logout').click();second.wait_for_function('document.getElementById("google-login").hidden===false && !document.getElementById("google-login").disabled');assert not rows(second)
 assert not errors,errors;b.close()
print('PASS B-only guest adoption / two browsers / partial answers + current item + fixed material / foreground input protected / CAS conflict + explicit fork retains both / guest-account separation')
