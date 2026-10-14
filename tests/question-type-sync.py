"""Private mixed-format fixture + real SDK/Auth/Firestore emulators in two browsers."""
import copy,json,shutil,tempfile,threading,uuid
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from common_fixtures import prepare,builder,write,review
from browser_storage import nav,wait_for_async
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
READ='''async()=>{const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js');const store=createLocalStore({qualificationId:'fixture',rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{const identity=await store.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),workspace=createWorkspaceStore({...identity,rootPath:'/',validate:(kind,payload)=>payload});try{return {state:JSON.parse(await store.snapshot()),pending:await store.pending(),rows:await workspace.read()};}finally{await workspace.close();}}finally{await store.close();}}'''
def settings(page):
    if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
    if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる',exact=True).click()
def kick(page):settings(page);page.locator('#sync-now').click();close(page)
def synced(page):
    kick(page);wait_for_async(page,'async()=>{const r=await ('+READ+')();return !r.pending.length&&!r.rows.some(r=>r.dirty||r.conflict)}',timeout=20000)
def login(page,email):
    settings(page);page.locator('#google-login').wait_for();page.wait_for_function('!document.getElementById("google-login").disabled')
    with page.expect_popup() as event:page.locator('#google-login').click()
    popup=event.value;popup.wait_for_url('**/emulator/auth/handler?**');popup.get_by_text('Sign-in with Google.com',exact=True).wait_for()
    if popup.get_by_text(email,exact=True).count():popup.get_by_text(email,exact=True).click()
    else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('Typed test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
    page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');synced(page)
def multi(q):
    q=copy.deepcopy(q);q.pop('correctChoiceId');q.update(type='multipleChoice',choices=[{'id':'a','label':'A','text':'1'},{'id':'b','label':'B','text':'2'},{'id':'c','label':'C','text':'3'}],correctChoiceIds=['a','c'],selection={'mode':'exact','count':2},grading={'method':'exactChoiceSet'},stem='奇数を2つ選んでください。',explanation='1と3が奇数です。',choiceReasons=['奇数','偶数','奇数']);return q
with tempfile.TemporaryDirectory() as d:
    root=Path(d);config,normal,extras=prepare(root);normal=[multi(q) for q in normal];extras=[multi(q) for q in extras];path=root/'content/fixture'
    for name,data in [('questions.json',normal),('reviews.json',[review(q) for q in normal]),('assessments.json',extras),('assessment-reviews.json',[review(q) for q in extras])]:write(path/name,data)
    builder.build(root);server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=d));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/?firebase-emulator=1'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[browser.new_context(viewport={'width':390,'height':844}) for _ in range(2)];a,b=[c.new_page() for c in contexts];errors=[]
            for page in [a,b]:page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.goto(url);page.locator('.quick-start').wait_for()
            email='typed-'+uuid.uuid4().hex+'@example.test';login(a,email);login(b,email)
            a.locator('.study-entrance').first.click();a.get_by_role('checkbox').nth(2).check();synced(a);kick(b);wait_for_async(b,'async()=>(await ('+READ+')()).state?.attempts.some(a=>a.selectedChoiceIds?.includes("c"))')
            b.locator('.study-entrance').first.click();b.get_by_role('checkbox').nth(2).wait_for();assert b.get_by_role('checkbox').nth(2).is_checked();b.get_by_role('checkbox').first.check();b.locator('[data-action=submit]').click();b.locator('#result-heading').wait_for();synced(b);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).state.attempts.some(a=>a.status==="correct"&&JSON.stringify(a.selectedChoiceIds)==="[\\"a\\",\\"c\\"]")')
            nav(a,'home');a.locator('.home-assessments [data-view=diagnostics]').click();a.get_by_role('button',name='40問の診断をはじめる',exact=True).click();a.get_by_role('checkbox').nth(2).check();a.locator('[data-action=pause-diagnostic]').click();synced(a);kick(b);wait_for_async(b,'async()=>(await ('+READ+')()).rows.some(r=>r.kind==="diagnostic"&&JSON.stringify(r.payload.currentChoiceId)==="[\\"c\\"]")');nav(b,'home');b.locator('.home-assessments [data-action=resume-diagnostic]').click();b.get_by_role('checkbox').nth(2).wait_for();assert b.get_by_role('checkbox').nth(2).is_checked();b.get_by_role('checkbox').first.check();b.locator('[data-action=submit-diagnostic]').click();b.locator('[data-action=end-diagnostic]').click();b.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();synced(b);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).rows.some(r=>r.kind==="diagnostic"&&r.payload.status==="ended_early")');nav(a,'home');a.locator('.home-assessments [data-view=diagnostics]').click();a.get_by_role('button',name='結果を見る',exact=True).click();a.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();assert '正解 1' in a.locator('#main').inner_text();assert not errors,errors
            browser.close()
    finally:server.shutdown()
print('PASS real Auth/Firestore and two browser stores / partial multiple selection sync / foreign-device continuation and exact grading / diagnosis array checkpoint and completed result sync / no production writes')
