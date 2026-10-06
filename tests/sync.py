"""Real Firebase SDK + Auth popup/Firestore Emulator in independent browsers."""
import json
import os
import shutil
import time
from playwright.sync_api import sync_playwright
from browser_storage import wait_for_async

URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/')+'?firebase-emulator=1'
READ='''async()=>{
 const root=new URL('.',document.baseURI),sdk=await import(new URL('assets/vendor/firebase.js',root));
 const user=sdk.getAuth().currentUser,{createLocalStore}=await import(new URL('src/storage/local.js',root));
 const store=createLocalStore({qualificationId:'ap',rootPath:root.pathname,owner:user?`uid:${user.uid}`:undefined});
 try{return {state:JSON.parse(await store.snapshot()),pending:await store.pending(),identity:await store.identity(),cursor:await store.cursor()};}finally{await store.close();}
}'''
def state(page):
    page.wait_for_function('document.getElementById("save-state").textContent!=="保存中…" && !document.getElementById("main").inert')
    return page.evaluate(READ)

def settings(page):
    if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()

def close_settings(page):
    if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる').click()

def login(page,email):
    settings(page);page.wait_for_function('!document.getElementById("google-login").disabled')
    with page.expect_popup() as event:page.locator('#google-login').click()
    popup=event.value;popup.wait_for_url('**/emulator/auth/handler?**');popup.locator('body').wait_for();popup.get_by_text('Sign-in with Google.com',exact=True).wait_for()
    existing=popup.get_by_text(email,exact=True)
    if existing.count():existing.click()
    else:
        popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill(email.split('@')[0]);popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
    page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled')
    synced(page)

def synced(page):
    settings(page);page.locator('#sync-now').click()
    try:page.wait_for_function('document.getElementById("sync-state").textContent==="同期済み"',timeout=30000)
    except Exception:
        print('SYNC STATUS',page.locator('#sync-state').inner_text(),flush=True);print('PENDING',[(i['id'],i['revision'],i['payload']['status']) for i in state(page)['pending']],flush=True);raise
    wait_for_async(page,'async()=>!(await ('+READ+')()).pending.length')
    close_settings(page)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
    contexts=[browser.new_context(viewport={'width':390,'height':844}) for _ in range(3)]
    first,second,third=[c.new_page() for c in contexts];errors=[]
    for page in [first,second,third]:
        page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:print(m.text,flush=True) if m.text.startswith('Study sync failed') else None);page.goto(URL);page.locator('.quick-start').wait_for()
    email=f'sync-{time.time_ns()}@example.test'
    # Guest data is not silently adopted; explicit repeated import is idempotent.
    first.locator('[data-action=start-session][data-count="1"]').click();first.locator('[data-action=hint]').click();first.get_by_role('radio').first.check();guest=state(first);guest_id=guest['state']['currentId']
    first.locator('[data-action=pause]').click();login(first,email);assert not state(first)['state']['attempts']
    twin=contexts[0].new_page();twin.goto(URL);twin.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("import-guest").disabled');assert not state(twin)['state']['attempts']
    settings(first);settings(twin);first.once('dialog',lambda d:d.accept());twin.once('dialog',lambda d:d.accept());first.locator('#import-guest').click();twin.locator('#import-guest').click();first.wait_for_function('!document.getElementById("import-guest").disabled');twin.wait_for_function('!document.getElementById("import-guest").disabled');synced(first);synced(twin);assert len(state(twin)['state']['attempts'])==1;twin.close()
    imported=state(first);assert len(imported['state']['attempts'])==1 and imported['state']['attempts'][0]['id']!=guest_id
    settings(first);first.once('dialog',lambda d:d.accept());first.locator('#import-guest').click();first.wait_for_function('!document.getElementById("import-guest").disabled');synced(first);assert len(state(first)['state']['attempts'])==1
    print('PASS Google popup in Auth Emulator / explicit guest adoption / concurrent and repeated import without duplicates',flush=True)
    # Download hint and selected choice in a separate browser; resume forks.
    login(second,email);imported_id=imported['state']['attempts'][0]['id'];download=state(second)['state'];assert download['attempts'][0]['hintCount']==1 and download['attempts'][0]['selected']==0
    first.locator('[data-action=resume]').first.click();second.locator('[data-action=resume]').first.click();s1=state(first)['state'];s2=state(second)['state'];a1=next(a for a in s1['attempts'] if a['id']==s1['currentId']);a2=next(a for a in s2['attempts'] if a['id']==s2['currentId'])
    assert a1['id']!=a2['id'] and a2['continuationOf']==imported_id
    answer=a1['questionSnapshot']['answer'];first.get_by_role('radio').nth(answer).check();first.locator('[data-action=submit]').click();second.get_by_role('radio').nth((answer+1)%4).check();second.locator('[data-action=submit]').click();synced(first);synced(second);synced(first)
    history=state(first)['state']['attempts'];assert {a['status'] for a in history if a['completedAt']}=={'assisted','incorrect'}
    assert len([a for a in history if a['completedAt']])==2
    print('PASS two browsers / selected choice and hint checkpoint / concurrent continuation keeps both answers',flush=True)
    # Post-answer hints on a downloaded completed attempt merge without another grade.
    second.locator('.sidebar [data-view=history]').click();correct=[a for a in history if a['status']=='assisted'][0]
    second.locator('[data-action=resume][data-id="'+correct['id']+'"]').click();second.locator('[data-action=hint]').click();synced(second);synced(first)
    history=state(first)['state']['attempts'];assert len([a for a in history if a['completedAt']])==2
    assert next(a for a in history if a['id']==correct['id'])['hintCount']==2
    print('PASS another device opens post-answer hint / original grading retained / no duplicate completion',flush=True)
    # Offline SDK initialization, local answer/outbox, reload, automatic/manual retry.
    first.locator('.sidebar [data-view=home]').click();first.locator('[data-action=start-session][data-count="1"]').click();first.get_by_role('radio').first.wait_for();first.evaluate('async()=>await navigator.serviceWorker.ready')
    contexts[0].set_offline(True);first.locator('[data-action=hint]').click();first.get_by_role('radio').first.check();first.locator('[data-action=submit]').click();offline=state(first);assert offline['pending']
    first.reload();first.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+')');first.locator('#result-heading').wait_for();assert state(first)['pending'] and state(first)['state']['currentId']==offline['state']['currentId']
    contexts[0].set_offline(False);synced(first);synced(second);assert len([a for a in state(second)['state']['attempts'] if a['completedAt']])==3
    print('PASS offline answer/hints / reload / durable pending queue / replay without duplicate',flush=True)
    # Log out restores the guest; another UID has no old records/outbox.
    first.locator('.sidebar [data-view=home]').click();first.locator('[data-action=start-session][data-count="1"]').click();first.get_by_role('radio').first.wait_for();contexts[0].set_offline(True);first.locator('[data-action=hint]').click();pending_owner=state(first);assert pending_owner['pending']
    settings(first);first.locator('#google-logout').click();first.wait_for_function('!document.getElementById("google-login").hidden && !document.getElementById("google-login").disabled');assert state(first)['state']['attempts'][0]['id']==guest_id
    contexts[0].set_offline(False)
    login(first,'other-'+email);assert state(first)['state']['attempts']==[] and state(first)['pending']==[]
    remaining=first.evaluate('''async owner=>{const {createLocalStore}=await import('./src/storage/local.js');const store=createLocalStore({qualificationId:'ap',rootPath:new URL('.',document.baseURI).pathname,owner});try{return await store.pending();}finally{await store.close();}}''',pending_owner['identity']['owner']);assert remaining
    login(third,email);assert len([a for a in state(third)['state']['attempts'] if a['completedAt']])==3
    assert third.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    assert not errors,errors
    third.screenshot(path='/workspace/scratch/firebase-sync/synced-mobile.png',full_page=True)
    print('PASS logout restores guest / UID isolation / fresh third browser / mobile viewport / no page errors',flush=True)
    for c in contexts:c.close()
    browser.close()
