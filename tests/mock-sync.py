"""Actual Auth/Firestore SDK: fixed mock snapshots and conflicts across browsers."""
import json,shutil,uuid
from playwright.sync_api import sync_playwright
from browser_storage import nav,wait_for_async,state
URL='http://127.0.0.1:4173/?firebase-emulator=1'
READ='''async()=>{const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js'),study=createLocalStore({qualificationId:'ap',rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{const identity=await study.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),w=createWorkspaceStore({...identity,rootPath:'/',validate:(k,p)=>p});try{return await w.read();}finally{await w.close();}}finally{await study.close();}}'''
def settings(page):
 if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
 if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる').click()
def kick(page):settings(page);page.locator('#sync-now').click();close(page)
def synced(page):
 kick(page);wait_for_async(page,'async()=>!(await ('+READ+')()).some(r=>r.dirty||r.conflict)')
def login(page,email):
 settings(page);page.wait_for_function('!document.getElementById("google-login").disabled')
 with page.expect_popup() as event:page.locator('#google-login').click()
 pop=event.value;pop.wait_for_url('**/emulator/auth/handler?**');pop.get_by_text('Sign-in with Google.com',exact=True).wait_for()
 if pop.get_by_text(email,exact=True).count():pop.get_by_text(email,exact=True).click()
 else:pop.get_by_text('Add new account').click();pop.locator('#email-input').fill(email);pop.locator('#display-name-input').fill('Mock test');pop.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');synced(page)
def active(page):return next(r for r in page.evaluate(READ) if r['kind']=='mock')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[b.new_context(viewport={'width':390,'height':844}) for _ in range(3)];a,c,other=[ctx.new_page() for ctx in contexts];errors=[]
 for pg in [a,c,other]:pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('dialog',lambda d:d.accept());pg.goto(URL);pg.get_by_role('button',name='模試を受ける',exact=True).wait_for()
 email='mock-'+uuid.uuid4().hex+'@hitomon.test';login(a,email);login(c,email)
 a.get_by_role('button',name='模試を受ける',exact=True).click();a.locator('[data-mock-set=ap-mock-a] [data-action=start-mock]').click();a.get_by_text('模試 A 1 / 80問',exact=True).wait_for();synced(a);synced(c)
 c.get_by_role('button',name='模試を受ける',exact=True).click();c.locator('[data-mock-set=ap-mock-a]').get_by_role('button',name='続きから',exact=True).click();c.get_by_text('模試 A 1 / 80問',exact=True).wait_for();first=active(a);assert active(c)['id']==first['id']
 frozen=json.dumps(first['payload']['slots'],sort_keys=True)
 a.locator('[name=diagnostic-answer]').first.check();a.get_by_role('button',name='回答して次へ',exact=True).click();a.get_by_text('模試 A 2 / 80問',exact=True).wait_for();synced(a);synced(c);c.get_by_text('模試 A 2 / 80問',exact=True).wait_for();assert json.dumps(active(c)['payload']['slots'],sort_keys=True)==frozen
 contexts[1].set_offline(True);c.locator('[name=diagnostic-answer]').first.check();wait_for_async(c,'async()=>{const r=await ('+READ+')();return r.some(r=>r.kind==="mock"&&r.dirty)}')
 a.locator('[name=diagnostic-answer]').nth(1).check();a.get_by_role('button',name='回答して次へ',exact=True).click();a.get_by_text('模試 A 3 / 80問',exact=True).wait_for();synced(a);contexts[1].set_offline(False);kick(c)
 wait_for_async(c,'async()=>{const r=await ('+READ+')();return r.some(r=>r.kind==="mock"&&r.conflict)}');c.get_by_role('heading',name='模試の変更が競合しています',exact=True,level=1).wait_for();c.get_by_role('button',name='クラウドの内容を使う',exact=True).click();c.get_by_text('模試 A 3 / 80問',exact=True).wait_for();assert active(c)['payload']['responses']==active(a)['payload']['responses'];assert json.dumps(active(c)['payload']['slots'],sort_keys=True)==frozen
 a.get_by_role('button',name='ここまでで模試終了',exact=True).click();a.get_by_role('heading',name='模試 Aの結果（部分結果）',exact=True).wait_for();synced(a);synced(c);c.get_by_role('heading',name='模試 Aの結果（部分結果）',exact=True).wait_for()
 nav(c,'history');c.get_by_role('button',name='模試結果',exact=True).click();assert '前回（途中終了）' in c.locator('[data-mock-set=ap-mock-a]').inner_text();assert state(c)['attempts']==[]
 login(other,'mock-other-'+uuid.uuid4().hex+'@hitomon.test');assert not any(r['kind']=='mock' for r in other.evaluate(READ))
 backup_check=c.evaluate('''async()=>{const rows=await ('''+READ+''')(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),{validateMock}=await import('/src/domain/mock.js'),{loadCatalog}=await import('/src/content/catalog.js'),catalog=await loadCatalog('ap'),store=createWorkspaceStore({owner:'guest:restore-test',qualificationId:'ap',deviceId:'restore-test',rootPath:'/',namespaceName:'mock-backup-test',validate:(kind,payload)=>validateMock(payload,catalog.manifest,()=>{})});try{const result=await store.restoreBackup({plan:null,runs:rows.filter(r=>r.kind==='mock').map(r=>r.payload)}),stored=await store.read();return {result,kinds:stored.map(r=>r.kind),snapshotsMatch:JSON.stringify(stored[0].payload)===JSON.stringify(rows.find(r=>r.kind==='mock').payload)};}finally{await store.close();}}''')
 assert backup_check['kinds']==['mock'] and backup_check['snapshotsMatch']
 assert not errors,errors;b.close()
print('PASS SDK/Emulator two-browser mock80 sync / fixed snapshots / selected+finalized progress / offline conflict explicit cloud choice / partial score per-set history / UID isolation / backup kind and payload preservation / no normal-attempt pollution')
