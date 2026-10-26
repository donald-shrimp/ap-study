"""Exercise grouped checking through the real UI, storage, backup and offline resume."""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
from browser_storage import open_written_case,wait_for_async,open_data_management
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-case-batch-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
READ='''async()=>{const root=new URL('.',document.baseURI),{createLocalStore}=await import(new URL('src/storage/local.js',root)),s=createLocalStore({qualificationId:document.documentElement.dataset.qualification,rootPath:root.pathname});try{const identity=await s.identity(),{createWorkspaceStore}=await import(new URL('src/storage/workspace.js',root)),w=createWorkspaceStore({...identity,rootPath:root.pathname,namespaceName:'written',validate:()=>{}});try{return(await w.read()).map(r=>r.payload).sort((a,b)=>a.startedAt.localeCompare(b.startedAt)).at(-1);}finally{await w.close();}}finally{await s.close();}}'''
def run(pg):return pg.evaluate(READ)
def field(pg,key):return pg.locator(f'.written-field[data-written-key="{key}"]')
def choose(pg,item):
 pg.locator(f'.written-item-nav [data-action=written-item][data-id="{item["id"]}"]').click()
 pg.locator(f'.written-item-nav [data-id="{item["id"]}"][aria-current=step]').wait_for()
def enter(pg,item):
 for f in item['fields']:
  el=field(pg,item['id']+'--'+f['id'])
  if el.locator('[data-action=written-submit]').count()==0:continue
  if f['type']=='singleChoice':el.locator(f'input[value="{next(c["id"] for c in f["choices"] if c["label"]==f["referenceAnswers"][0])}"]').check()
  else:el.locator('textarea,input[type=text]').fill(f['referenceAnswers'][0])
def shot(pg,name):
 for width in [320,390,1440]:
  pg.set_viewport_size({'width':width,'height':1000});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  pg.locator('[data-action=written-check-item]').scroll_into_view_if_needed();pg.screenshot(path=str(ART/f'{name}-{width}.png'))
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':390,'height':1000});pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(BASE+'ap/?part=written&entry=home');pg.locator('.quick-start').wait_for();open_written_case(pg,'ap-r07h-pm8');expect(pg.locator('[data-action=written-check-item]')).to_be_disabled()
  original=run(pg);item=original['material']['items'][0];keys=[item['id']+'--'+f['id'] for f in item['fields']];assert len(keys)==3
  field(pg,keys[0]).locator('textarea').fill(item['fields'][0]['referenceAnswers'][0]);field(pg,keys[0]).locator('[data-action=written-submit]').click()
  field(pg,keys[1]).locator('textarea').fill('未知の表現');shot(pg,'ap-before');pg.locator('[data-action=written-check-item]').click();expect(pg.locator('.written-answer')).to_have_count(2)
  assert not field(pg,keys[0]).locator('.written-explanation').evaluate('e=>e.open');assert field(pg,keys[1]).locator('.written-explanation').evaluate('e=>e.open');assert field(pg,keys[2]).locator('textarea').is_editable()
  r=run(pg);assert len(r['responses'])==2 and keys[1] not in r['evaluations'];assert all(not v['answerViewedBefore'] for v in r['responses'].values());assert r['progress']['status']=='in_progress'
  # The workspace queues pending input before the batch operation, even offline.
  pg.evaluate('async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(ok=>navigator.serviceWorker.addEventListener("controllerchange",ok,{once:true}));}')
  ctx.set_offline(True);field(pg,keys[2]).locator('textarea').fill('後から考えた回答');pg.locator('[data-action=written-check-item]').click();expect(pg.locator('.written-answer')).to_have_count(3)
  saved=run(pg);assert saved['responses'][keys[2]]['answerViewedBefore'];assert len(saved['evaluations'])==1
  pg.reload();pg.locator('.written-layout').wait_for();assert field(pg,keys[2]).locator('textarea').input_value()=='後から考えた回答';assert pg.locator('.written-answer').count()==3;assert field(pg,keys[1]).locator('.written-explanation').evaluate('e=>e.open');ctx.set_offline(False)
  # The exported canonical record retains grouped answers and explicit self-rating gaps.
  open_data_management(pg)
  with pg.expect_download() as event:pg.locator('#export-state').click()
  backup=ART/'synthetic-backup.json';event.value.save_as(str(backup));data=json.loads(backup.read_text());restored=next(r for r in data['writtenBackup']['runs'] if r['id']==saved['id']);assert all(restored[k]==saved[k] for k in ['responses','evaluations','assistance','material']);pg.get_by_role('button',name='設定を閉じる').click()
  # Exam mode locks a group without leaking answers until the whole case is submitted.
  open_written_case(pg,'ap-r07h-pm8',mode='exam');exam=run(pg);enter(pg,exam['material']['items'][0]);expect(pg.locator('[data-action=written-check-item]')).to_have_text('まとめて回答する');pg.locator('[data-action=written-check-item]').click();expect(pg.locator('.written-field [data-action=written-submit]')).to_have_count(0);assert pg.locator('.written-answer,[data-action=written-answer]').count()==0;assert run(pg)['assistance']['viewedFields']==[]
  for item in exam['material']['items'][1:]:
   choose(pg,item);enter(pg,item)
   if len(item['fields'])>1:pg.locator('[data-action=written-check-item]').click()
   else:pg.locator('[data-action=written-submit]').click()
   expect(pg.locator('.written-field [data-action=written-submit]')).to_have_count(0)
   if item!=exam['material']['items'][-1]:assert pg.locator('.written-answer').count()==0
  choose(pg,exam['material']['items'][0]);pg.locator('[data-action=written-check-item]').click();expect(pg.locator('.written-answer')).to_have_count(3)
  # The same button checks FP's four-choice group and decimal fields.
  pg.goto(BASE+'fp2/?part=jafp-practical&entry=home');pg.locator('.quick-start').wait_for();open_written_case(pg,'fp2-202605-jafp-q01');r=run(pg);enter(pg,r['material']['items'][0]);shot(pg,'fp-before');pg.locator('[data-action=written-check-item]').click();expect(pg.locator('.written-answer')).to_have_count(4);assert run(pg)['progress']['status']=='completed';assert pg.locator('.written-explanation[open]').count()==0
  fp=json.loads((ROOT/'content/fp2/practical-cases.json').read_text());numeric=next(c for c in fp if any(len(i['fields'])>1 and any(f['type']=='numeric' for f in i['fields']) for i in c['items']));open_written_case(pg,numeric['id']);r=run(pg)
  for item in r['material']['items']:
   if len(r['material']['items'])>1:choose(pg,item)
   enter(pg,item)
   if len(item['fields'])>1:pg.locator('[data-action=written-check-item]').click()
   else:pg.locator('[data-action=written-submit]').click()
   expect(pg.locator('.written-field [data-action=written-submit]')).to_have_count(0)
  assert run(pg)['progress']['status']=='completed';assert all(e['outcome']=='correct' for e in run(pg)['evaluations'].values());assert not errors,errors;b.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps({'groupSubmitAndReveal':True,'emptyUnchanged':True,'selfExplanationsOpen':True,'automaticCorrectDetailsCollapsed':True,'assistanceOrdering':True,'examDisclosure':True,'fpChoiceAndNumeric':True,'offlineReload':True,'canonicalBackup':True,'widths':[320,390,1440],'pageErrors':errors},indent=2)+'\n')
print('PASS grouped checking / self explanations / empty fields / assistance / exam / FP choices and decimals / offline and backup');print('Artifacts:',ART)
