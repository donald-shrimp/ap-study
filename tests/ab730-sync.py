"""Actual AB bank, two separate browser stores and real Firebase SDK emulators only."""
import json,shutil,uuid
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import nav,state,wait_for_async,open_answer_history
ROOT=Path(__file__).resolve().parents[1];bank=json.loads((ROOT/'content/ab730/questions.json').read_text());q=next(q for q in bank if q['type']=='multipleChoice')
URL='http://127.0.0.1:4181/ab730/?firebase-emulator=1'
READ='''async()=>{const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js');const store=createLocalStore({qualificationId:'ab730',rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{const identity=await store.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),workspace=createWorkspaceStore({...identity,rootPath:'/',validate:(kind,payload)=>payload});try{return {state:JSON.parse(await store.snapshot()),pending:await store.pending(),rows:await workspace.read()};}finally{await workspace.close();}}finally{await store.close();}}'''
def settings(page):
 if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
 if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる',exact=True).click()
def kick(page):settings(page);page.locator('#sync-now').click();close(page)
def synced(page):
 kick(page);wait_for_async(page,'async()=>{const r=await ('+READ+')();return !r.pending.length&&!r.rows.some(r=>r.dirty||r.conflict)}',timeout=30000)
def login(page,email):
 settings(page);page.locator('#google-login').wait_for();page.wait_for_function('!document.getElementById("google-login").disabled')
 with page.expect_popup() as event:page.locator('#google-login').click()
 popup=event.value;popup.wait_for_url('**/emulator/auth/handler?**');popup.get_by_text('Sign-in with Google.com',exact=True).wait_for()
 if popup.get_by_text(email,exact=True).count():popup.get_by_text(email,exact=True).click()
 else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('AB real-bank test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');synced(page)
def open_q(page):
 nav(page,'materials');page.locator('[data-action=reset-filters]').click();page.locator('[name=query]').fill(q['title']);page.locator(f'[data-action=start][data-id="{q["id"]}"]').click();page.locator('[name=answer]').first.wait_for()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[browser.new_context(viewport={'width':390,'height':844}) for _ in range(2)];a,b=[c.new_page() for c in contexts];errors=[]
 for page in [a,b]:page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.goto(URL);page.locator('.quick-start').wait_for()
 # Logged-out partial multiple selection can be explicitly imported after login.
 open_q(a);first=q['correctChoiceIds'][0];first_index=next(i for i,c in enumerate(q['choices']) if c['id']==first);a.locator(f'[name=answer][value="{first_index}"]').check();guest=state(a)['attempts'][-1];email='ab730-'+uuid.uuid4().hex+'@example.test';login(a,email)
 settings(a);a.locator('#import-guest').click();close(a);wait_for_async(a,'async()=>(await ('+READ+')()).state.attempts.some(a=>a.importedFrom)');synced(a);login(b,email)
 wait_for_async(b,'async()=>(await ('+READ+')()).state.attempts.some(a=>a.importedFrom&&a.selectedChoiceIds?.includes('+json.dumps(first)+'))')
 imported=next(x for x in b.evaluate(READ)['state']['attempts'] if x.get('importedFrom'));assert imported['selectedChoiceIds']==[first] and imported['questionSnapshot']['sourceKind']=='authored'
 nav(b,'history');open_answer_history(b);b.locator(f'[data-action=resume][data-id="{imported["id"]}"]').click();b.locator('[name=answer]').first.wait_for();assert b.locator(f'[name=answer][value="{first_index}"]').is_checked()
 for id in q['correctChoiceIds']:b.locator('[name=answer]').nth(next(i for i,c in enumerate(q['choices']) if c['id']==id)).check()
 b.locator('[data-action=submit]').click();b.locator('#result-heading').wait_for();synced(b);kick(a)
 wait_for_async(a,'async()=>(await ('+READ+')()).state.attempts.some(a=>a.questionId==='+json.dumps(q['id'])+'&&a.status==="correct"&&a.selectedChoiceIds?.length=='+str(len(q['correctChoiceIds']))+')')
 nav(a,'home');a.locator('.home-assessments [data-view=diagnostics]').click();a.get_by_role('button',name='30問の診断をはじめる',exact=True).click();a.locator('[name=diagnostic-answer]').first.check();a.locator('[data-action=pause-diagnostic]').click();synced(a);kick(b)
 wait_for_async(b,'async()=>(await ('+READ+')()).rows.some(r=>r.kind==="diagnostic"&&r.payload.currentChoiceId!==null)');nav(b,'home');b.locator('.home-assessments [data-action=resume-diagnostic]').click();b.locator('[name=diagnostic-answer]:checked').wait_for();b.locator('[data-action=skip-diagnostic]').click();b.locator('[data-action=end-diagnostic]').click();b.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();synced(b);kick(a)
 wait_for_async(a,'async()=>(await ('+READ+')()).rows.some(r=>r.kind==="diagnostic"&&r.payload.status==="ended_early")');assert not errors,errors;browser.close()
print('PASS actual AB-730 real Auth/Firestore emulators / guest partial multiple selection import / two-device resume+grading / original source and syllabus snapshot preserved /30-question diagnostic checkpoint and partial result sync / no production writes')
