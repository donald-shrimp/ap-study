"""Real Firebase SDK, separate browsers: explicit card resume and protected notes."""
from pathlib import Path
exec(compile((Path(__file__).parent/'sync.py').read_text().split('with sync_playwright() as p:')[0],str(Path(__file__).parent/'sync.py'),'exec'))
READ_PERSONAL='''async()=>{const root=new URL('.',document.baseURI),sdk=await import(new URL('assets/vendor/firebase.js',root)),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),{createLocalStore}=await import(new URL('src/storage/local.js',root));const main=createLocalStore({rootPath:root.pathname,qualificationId:'ap',owner:sdk.getAuth().currentUser?`uid:${sdk.getAuth().currentUser.uid}`:undefined}),identity=await main.identity();await main.close();const s=createWorkspaceStore({...identity,rootPath:root.pathname,namespaceName:'personal',validate:(k,p)=>p});try{return {rows:await s.read(),identity};}finally{await s.close();}}'''
def personal(page):return page.evaluate(READ_PERSONAL)
def personal_synced(page):
 settings(page);page.locator('#sync-now').click();page.wait_for_function('document.getElementById("sync-state").dataset.personal==="synced"',timeout=45000)
 wait_for_async(page,'async()=>!(await ('+READ_PERSONAL+')()).rows.some(r=>r.kind!=="draft"&&r.dirty)',timeout=45000);close_settings(page)
def records(page):
 close_settings(page);page.locator('.sidebar [data-view=history]').click();page.locator('[data-reading-topic="ネットワーク"]').wait_for()
def note(page):return page.locator('[data-reading-topic="ネットワーク"]')
def saved_note(page,text):wait_for_async(page,'async()=>(await ('+READ_PERSONAL+')()).rows.some(r=>r.id==="note--network"&&r.payload.text==='+json.dumps(text)+')')
def open_cards(page):
 close_settings(page);page.locator('.sidebar [data-view=home]').click();page.locator('[data-action=cards-open]').click();page.locator('.flashcard').wait_for()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[b.new_context(viewport={'width':390,'height':844}) for _ in range(2)];a,c=[ctx.new_page() for ctx in contexts];errors=[]
 for page in [a,c]:page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL);page.locator('.quick-start').wait_for()
 artifacts=Path('/workspace/scratch/personal-ui');artifacts.mkdir(exist_ok=True)
 email=f'personal-{time.time_ns()}@example.test'
 records(a);note(a).fill('ゲストのメモ');saved_note(a,'ゲストのメモ');login(a,email);personal_synced(a);records(a);assert note(a).input_value()==''
 login(c,email);personal_synced(c)
 note(a).fill('ネットワーク p.20');saved_note(a,'ネットワーク p.20');personal_synced(a);personal_synced(c);records(c);assert note(c).input_value()=='ネットワーク p.20'
 note(c).fill('スマホで編集中');saved_note(c,'スマホで編集中');personal_synced(c);personal_synced(a);records(a)
 # Remote acknowledged change while the other input is focused: no DOM swap,
 # cursor movement or typing loss. A subsequent edit requires an explicit choice.
 note(c).focus();note(c).evaluate('(el)=>el.setSelectionRange(2,2)');handle=note(c).element_handle()
 note(a).fill('PCから変更');saved_note(a,'PCから変更');personal_synced(a)
 c.evaluate('document.getElementById("sync-now").click()');wait_for_async(c,'async()=>(await ('+READ_PERSONAL+')()).rows.some(r=>r.id==="note--network"&&r.payload.text==="PCから変更")')
 assert handle.evaluate('(el)=>el.isConnected && document.activeElement===el && el.selectionStart===2')
 assert note(c).input_value()=='スマホで編集中'
 note(c).fill('スマホの入力を残す');c.locator('[data-action=note-local][data-topic-id=network]').wait_for()
 c.locator('#record-field-network').screenshot(path=str(artifacts/'memo-conflict.png'));assert c.evaluate('document.documentElement.scrollWidth<=innerWidth')
 c.locator('[data-action=note-local][data-topic-id=network]').click();saved_note(c,'スマホの入力を残す');personal_synced(c);personal_synced(a);records(a);assert note(a).input_value()=='スマホの入力を残す'
 print('PASS explicit guest isolation / note sync / focused DOM and cursor protected / local choice',flush=True)
 # Competing offline edits persist after reload. Choosing remote clears the
 # local pending draft; an empty note is a cloud operation, not a lost deletion.
 contexts[1].set_offline(True);records(c);note(c).fill('オフラインの入力');saved_note(c,'オフラインの入力');c.reload();c.locator('[data-reading-topic="ネットワーク"]').wait_for();assert note(c).input_value()=='オフラインの入力'
 note(a).fill('PCの新しいメモ');saved_note(a,'PCの新しいメモ');personal_synced(a)
 contexts[1].set_offline(False);c.evaluate('document.getElementById("sync-now").click()');c.locator('[data-action=note-remote][data-topic-id=network]').wait_for(timeout=45000);assert note(c).input_value()=='オフラインの入力'
 c.locator('[data-action=note-remote][data-topic-id=network]').click();saved_note(c,'PCの新しいメモ');personal_synced(c)
 note(c).fill('');saved_note(c,'');personal_synced(c);personal_synced(a);records(a);assert note(a).input_value()==''
 print('PASS offline save/reload / CAS conflict remote choice / empty note synced',flush=True)
 # Per-device positions remain independent. No incoming checkpoint replaces
 # the active flashcard or focus; continuation is an explicit control.
 open_cards(a);a.locator('[name=card-topic]').select_option('network');a.locator('[data-action=card-flip]').click();a.locator('.card-back').wait_for();personal_synced(a)
 open_cards(c);c.locator('[name=card-topic]').select_option('database');c.locator('[data-action=card-flip]').click();c.locator('.card-back').wait_for();current=c.locator('.flashcard h2').inner_text();back=c.locator('.card-back').element_handle()
 a.locator('[data-action=card-rate][data-outcome=recalled]').click();a.locator('[data-action=card-flip]').wait_for();personal_synced(a)
 c.evaluate('document.getElementById("sync-now").click()');wait_for_async(c,'async()=>(await ('+READ_PERSONAL+')()).rows.filter(r=>r.kind==="checkpoint").length===2');c.locator('#card-remote-resume summary').wait_for()
 assert back.evaluate('(el)=>el.isConnected && document.activeElement===el');assert c.locator('.flashcard h2').inner_text()==current
 c.locator('#card-remote-resume summary').click();c.screenshot(path=str(artifacts/'card-resume.png'),full_page=True);c.evaluate('document.documentElement.style.fontSize="32px"');assert c.evaluate('document.documentElement.scrollWidth<=innerWidth');c.evaluate('document.documentElement.style.fontSize=""');c.locator('#card-remote-resume summary').click()
 latest=[r for r in personal(a)['rows'] if r['kind']=='checkpoint'][0]['payload']['checkpoint'];c.locator('#card-remote-resume summary').click();c.locator('[data-action=card-remote-resume]').click();c.locator('[data-action=card-flip]').wait_for();assert c.locator('[name=card-topic]').input_value()==latest['topicId'];personal_synced(c)
 own=[r for r in personal(c)['rows'] if r['id']=='checkpoint--'+personal(c)['identity']['deviceId']][0]['payload']['checkpoint'];assert own==latest
 contexts[1].set_offline(True);c.reload();c.locator('.flashcard').wait_for();assert c.locator('[name=card-topic]').input_value()=='network';contexts[1].set_offline(False)
 assert state(a)['state']['attempts']==state(c)['state']['attempts']==[]
 print('PASS per-device checkpoints / incoming card and focus stable / explicit resume / offline resumed view / normal attempts untouched',flush=True)
 # Explicit guest adoption brings notes only where an account note does not
 # exist; logout/account switch restores the right namespace.
 settings(a);a.wait_for_function('document.getElementById("import-guest").hidden');personal_synced(a);records(a);assert note(a).input_value()==''
 settings(a);a.locator('#google-logout').click();a.wait_for_function('!document.getElementById("google-login").hidden && !document.getElementById("google-login").disabled');close_settings(a);records(a);assert note(a).input_value()=='ゲストのメモ'
 login(a,'other-'+email);personal_synced(a);records(a);assert note(a).input_value()==''
 assert not errors,errors
 print('PASS explicit adoption retains existing account note / logout restores guest / UID isolation / no browser errors',flush=True)
 for ctx in contexts:ctx.close()
 b.close()
