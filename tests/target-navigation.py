"""Real target links, URL precedence, history, tabs, shared plans and offline caches."""
import json,os,shutil,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import select_target,state,open_plan_editor,open_data_management,wait_for_async

URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/ap/')
ROOT=URL.rsplit('ap/',1)[0]
ARTIFACTS=Path(tempfile.mkdtemp(prefix='hitomon-target-navigation-'))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
 ctx=b.new_context(viewport={'width':390,'height':844});page=ctx.new_page();errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.goto(ROOT+'?qualifications');page.get_by_role('heading',name='資格・科目を選ぶ').wait_for()
 assert page.locator('.qualification-option').count()==3
 assert page.locator('[data-qualification-id=ap][data-part-id=objective]').inner_text().startswith('応用情報－科目A\n800問')
 assert page.locator('[data-qualification-id=ap][data-part-id=written]').inner_text().startswith('応用情報－科目B\n大問44題')
 assert not any('/packs/' in u or '/index.' in u for u in requests)
 for width in [320,390,800,801,1440,1920]:
  page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  box=page.locator('.qualification-chooser').bounding_box();assert box['width']>=min(width-70,600)
  if width in [390,1440]:page.screenshot(path=str(ARTIFACTS/f'chooser-{width}.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 page.locator('[data-qualification-id=ap][data-part-id=written]').focus();page.keyboard.press('Enter')
 page.locator('#qualification-switch[data-part-id=written]').wait_for();assert 'entry=' not in page.url
 assert page.locator('[data-action=switch-target]').count()==0
 for width in [320,390,1440]:
  page.set_viewport_size({'width':width,'height':900});assert page.locator('.qualification-part').inner_text()=='・科目B'
  part=page.locator('.qualification-part').bounding_box();button=page.locator('#qualification-switch').bounding_box();assert part['x']+part['width']<=button['x']+button['width']
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(ARTIFACTS/'header-b.png'))
 # URL wins over prior B selection and is pinned across reload/history.
 page.goto(ROOT+'ap/?part=objective');page.locator('#qualification-switch[data-part-id=objective]').wait_for();assert page.locator('.quick-start').count()
 select_target(page,'written');page.locator('.study-entry').wait_for();page.go_back();page.get_by_role('heading',name='資格・科目を選ぶ').wait_for();page.go_forward();page.locator('#qualification-switch[data-part-id=written]').wait_for()
 page.goto(ROOT);page.locator('#qualification-switch[data-part-id=written]').wait_for();assert 'qualification=ap' in page.url
 # A second tab changes the startup preference, not the foreground target.
 other=ctx.new_page();other.goto(ROOT+'ab730/');other.locator('#qualification-switch').wait_for();assert other.locator('.qualification-part').count()==0
 page.reload();page.locator('#qualification-switch[data-part-id=written]').wait_for()
 # The same plan/date is visible from both AP targets.
 select_target(page,'objective');page.get_by_role('button',name='計画を登録',exact=True).click();open_plan_editor(page);page.locator('#exam-form').wait_for()
 page.locator('[name=exam-objective]').fill('2026-12-01');page.get_by_role('button',name='受験日を保存',exact=True).click();page.get_by_text('受験日を保存しました。',exact=True).wait_for()
 select_target(page,'written');page.get_by_role('button',name='計画を見る',exact=True).click();open_plan_editor(page);page.locator('#exam-form').wait_for();assert page.locator('[name=exam-objective]').input_value()=='2026-12-01'
 # B draft/save failure prevents both header and brand exits without losing input.
 page.locator('.sidebar [data-view=home]').click();page.locator('[data-action=written-start]').first.click();page.locator('textarea[data-written-key]').fill('別タブでも維持')
 wait_for_async(page,"async()=>{const {createLocalStore}=await import(new URL('src/storage/local.js',document.baseURI)),s=createLocalStore({qualificationId:'ap',rootPath:new URL('.',document.baseURI).pathname});try{const i=await s.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',document.baseURI)),w=createWorkspaceStore({...i,rootPath:new URL('.',document.baseURI).pathname,namespaceName:'written',validate:(k,p)=>p});try{return (await w.read()).some(r=>r.payload.responses['q1--answer']?.value==='別タブでも維持');}finally{await w.close();}}finally{await s.close();}}")
 other.goto(ROOT+'ap/?part=objective&entry=home');other.locator('#qualification-switch[data-part-id=objective]').wait_for();assert page.locator('textarea[data-written-key]').input_value()=='別タブでも維持'
 page.evaluate("()=>{window.savedPut=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...a){if(this.name==='documents')throw new DOMException('test','QuotaExceededError');return window.savedPut.apply(this,a);};}")
 page.locator('textarea[data-written-key]').fill('保存失敗も保持');page.get_by_role('button',name='保存を再試行',exact=True).wait_for();previous_url=page.url
 for selector in ['#qualification-switch','.brand']:
  page.locator(selector).click();page.wait_for_timeout(100);assert page.url==previous_url;assert page.locator('textarea[data-written-key]').input_value()=='保存失敗も保持'
 page.evaluate('()=>{IDBObjectStore.prototype.put=window.savedPut;}');page.get_by_role('button',name='保存を再試行',exact=True).click();page.locator('.written-save-actions').wait_for(state='hidden')
 # B scrolling and its exit guard must not overwrite A's independent display cursor.
 select_target(page,'objective');page.locator('.study-entrance[data-paper-mode=all]').click();page.locator('[data-action=submit]').wait_for();aid=state(page)['currentId']
 select_target(page,'written');saved_scroll=next(a['scrollY'] for a in state(page)['attempts'] if a['id']==aid)
 page.locator('.study-entry [data-action=written-resume]').click();page.locator('[data-action=written-pane][data-pane=body]').click();page.evaluate('window.scrollTo(0,430)')
 select_target(page,'objective');assert next(a['scrollY'] for a in state(page)['attempts'] if a['id']==aid)==saved_scroll
 select_target(page,'written',resume_written=True);page.locator('[data-action=written-pane][data-pane=questions]').click();assert page.locator('textarea[data-written-key]').input_value()=='保存失敗も保持'
 # Root launch follows the latest choice; invalid explicit parts open the chooser.
 select_target(page,'written');page.goto(ROOT);page.locator('#qualification-switch[data-part-id=written]').wait_for()
 requests.clear();page.goto(ROOT+'ab730/?part=written');page.get_by_role('heading',name='資格・科目を選ぶ').wait_for();assert '利用できません' in page.locator('#notice').inner_text();assert not page.locator('.qualification-option[aria-current=true]').count();assert not any('/index.' in u for u in requests)
 # Cached manifests support an older qualification-only catalog offline.
 page.goto(ROOT+'ab730/?part=objective');page.locator('.quick-start').wait_for();page.locator('#qualification-switch').click();page.get_by_role('heading',name='資格・科目を選ぶ').wait_for()
 page.evaluate("async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener('controllerchange',ok,{once:true}));const root=new URL('.',document.baseURI),cache=await caches.open('hitomon-'+root.pathname+'content'),u=new URL('data/qualifications/catalog.json',root),r=await cache.match(u.href),v=await r.json();for(const q of v.qualifications)delete q.studyTargets;await cache.put(u.href,new Response(JSON.stringify(v),{headers:{'Content-Type':'application/json'}}));}")
 ctx.set_offline(True);page.reload();page.get_by_role('heading',name='資格・科目を選ぶ').wait_for();assert page.locator('.qualification-option').count()==3
 page.locator('[data-qualification-id=ap][data-part-id=written]').click();page.locator('#qualification-switch[data-part-id=written]').wait_for();page.locator('.study-entry [data-action=written-resume]').click();page.locator('textarea[data-written-key]').wait_for();assert page.locator('textarea[data-written-key]').input_value()=='保存失敗も保持'
 # Cached A stays usable even if B's bank and another qualification's manifest are absent.
 page.evaluate("""async()=>{for(const name of await caches.keys()){const cache=await caches.open(name);for(const req of await cache.keys()){const path=new URL(req.url).pathname;if(path.includes('/ap/cases.')||path.endsWith('/ab730/manifest.json'))await cache.delete(req);}}}""")
 page.goto(ROOT+'ap/?part=objective&entry=home');page.locator('#qualification-switch[data-part-id=objective]').wait_for();assert page.locator('.quick-start').count()
 ctx.set_offline(False)
 # Storage rejection still allows direct, explicit target selection.
 fresh=b.new_context();fresh.add_init_script("Storage.prototype.getItem=()=>{throw Error('blocked');};Storage.prototype.setItem=()=>{throw Error('blocked');};")
 blocked=fresh.new_page();blocked.on('pageerror',lambda e:errors.append(str(e)));blocked.goto(ROOT+'ap/?part=written&entry=home');blocked.locator('#qualification-switch[data-part-id=written]').wait_for();assert blocked.locator('.study-entry').count()
 assert not errors,errors;b.close()
print('PASS target counts / lazy chooser / 320-1920px / keyboard / URL and history / root+tabs / shared plan / failed-save header and brand guards / old catalog offline / localStorage denied')
print('Artifacts:',ARTIFACTS)
