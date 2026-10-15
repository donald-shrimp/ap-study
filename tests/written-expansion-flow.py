"""All published written cases open with their complete items, images and durable records."""
import json,os,shutil,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from browser_storage import nav,open_data_management,wait_for_async
ROOT=Path(__file__).resolve().parents[1];BANK=json.loads((ROOT/'content/ap/written-cases.json').read_text());URL=os.getenv('AP_STUDY_URL','http://127.0.0.1:4173/ap/');ART=Path(tempfile.mkdtemp(prefix='hitomon-written-expansion-'));SCOPE=[c for c in BANK if c['id'].startswith(os.getenv('HITOMON_CASE_PREFIX',''))];COUNT=len(SCOPE);LIBRARY=44+22*len(json.loads((ROOT/'content/ap/written-drafts/2021-2023/progress.json').read_text())['integratedYears'])
READ='''async()=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),s=createLocalStore({qualificationId:'ap',rootPath:root.pathname});try{const i=await s.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),w=createWorkspaceStore({...i,rootPath:root.pathname,namespaceName:'written',validate:(k,p)=>p});try{return (await w.read()).map(r=>r.payload);}finally{await w.close();}}finally{await s.close();}}'''
with sync_playwright() as p:
 opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
 if URL.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
 b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();page.set_default_timeout(45000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.goto(URL+'?part=written');page.locator('.study-entry').wait_for()
 assert len(BANK)==LIBRARY and COUNT>0;assert page.locator('.written-case-option').count()==LIBRARY and page.locator('.study-entry .button.primary').count()==1
 for c in SCOPE:
  if not page.locator('.written-case-option').count():nav(page,'home')
  page.locator(f'.written-case-option [data-action=written-start][data-id="{c["id"]}"]:not([data-mode])').click();page.locator('.written-layout').wait_for();assert page.locator('.written-answer').count()==0
  for item in c['items']:
   page.locator(f'.written-item-nav [data-id="{item["id"]}"]').click();page.locator(f'.written-item-nav [data-id="{item["id"]}"][aria-current=step]').wait_for();assert page.locator('.written-field').count()==len(item['fields'])
   for f in item['fields']:
    key=item['id']+'--'+f['id'];field=page.locator(f'.written-field[data-written-key="{key}"]');assert f['label'] in field.locator('h3').inner_text()
    if f['type']=='singleChoice':assert field.locator('input[type=radio]').count()==len(f['choices'])
    else:assert field.locator('textarea').get_attribute('maxlength')==str(f['maxLength'])
  # Original diagrams/tables are loaded, and inline math/code never fall back to broken syntax.
  page.evaluate('''async()=>{const images=[...document.querySelectorAll('.written-body img')];for(const img of images)img.loading='eager';await Promise.all(images.map(img=>img.decode()));}''')
  assert page.locator('.written-body img').count()==len(c['bodyFigures']);assert page.locator('.math-error').count()==0,c['id']
  for width in [320,390,1440]:
   page.set_viewport_size({'width':width,'height':1000})
   if width<=1000:
    page.locator('[data-action=written-pane][data-pane=body]').click();page.locator('.written-body').wait_for(state='visible')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(c['id'],width,'body')
    page.locator('[data-action=written-pane][data-pane=questions]').click();page.locator('.written-items').wait_for(state='visible')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(c['id'],width,'questions')
  first=c['items'][0];f=first['fields'][0];key=first['id']+'--'+f['id'];page.locator(f'.written-item-nav [data-id="{first["id"]}"]').click();page.locator(f'.written-item-nav [data-id="{first["id"]}"][aria-current=step]').wait_for();field=page.locator(f'.written-field[data-written-key="{key}"]')
  if f['type']=='singleChoice':field.locator('input[type=radio]').first.check()
  else:field.locator('textarea').fill(f['referenceAnswers'][0])
  field.locator('[data-action=written-submit]').click();field.locator('[data-action=written-answer]').click();field.locator('.written-answer').wait_for();assert f['referenceAnswers'][0] in field.locator('.written-answer').inner_text()
  if field.locator('[data-action=written-rate]').count():field.locator('[data-action=written-rate][data-outcome=meets]').click()
  field.locator('[data-action=written-ai]').click();page.locator('#ai-handoff-dialog').wait_for(state='visible');prompt=page.locator('#ai-handoff-preview').input_value();assert c['body'] in prompt and first['prompt'] in prompt;page.locator('#ai-handoff-close').click()
  if c['id'] in [f'ap-r0{y}{s}-pm{n}' for y in [3,4,5] for s,n in [('a',3),('a',6),('h',7)]]:
   page.screenshot(path=str(ART/(c['id']+'-1440.png')))
  page.reload();page.locator('.written-items').wait_for();assert page.locator(f'.written-field[data-written-key="{key}"] .written-answer').count()==1
 assert len(page.evaluate(READ))==COUNT
 open_data_management(page)
 with page.expect_download() as event:page.locator('#export-state').click()
 backup=ART/'all-written-records.json';event.value.save_as(backup);data=json.loads(backup.read_text());assert len(data['writtenBackup']['runs'])==COUNT and data['records']==[];page.get_by_role('button',name='設定を閉じる',exact=True).click()
 fresh=b.new_context(viewport={'width':390,'height':844});other=fresh.new_page();other.on('dialog',lambda d:d.accept());other.goto(URL+'?part=written');other.locator('.study-entry').wait_for();open_data_management(other);other.locator('#import-state').set_input_files(str(backup));other.get_by_text('学習記録を読み込みました。',exact=False).wait_for();other.get_by_role('button',name='設定を閉じる',exact=True).click();restored=other.evaluate(READ);assert {r['caseId'] for r in restored}=={c['id'] for c in SCOPE};assert all(r['responses'] and r['evaluations'] for r in restored);fresh.close()
 page.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener("controllerchange",ok,{once:true}));}');ctx.set_offline(True);page.reload();page.locator('.written-items').wait_for();assert page.locator('.written-answer').count()==1;assert not errors,errors;b.close()
print(f'PASS {COUNT} case routes in library{LIBRARY} / every item+field / original diagrams / no math errors / 320+390+1440 / answer+AI+reload / backup import to fresh device / offline; artifacts:',ART)
