"""Real Auth/Firestore SDK: immutable self-ratings and observed reset/restore."""
from pathlib import Path
exec(compile((Path(__file__).parent/'sync.py').read_text().split('with sync_playwright() as p:')[0],str(Path(__file__).parent/'sync.py'),'exec'))
READ_CARDS='''async()=>{const root=new URL('.',document.baseURI),sdk=await import(new URL('assets/vendor/firebase.js',root)),{createCardStore}=await import(new URL('src/storage/cards.js',root)),{createLocalStore}=await import(new URL('src/storage/local.js',root));const main=createLocalStore({rootPath:root.pathname,qualificationId:'ap'}),identity=await main.identity();await main.close();const s=createCardStore({rootPath:root.pathname,owner:sdk.getAuth().currentUser?`uid:${sdk.getAuth().currentUser.uid}`:identity.owner,qualificationId:'ap'});try{return {...await s.read(),rows:await s.syncStore().read(),cursor:await s.syncStore().cursor()};}finally{await s.close();}}'''
def cards(page):return page.evaluate(READ_CARDS)
def card_synced(page):
 settings(page);page.locator('#sync-now').click();page.wait_for_function('document.getElementById("card-sync-state").textContent.includes("自己評価も同期済み")',timeout=45000)
 wait_for_async(page,'async()=>!(await ('+READ_CARDS+')()).rows.some(r=>r.dirty)',timeout=45000);close_settings(page)
def open_cards(page):
 if not page.locator('.flashcard').count():page.locator('.sidebar [data-view=home]').click();page.locator('[data-action=cards-open]').click()
 page.locator('.flashcard').wait_for()
def rate(page,outcome):
 if page.locator('[data-action=card-flip]').count():page.locator('[data-action=card-flip]').click()
 count=len(cards(page)['events']);page.locator(f'[data-action=card-rate][data-outcome={outcome}]').click();wait_for_async(page,'async()=>(await ('+READ_CARDS+')()).events.length>'+str(count));page.locator('[data-action=card-flip]').wait_for()
def reset(page):
 page.locator('.card-data > summary').click();page.once('dialog',lambda d:d.accept());page.locator('[data-action=card-clear]').click();page.wait_for_function('document.querySelector("#card-progress").textContent.includes("確認済み 0")')
def import_backup(page,events):
 if not page.locator('#import-cards').is_visible():page.locator('.card-data > summary').click()
 page.locator('#import-cards').set_input_files({'name':'cards.json','mimeType':'application/json','buffer':json.dumps({'format':'hitomon-card-record','version':1,'qualificationId':'ap','events':events}).encode()})
 wait_for_async(page,'async()=>(await ('+READ_CARDS+')()).events.length==='+str(len(events)))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[b.new_context(viewport={'width':390,'height':844}) for _ in range(3)];a,c,f=[ctx.new_page() for ctx in contexts];errors=[]
 for page in [a,c,f]:page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL);page.locator('.quick-start').wait_for()
 email=f'cards-{time.time_ns()}@example.test'
 open_cards(a);rate(a,'again');guest=cards(a)['events'];assert len(guest)==1
 login(a,email);card_synced(a);assert cards(a)['events']==[] # no silent guest adoption
 login(c,email);card_synced(c)
 open_cards(a);open_cards(c);assert a.locator('.flashcard h2').inner_text()==c.locator('.flashcard h2').inner_text()
 # Simultaneous judgments of one card are separate events. Remote changes keep
 # the current card/back/focus stable, while counts and future selection update.
 c.locator('[data-action=card-flip]').click();current=c.locator('.flashcard h2').inner_text()
 rate(a,'recalled');card_synced(a);back=c.locator('.card-back').element_handle();c.evaluate('document.getElementById("sync-now").click()');wait_for_async(c,'async()=>(await ('+READ_CARDS+')()).events.length===1');assert back.evaluate('(el)=>el.isConnected && document.activeElement===el');assert c.locator('.card-back').is_visible() and c.locator('.flashcard h2').inner_text()==current
 rate(c,'again');card_synced(c);card_synced(a);events=cards(a)['events'];assert len(events)==2 and len({e['cardId'] for e in events})==1 and {e['outcome'] for e in events}=={'again','recalled'}
 before=state(a)['state']['attempts'];assert before==[]
 print('PASS two-device independent ratings / no implicit guest import / incoming counts preserve current card and back',flush=True)
 # An unobserved offline event survives the other device's reset; the observed
 # pair never returns through replay/reload. Offline outbox survives reload.
 contexts[1].set_offline(True);rate(c,'again');assert 'オフライン' in c.locator('#card-sync-detail').inner_text();offline=cards(c);assert any(r['dirty'] for r in offline['rows']);c.evaluate('navigator.serviceWorker.ready');c.reload();c.locator('.flashcard').wait_for();assert any(r['dirty'] for r in cards(c)['rows'])
 reset(a);assert cards(a)['events']==[];card_synced(a)
 contexts[1].set_offline(False);cp=cards(c)['checkpoint'];card_synced(c);assert len(cards(c)['events'])==1 and cards(c)['checkpoint']==cp;card_synced(a);assert len(cards(a)['events'])==1
 a.reload();a.locator('.flashcard').wait_for();card_synced(a);assert len(cards(a)['events'])==1
 print('PASS offline reload/outbox / observed reset propagates / concurrent unobserved rating and local checkpoint survive',flush=True)
 # Backup import explicitly restores the deleted IDs, and remains idempotent.
 backup=events+cards(a)['events'];import_backup(a,backup);card_synced(a);card_synced(c);assert len(cards(c)['events'])==3
 count=len(cards(a)['rows']);import_backup(a,backup);card_synced(a);assert len(cards(a)['rows'])==count
 reset(a);card_synced(a);card_synced(c);assert cards(c)['events']==[]
 import_backup(a,backup);card_synced(a);login(f,email);card_synced(f);assert len(cards(f)['events'])==3
 print('PASS backup restores observed deletions / repeated import idempotent / subsequent reset / fresh third device',flush=True)
 # Guest adoption adds ratings only once and cannot resurrect after reset.
 settings(a);a.once('dialog',lambda d:d.accept());a.locator('#import-guest').click();a.wait_for_function('!document.getElementById("import-guest").disabled');card_synced(a);assert len(cards(a)['events'])==4
 reset(a);card_synced(a);settings(a);a.once('dialog',lambda d:d.accept());a.locator('#import-guest').click();a.wait_for_function('!document.getElementById("import-guest").disabled');card_synced(a);assert cards(a)['events']==[]
 settings(a);a.locator('#google-logout').click();a.wait_for_function('!document.getElementById("google-login").disabled && !document.getElementById("google-login").hidden');assert cards(a)['events']==guest
 close_settings(a);login(a,'other-'+email);card_synced(a);assert cards(a)['events']==[]
 assert state(c)['state']['attempts']==before
 print('PASS explicit guest adoption / repeated adoption cannot undo deletion / logout restores guest / UID isolation / normal attempts unchanged',flush=True)
 assert not errors,errors
 for ctx in contexts:ctx.close()
 b.close()
