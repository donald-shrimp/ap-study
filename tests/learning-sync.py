"""Real SDK/Firestore two-browser test of mutable preferences and immutable answers."""
from pathlib import Path
import json,os,shutil,time,subprocess
from playwright.sync_api import sync_playwright
from browser_storage import nav,wait_for_async
ROOT=Path(__file__).resolve().parents[1]
# Use the existing real Auth Emulator helpers, without running their scenarios.
exec(compile((ROOT/'tests/sync.py').read_text().split('with sync_playwright() as p:')[0],str(ROOT/'tests/sync.py'),'exec'))
BASE_READ=READ
LEARNING='''async()=>{const root=new URL('.',document.baseURI),sdk=await import(new URL('assets/vendor/firebase.js',root)),{createLocalStore}=await import(new URL('src/storage/local.js',root));const s=createLocalStore({qualificationId:'ap',rootPath:root.pathname,owner:sdk.getAuth().currentUser?'uid:'+sdk.getAuth().currentUser.uid:undefined});try{return await s.learningStore().read();}finally{await s.close();}}'''
def all_synced(page):
 settings(page);page.locator('#sync-now').click();page.wait_for_function('document.getElementById("sync-state").textContent==="同期済み" && document.getElementById("learning-sync-state").textContent==="学習設定も同期済み。"',timeout=30000);close_settings(page)
def active(page):
 s=state(page)['state'];return next(a for a in s['attempts'] if a['id']==s['currentId'])
def field(page,topic='network',mode='paperless'):
 nav(page,'topics');page.locator(f'[data-action=paper-mode][data-mode={mode}]').click();page.locator(f'[data-mode={mode}][aria-pressed=true]').wait_for();page.locator(f'#field-{topic} [data-action=field-practice]').click();page.get_by_role('button',name='回答する',exact=True).wait_for()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);mobile=b.new_context(viewport={'width':390,'height':844});desktop=b.new_context(viewport={'width':1280,'height':900});m=mobile.new_page();d=desktop.new_page();errors=[]
 for pg in [m,d]:pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL);pg.locator('.study-entrance').first.wait_for()
 email=f'learning-{time.time_ns()}@example.test';login(m,email);all_synced(m);login(d,email);all_synced(d)
 field(d,'security');d.get_by_role('radio').last.check();open_pc=active(d)
 field(m);m.get_by_role('radio').first.check();m.locator('[data-action=hint]').click();original=active(m);m.locator('[data-action=desk-later]').click();all_synced(m);all_synced(d)
 assert active(d)['id']==open_pc['id'] and active(d)['selected']==open_pc['selected']
 assert original['questionId'] in state(d)['state']['settings']['deskQuestionIds']
 d.locator('[data-action=pause]').click();button=d.locator('.study-entrance[data-paper-mode=desk]');assert button.get_attribute('data-id')==original['id'];button.click();d.get_by_role('button',name='回答する',exact=True).wait_for();fork=active(d)
 assert fork['id']!=original['id'] and fork['continuationOf']==original['id'];assert fork['entryMode']=='desk' and fork['practiceScope']['topicId']=='network';assert fork['hintCount']==1 and fork['selected']==0
 d.get_by_role('radio').nth(fork['questionSnapshot']['answer']).check();d.locator('[data-action=submit]').click();all_synced(d);all_synced(m)
 assert next(a for a in state(m)['state']['attempts'] if a['id']==fork['id'])['status']=='assisted'
 d.locator('[data-action=hint]').click();all_synced(d);all_synced(m);assert next(a for a in state(m)['state']['attempts'] if a['id']==fork['id'])['hintsBeforeAnswer']==1
 print('PASS mobile desk designation -> PC field/mode/answer/hints resume; UUID continuation; current PC question unchanged; final answer frozen',flush=True)
 # Offline releases remain durable, and the old browser cannot resurrect them.
 nav(d,'home');d.locator('.desk-preferences > summary').click();d.locator('[data-action=clear-desk]').click();all_synced(d);all_synced(m);assert original['questionId'] not in state(m)['state']['settings']['deskQuestionIds']
 field(m,'database','all');deferred=active(m);m.locator('[data-action=postpone]').click();all_synced(m);all_synced(d)
 assert next(a for a in state(d)['state']['attempts'] if a['id']==deferred['id'])['deferred'] is True
 mobile.set_offline(True);nav(d,'review');d.locator(f'[data-action=resume][data-id="{deferred["id"]}"]').click();d.get_by_role('button',name='回答する',exact=True).wait_for();assert active(d)['deferred'] is False;d.locator('[data-action=pause]').click();all_synced(d)
 mobile.set_offline(False);all_synced(m);assert deferred['questionId'] not in state(m)['state']['session'].get('excludedQuestionIds',[]);assert not any(a.get('deferred') for a in state(m)['state']['attempts'] if a['questionId']==deferred['questionId'])
 print('PASS paper designation release; per-question deferral; explicit remote resume clears parent and current-session exclusion; reconnect does not resurrect',flush=True)
 # The main state and learning outbox must commit in one IndexedDB transaction.
 atomic=m.evaluate('''async()=>{const root=new URL('.',document.baseURI),sdk=await import(new URL('assets/vendor/firebase.js',root)),{createLocalStore}=await import(new URL('src/storage/local.js',root));const s=createLocalStore({qualificationId:'ap',rootPath:root.pathname,owner:'uid:'+sdk.getAuth().currentUser.uid});try{const before=await s.snapshot(),value=JSON.parse(before),rows=await s.learningStore().read(),row=rows.find(r=>r.kind==='desk');value.settings.deskQuestionIds.push('atomic-test');try{await s.write(value,{learningOperations:[{id:row.id,kind:row.kind,payload:{...row.payload,value:!row.payload.value},expectedLocalRevision:-1}]});return false;}catch{}return before===await s.snapshot();}finally{await s.close();}}''');assert atomic
 assert not errors,errors;b.close()
print('PASS atomic preference/result local commit rollback / isolated SDK browsers')
