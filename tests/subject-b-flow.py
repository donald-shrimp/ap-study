"""A/B isolation, canonical persistence, independent UI, offline resume and v2 backup."""
import json,shutil,tempfile,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_storage import state,nav,wait_for_async,open_plan_ai,open_data_management,select_target
ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('AP_STUDY_URL','http://127.0.0.1:4173/ap/')
ARTIFACTS=Path(tempfile.mkdtemp(prefix='hitomon-subject-b-'))
READ_CASES='''async()=>{const {createLocalStore}=await import('/src/storage/local.js'),s=createLocalStore({qualificationId:'ap',rootPath:'/'});try{const i=await s.identity(),{createWorkspaceStore}=await import('/src/storage/workspace.js'),w=createWorkspaceStore({...i,rootPath:'/',namespaceName:'written',validate:(k,p)=>p});try{return (await w.read()).map(r=>r.payload).sort((a,b)=>a.startedAt.localeCompare(b.startedAt));}finally{await w.close();}}finally{await s.close();}}'''
def cases(page):return page.evaluate(READ_CASES)
def wait_case(page,predicate):wait_for_async(page,'async()=>{const r=await ('+READ_CASES+')();return '+predicate+';}')
def target(page,part):
 select_target(page,part,resume_written=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write']);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.goto(URL);page.locator('.quick-start').wait_for()
 page.locator('.study-entrance[data-paper-mode=all]').click();page.locator('[data-action=submit]').wait_for();a=state(page);aid=a['currentId'];page.locator('[data-action=hint]').click();page.locator('[data-action=pause]').click();target(page,'written');assert not page.locator('.home-assessments').count();page.locator('[data-action=written-start]').first.click();page.locator('textarea[data-written-key]').fill('未知表現');wait_case(page,'r[0].responses["q1--answer"]?.value==="未知表現"');assert state(page)['attempts'][0]['hintCount']==1
 page.locator('[data-action=written-submit]').click();page.locator('[data-action=written-answer]').click();page.locator('[data-action=written-rate][data-outcome=unsure]').click();wait_case(page,'r[0].evaluations["q1--answer"]?.outcome==="unsure"');page.locator('[data-action=written-item]').nth(2).click();page.locator('textarea[data-written-key]').first.fill('ロックアウト');wait_case(page,'r[0].responses["q3--setting"]?.value==="ロックアウト"');case_id=cases(page)[0]['id'];target(page,'objective');assert page.locator('.quick-start').count();page.locator('.study-entrance[data-paper-mode=all]').click();page.locator('[data-action=submit]').wait_for();assert state(page)['currentId']==aid;target(page,'written');assert page.locator('textarea[data-written-key]').first.input_value()=='ロックアウト'
 # A and B keep their own checkpoints across page reload.
 page.reload();page.locator('.written-items').wait_for();assert page.locator('textarea[data-written-key]').first.input_value()=='ロックアウト';assert cases(page)[0]['id']==case_id
 for width in [320,390,1440,2560]:
  page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  if width in [390,1440]:page.screenshot(path=str(ARTIFACTS/f'written-{width}.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.locator('[data-action=written-pane][data-pane=body]').click();page.locator('.written-body').wait_for(state='visible');assert not page.locator('.written-items').is_visible();page.locator('[data-action=written-pane][data-pane=questions]').click();page.locator('.written-items').wait_for(state='visible')
 # An exam-like run hides all explanations until all fields are submitted.
 nav(page,'home');page.locator('[data-action=written-start][data-id=ap-r07h-pm1][data-mode=exam]').click();page.locator('textarea[data-written-key]').fill('デジタルフォレンジックス');page.locator('[data-action=written-submit]').click();assert page.locator('[data-action=written-answer]').count()==0 and page.locator('.written-answer').count()==0
 run=cases(page)[-1];assert run['mode']=='exam';mode_id=run['id'];slots=[(i,f) for i in run['material']['items'] for f in i['fields']]
 for item in run['material']['items']:
  page.locator('.written-item-nav [data-action=written-item][data-id='+item['id']+']').click();page.locator('.written-item-nav [data-id='+item['id']+'][aria-current=step]').wait_for()
  for f in item['fields']:
   key=item['id']+'--'+f['id'];btn=page.locator('[data-action=written-skip][data-written-key='+key+']')
   if btn.count():btn.click()
  if item!=run['material']['items'][-1]:assert page.locator('[data-action=written-answer]').count()==0
 wait_case(page,'r.find(x=>x.id==='+json.dumps(mode_id)+').progress.status==="awaiting_evaluation"')
 for item in run['material']['items']:
  page.locator('.written-item-nav [data-action=written-item][data-id='+item['id']+']').click();page.locator('.written-item-nav [data-id='+item['id']+'][aria-current=step]').wait_for()
  for f in item['fields']:
   key=item['id']+'--'+f['id'];page.locator('[data-action=written-answer][data-written-key='+key+']').click();page.locator('.written-field[data-written-key='+key+'] .written-answer').wait_for();rating=page.locator('[data-action=written-rate][data-written-key='+key+'][data-outcome=notYet]')
   if rating.count():rating.click()
 wait_case(page,'r.find(x=>x.id==='+json.dumps(mode_id)+').progress.status==="completed"')
 # AI prompt contains the current field + shared body, not all other answer explanations.
 page.locator('[data-action=written-ai]').first.click();page.locator('#ai-handoff-dialog').wait_for(state='visible');assert '【共通本文】' in page.locator('#ai-handoff-preview').input_value();page.locator('#ai-handoff-close').click()
 # New backups serialize only stable vector responses for choice records.
 page.locator('#settings-button').click();open_data_management(page)
 with page.expect_download() as event:page.locator('#export-state').click()
 download=event.value;path=ARTIFACTS/'v2-backup.json';download.save_as(str(path));backup=json.loads(path.read_text());assert backup['version']==2 and backup['format']=='hitomon-study-state' and 'attempts' not in backup;assert len(backup['writtenBackup']['runs'])==2 and len(backup['records'])==1;assert 'answer' not in backup['records'][0]['material'];page.get_by_role('button',name='設定を閉じる').click()
 # Verify raw IndexedDB payloads and durable outbox use the same canonical format.
 raw=page.evaluate('''async()=>{const name='hitomon:/:records-v2',db=await new Promise((ok,no)=>{const r=indexedDB.open(name);r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error);});try{const t=db.transaction(['attempts','outbox']),all=n=>new Promise(ok=>{const r=t.objectStore(n).getAll();r.onsuccess=()=>ok(r.result);});return {records:await all('attempts'),outbox:await all('outbox')};}finally{db.close();}}''');assert raw['records'] and all(r['data']['format']=='hitomon-learning-record' for r in raw['records']);assert all(r['payload']['format']=='hitomon-learning-record' for r in raw['outbox'])
 # PWA must retain new modules and the case/material/checkpoint when offline.
 page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener("controllerchange",ok,{once:true}));}');ctx.set_offline(True);page.reload();page.locator('.written-items').wait_for();assert cases(page)[-1]['progress']['status']=='completed';target(page,'objective');page.locator('.study-entrance[data-paper-mode=all]').click();page.locator('[data-action=submit]').wait_for();assert state(page)['currentId']==aid;ctx.set_offline(False)
 # Import a v2 file into a new device and restore B and A simultaneously.
 fresh=b.new_context(viewport={'width':390,'height':844});other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(URL);other.locator('.quick-start').wait_for();other.locator('#settings-button').click();open_data_management(other);other.locator('#import-state').set_input_files(str(path));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();other.get_by_role('button',name='設定を閉じる').click();assert len(state(other)['attempts'])==1 and len(cases(other))==2;target(other,'written');nav(other,'history');assert '自己評価' in other.locator('#main').inner_text();target(other,'objective');assert not other.locator('.written-answer').count()
 assert not errors,errors;b.close()
print('PASS A/B checkpoints and record separation / 320/390/1440/2560 / early completion excluded / 8 fields and self rating / unaided case / AI scope / canonical IndexedDB and outbox / v2 Export+Import / offline A+B')
print('Artifacts:',ARTIFACTS)
