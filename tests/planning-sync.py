from browser_storage import nav as action_nav, open_plan_editor, open_plan_ai
"""Real Auth/Firestore Emulator: plans and diagnostic runs across two browsers."""
import json, shutil, uuid
from playwright.sync_api import sync_playwright
from browser_storage import wait_for_async
URL='http://127.0.0.1:4173/?firebase-emulator=1'
READ='''async()=>{
 const sdk=await import('/assets/vendor/firebase.js'),user=sdk.getAuth().currentUser,{createLocalStore}=await import('/src/storage/local.js');
 const study=createLocalStore({qualificationId:'ap',rootPath:'/',owner:user?`uid:${user.uid}`:undefined});try{const identity=await study.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),workspace=createWorkspaceStore({...identity,rootPath:'/',validate:(kind,payload)=>payload});try{return await workspace.read();}finally{await workspace.close();}}finally{await study.close();}
}'''
def settings(page):
 if not page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.locator('#settings-button').click()
def close(page):
 if page.locator('#settings-dialog').evaluate('(d)=>d.open'):page.get_by_role('button',name='設定を閉じる').click()
def kick(page):settings(page);page.locator('#sync-now').click();close(page)
def synced(page):
 kick(page)
 try:wait_for_async(page,'async()=>!(await ('+READ+')()).some(r=>r.dirty||r.conflict)')
 except AssertionError:
  print('Sync status:',page.locator('#workspace-sync-state').inner_text());print('Pending metadata:',[{k:r.get(k) for k in ['kind','dirty','remoteRevision','localRevision']} for r in page.evaluate(READ)]);raise
def login(page,email):
 settings(page);page.wait_for_function('!document.getElementById("google-login").disabled')
 with page.expect_popup() as event:page.locator('#google-login').click()
 popup=event.value;popup.wait_for_url('**/emulator/auth/handler?**');popup.get_by_text('Sign-in with Google.com',exact=True).wait_for()
 if popup.get_by_text(email,exact=True).count():popup.get_by_text(email,exact=True).click()
 else:popup.get_by_text('Add new account').click();popup.locator('#email-input').fill(email);popup.locator('#display-name-input').fill('Plan test');popup.get_by_role('button',name='Sign in with Google.com',exact=True).click()
 page.wait_for_function('document.getElementById("account-name").textContent.includes('+json.dumps(email)+') && !document.getElementById("google-logout").disabled');synced(page)
def plan_view(page):
 page.locator('.sidebar [data-view=home]').click();page.get_by_role('button',name='計画を見る' if page.get_by_role('button',name='計画を見る',exact=True).count() else '受験日・計画を登録',exact=True).click()
 open_plan_editor(page);open_plan_ai(page)
def set_date(page,date):
 page.locator('[name=exam-objective]').fill(date);page.get_by_role('button',name='受験日を保存',exact=True).click();page.get_by_text('受験日を保存しました。',exact=True).wait_for()

with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[b.new_context(viewport={'width':390,'height':844}) for _ in range(3)];pages=[c.new_page() for c in contexts];a,c,other=pages;errors=[]
 for page in pages:page.on('console',lambda message:print(message.text) if message.type=='warning' else None);page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL);page.get_by_role('button',name='とりあえずはじめる',exact=True).wait_for()
 email='planning-test-'+uuid.uuid4().hex+'@hitomon.test';login(a,email);login(c,email)
 plan_view(c);assert c.locator('[name=exam-objective]').input_value()==''
 plan_view(a);set_date(a,'2026-11-04');synced(a);kick(c);wait_for_async(c,'async()=>(await ('+READ+')()).some(r=>r.id==="planning")');c.wait_for_function('document.querySelector("[name=exam-objective]").value==="2026-11-04"');assert not c.locator('#planning-stale').is_visible()
 a.locator('[name=exam-objective]').fill('2026-12-24');set_date(c,'2026-11-30');synced(c);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).some(r=>r.payload.examDates?.[0]?.date==="2026-11-30")');a.locator('#planning-stale').wait_for(state='visible');assert a.locator('[name=exam-objective]').input_value()=='2026-12-24';a.get_by_role('button',name='入力を破棄して最新版を表示',exact=True).click();assert a.locator('[name=exam-objective]').input_value()=='2026-11-30'
 contexts[0].set_offline(True);set_date(a,'2026-12-03');set_date(c,'2026-12-15');synced(c);contexts[0].set_offline(False);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).some(r=>r.conflict)');a.get_by_role('heading',name='計画の変更が競合しています',exact=True).wait_for();a.get_by_role('button',name='この端末の内容を使う',exact=True).click();synced(a);kick(c);wait_for_async(c,'async()=>(await ('+READ+')()).some(r=>r.payload.examDates?.[0]?.date==="2026-12-03")',timeout=30000)
 # Optional phase fields and context are accepted by the updated Rules.
 example=json.loads(open('schemas/study-plan.example.json').read());example['examDates']=[{'examPartId':'objective','date':'2026-12-03'}]
 open_plan_ai(a);a.locator('#plan-json').fill(json.dumps(example));a.get_by_role('button',name='検証してプレビュー',exact=True).click();a.get_by_role('button',name='この内容で登録',exact=True).click();a.get_by_text('受験日と計画を登録しました。',exact=True).wait_for();synced(a);kick(c);wait_for_async(c,'async()=>(await ('+READ+')()).some(r=>r.payload.phases?.[0]?.weeklyTargets?.length===2)')
 c.get_by_role('heading',name=example['phases'][0]['name'],exact=True).first.wait_for();assert not c.locator('#planning-stale').is_visible();assert c.locator('#plan-overview .context-list').text_content().find(example['context']['rationale'])>=0
 # A real draft survives remote changes; an untouched page refreshes by itself.
 c.locator('.summary-preview').evaluate('(details)=>details.open=true');context_form=c.locator('#context-form');context_form.evaluate('(f)=>f.parentElement.open=true');context_form.locator('[name=rationale]').fill('まだ保存していないスマホ側の前提')
 form=a.locator('#context-form');form.evaluate('(f)=>f.parentElement.open=true');form.locator('[name=rationale]').fill('PCで更新した計画の前提');form.get_by_role('button',name='前提を保存',exact=True).click();a.get_by_text('計画の前提を保存しました。',exact=True).wait_for();synced(a);kick(c);wait_for_async(c,'async()=>(await ('+READ+')()).some(r=>r.payload.context?.rationale==="PCで更新した計画の前提")');c.locator('#planning-stale').wait_for(state='visible');assert context_form.locator('[name=rationale]').input_value()=='まだ保存していないスマホ側の前提';assert 'PCで更新した計画の前提' in c.locator('.summary-preview').inner_text();c.get_by_role('button',name='入力を破棄して最新版を表示',exact=True).click()
 context_form=c.locator('#context-form');context_form.evaluate('(f)=>f.parentElement.open=true');context_form.locator('[name=rationale]').fill('別端末で見直した計画の前提');context_form.get_by_role('button',name='前提を保存',exact=True).click();c.get_by_text('計画の前提を保存しました。',exact=True).wait_for();synced(c);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).some(r=>r.payload.context?.rationale==="別端末で見直した計画の前提")');c.locator('.phase-targets > summary').click();c.get_by_role('button',name='完了にする',exact=True).click();c.get_by_text('予定の完了状態を保存しました。',exact=True).wait_for();synced(c);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).some(r=>r.payload.phases?.[0]?.milestones?.[0]?.completed===true)')
 a.get_by_role('button',name='ホーム',exact=True).click();a.get_by_role('button',name='実力診断（30問）',exact=True).click();a.get_by_role('button',name='30問の診断をはじめる',exact=True).click();a.locator('[name=diagnostic-answer]').first.wait_for();a.locator('[name=diagnostic-answer]').first.check();a.get_by_role('button',name='回答して次へ',exact=True).click();a.get_by_text('診断 2 / 30問',exact=True).wait_for();synced(a);kick(c);wait_for_async(c,'async()=>(await ('+READ+')()).some(r=>r.kind==="diagnostic")');c.locator('.sidebar [data-view=home]').click();c.get_by_role('button',name='診断の続きから',exact=True).click();c.get_by_text('診断 2 / 30問',exact=True).wait_for();assert c.locator('.hint-section,.result').count()==0
 c.locator('[name=diagnostic-answer]').first.check();c.get_by_role('button',name='回答して次へ',exact=True).click();c.get_by_text('診断 3 / 30問',exact=True).wait_for();c.on('dialog',lambda d:d.accept());c.get_by_role('button',name='ここまでで診断終了',exact=True).click();c.get_by_role('heading',name='診断結果（部分結果）',exact=True).wait_for();synced(c);kick(a);wait_for_async(a,'async()=>(await ('+READ+')()).some(r=>r.kind==="diagnostic"&&r.payload.status==="ended_early")');assert a.get_by_role('heading',name='診断結果（部分結果）',exact=True).is_visible()
 assert len([r for r in a.evaluate(READ) if r['kind']=='diagnostic'])==1
 login(other,'planning-other-'+uuid.uuid4().hex+'@hitomon.test');assert not other.evaluate(READ), 'other UID received plans/diagnostics'
 assert not errors,errors;b.close()
print('PASS real Firebase plans / two browsers / untouched open planning page updates automatically / date and context drafts preserved / offline CAS conflict and local choice / context, week targets and manual milestones / diagnostic checkpoint and closure across devices / no duplicate run / UID isolation')
